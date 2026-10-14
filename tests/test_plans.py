"""Tests for API-key plans and monthly usage metering."""

import calendar
import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer

from slice import bitmap, knowledge, plans, rest
from tests import synthetic_person


def _write_keys(path, *, quota=2, plan="pro", owner="acme"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "plans": {plan: quota},
            "keys": {"test-key": {"plan": plan, "owner": owner}},
        }, f)


def _utc(month):
    return calendar.timegm(time.strptime(month, "%Y-%m"))


class TestMetering(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.keys_path = os.path.join(self.tmp.name, "keys.json")
        _write_keys(self.keys_path)
        self.meter = plans.Metering(self.keys_path)

    def test_quota_enforced_at_limit(self):
        self.assertTrue(self.meter.allowed("test-key", now=_utc("2025-01")))
        self.meter.record("test-key", now=_utc("2025-01"))
        self.meter.record("test-key", now=_utc("2025-01"))
        self.assertFalse(self.meter.allowed(
            "test-key", now=_utc("2025-01")))
        self.assertEqual(self.meter.usage(
            "test-key", now=_utc("2025-01"))["remaining"], 0)

    def test_unlimited_enterprise(self):
        path = os.path.join(self.tmp.name, "enterprise.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"keys": {
                "enterprise-key": {"plan": "enterprise"},
            }}, f)
        meter = plans.Metering(path)
        for _ in range(5):
            meter.record("enterprise-key", now=_utc("2025-01"))
        usage = meter.usage("enterprise-key", now=_utc("2025-01"))
        self.assertIsNone(usage["quota"])
        self.assertIsNone(usage["remaining"])
        self.assertTrue(meter.allowed("enterprise-key", now=_utc("2025-01")))

    def test_unknown_key_and_plan_are_unrecognized(self):
        self.assertIsNone(self.meter.plan_for("not-issued"))
        before = os.stat(self.keys_path)
        with open(self.keys_path, "w", encoding="utf-8") as f:
            json.dump({"keys": {
                "bad-plan": {"plan": "not-a-plan"},
            }}, f)
        os.utime(self.keys_path, ns=(
            before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        self.assertIsNone(self.meter.plan_for("bad-plan"))

    def test_month_rollover_retains_old_month(self):
        self.meter.record("test-key", units=3, now=_utc("2025-01"))
        january = self.meter.usage("test-key", now=_utc("2025-01"))
        february = self.meter.usage("test-key", now=_utc("2025-02"))
        self.assertEqual(january["used"], 3)
        self.assertEqual(february["used"], 0)
        self.assertEqual(self.meter._ledger["test-key"]["2025-01"], 3)

    def test_usage_persists_across_instances(self):
        self.meter.record("test-key", units=2, now=_utc("2025-01"))
        next_meter = plans.Metering(self.keys_path)
        self.assertEqual(next_meter.usage(
            "test-key", now=_utc("2025-01"))["used"], 2)

    def test_corrupt_ledger_raises_value_error(self):
        with open(self.meter.ledger_path, "w", encoding="utf-8") as f:
            f.write("{")
        with self.assertRaisesRegex(ValueError, "usage ledger"):
            plans.Metering(self.keys_path)

    def test_issue_key_creates_file_and_rejects_unknown_plan(self):
        path = os.path.join(self.tmp.name, "new-keys.json")
        key = plans.issue_key(path, "pro", owner="acme")
        meter = plans.Metering(path)
        self.assertEqual(meter.plan_for(key), {
            "plan": "pro", "owner": "acme", "quota": 10000,
        })
        with self.assertRaisesRegex(ValueError, "unknown plan"):
            plans.issue_key(path, "does-not-exist")

    def test_existing_metering_reloads_issued_keys(self):
        meter = plans.Metering(self.keys_path)
        self.assertIsNone(meter.plan_for("new-key"))
        before = os.stat(self.keys_path)
        key = plans.issue_key(self.keys_path, "pro", owner="new")
        os.utime(self.keys_path, ns=(
            before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        self.assertEqual(meter.plan_for(key)["owner"], "new")


class TestMeteredRest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        keys_path = os.path.join(self.tmp.name, "keys.json")
        _write_keys(keys_path, quota=1)
        rest.Handler.store = knowledge.KnowledgeStore(self.tmp.name)
        rest.Handler.token = None
        rest.Handler.metering = plans.Metering(keys_path)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), rest.Handler)
        self.srv = srv
        self.port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(setattr, rest.Handler, "metering", None)
        self.addCleanup(srv.shutdown)

    def _request(self, method, path, *, key=None, body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        headers = {}
        if key is not None:
            headers["Authorization"] = "Bearer " + key
        if body is not None:
            headers["Content-Type"] = "application/octet-stream"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        result = (response.status, response.getheader("X-Quota-Remaining"),
                  raw)
        conn.close()
        return result

    def test_auth_health_and_usage_endpoint(self):
        self.assertEqual(self._request("GET", "/knowledge")[0], 401)
        self.assertEqual(self._request(
            "GET", "/knowledge", key="unknown")[0], 401)
        self.assertEqual(self._request("GET", "/health")[0], 200)
        status, _, raw = self._request("GET", "/usage", key="test-key")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["used"], 0)

    def test_only_successful_analyze_is_charged_until_quota(self):
        status, _, _ = self._request(
            "POST", "/analyze", key="test-key", body=b"not an image")
        self.assertEqual(status, 415)
        self.assertEqual(rest.Handler.metering.usage("test-key")["used"], 0)

        raw_png = bitmap.encode_png(synthetic_person())
        status, remaining, _ = self._request(
            "POST", "/analyze", key="test-key", body=raw_png)
        self.assertEqual(status, 200)
        self.assertEqual(remaining, "0")
        self.assertEqual(rest.Handler.metering.usage("test-key")["used"], 1)

        status, _, raw = self._request(
            "POST", "/analyze", key="test-key", body=raw_png)
        self.assertEqual(status, 429)
        self.assertEqual(json.loads(raw)["error"], "quota exceeded")


if __name__ == "__main__":
    unittest.main()
