"""API-key plans and monthly request metering."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
import threading
import time
from typing import Optional


DEFAULT_PLANS = {
    "free": 100,
    "pro": 10000,
    "enterprise": None,
}


def _read_keys(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"plans": {}, "keys": {}}
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"cannot read API keys file {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"invalid API keys file {path}: expected an object")
    plans = data.get("plans", {})
    keys = data.get("keys", {})
    if not isinstance(plans, dict) or not isinstance(keys, dict):
        raise ValueError(
            f"invalid API keys file {path}: 'plans' and 'keys' "
            "must be objects")
    if any(not isinstance(name, str)
           or (quota is not None
               and (not isinstance(quota, int) or isinstance(quota, bool)
                    or quota < 0))
           for name, quota in plans.items()):
        raise ValueError(
            f"invalid API keys file {path}: plan quotas must be "
            "non-negative integers or null")
    return {"plans": plans, "keys": keys}


def _atomic_json(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".slice-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _month(now=None):
    return time.strftime("%Y-%m", time.gmtime(
        time.time() if now is None else now))


class Metering:
    def __init__(self, keys_path, ledger_path=None):
        self.keys_path = os.fspath(keys_path)
        self.ledger_path = (os.fspath(ledger_path) if ledger_path is not None
                            else self.keys_path + ".usage.json")
        self._lock = threading.RLock()
        self._keys_mtime = object()
        self._plans = dict(DEFAULT_PLANS)
        self._keys = {}
        self._reload_keys()
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                self._ledger = json.load(f)
        except FileNotFoundError:
            self._ledger = {}
        except (OSError, json.JSONDecodeError) as e:
            raise ValueError(
                f"cannot read usage ledger {self.ledger_path}: {e}") from e
        if not isinstance(self._ledger, dict) or any(
                not isinstance(key, str)
                or not isinstance(months, dict)
                or any(not isinstance(month, str)
                       or not isinstance(count, int)
                       or isinstance(count, bool)
                       or count < 0
                       for month, count in months.items())
                for key, months in self._ledger.items()):
            raise ValueError(
                f"invalid usage ledger {self.ledger_path}: expected "
                "an object of API keys and monthly counts")

    def _reload_keys(self):
        try:
            mtime = os.stat(self.keys_path).st_mtime_ns
        except FileNotFoundError:
            mtime = None
        if mtime == self._keys_mtime:
            return
        data = _read_keys(self.keys_path)
        self._plans = dict(DEFAULT_PLANS)
        self._plans.update(data["plans"])
        self._keys = data["keys"]
        self._keys_mtime = mtime

    def plan_for(self, key) -> Optional[dict]:
        with self._lock:
            self._reload_keys()
            entry = self._keys.get(key)
            if not isinstance(entry, dict):
                return None
            name = entry.get("plan")
            if not isinstance(name, str) or name not in self._plans:
                return None
            return {
                "plan": name,
                "owner": entry.get("owner", ""),
                "quota": self._plans[name],
            }

    def usage(self, key, now=None) -> dict:
        with self._lock:
            plan = self.plan_for(key)
            if plan is None:
                raise ValueError("unknown API key or plan")
            month = _month(now)
            used = self._ledger.get(key, {}).get(month, 0)
            quota = plan["quota"]
            return {
                "plan": plan["plan"],
                "owner": plan["owner"],
                "month": month,
                "used": used,
                "quota": quota,
                "remaining": None if quota is None else max(0, quota - used),
            }

    def allowed(self, key, now=None) -> bool:
        usage = self.usage(key, now=now)
        return usage["quota"] is None or usage["used"] < usage["quota"]

    def record(self, key, units=1, now=None) -> dict:
        if (not isinstance(units, int) or isinstance(units, bool)
                or units < 0):
            raise ValueError("units must be a non-negative integer")
        with self._lock:
            if self.plan_for(key) is None:
                raise ValueError("unknown API key or plan")
            month = _month(now)
            ledger = dict(self._ledger)
            months = dict(ledger.get(key, {}))
            months[month] = months.get(month, 0) + units
            ledger[key] = months
            _atomic_json(self.ledger_path, ledger)
            self._ledger = ledger
            return self.usage(key, now=now)


def issue_key(keys_path, plan, owner="") -> str:
    path = os.fspath(keys_path)
    data = _read_keys(path)
    available = dict(DEFAULT_PLANS)
    available.update(data["plans"])
    if plan not in available:
        raise ValueError(f"unknown plan: {plan}")
    key = secrets.token_urlsafe(24)
    data["keys"][key] = {"plan": plan, "owner": owner}
    _atomic_json(path, data)
    return key
