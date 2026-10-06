"""Knowledge Engine: the artifact Slice actually keeps.

Images are disposable; Knowledge JSON is the durable product.
Schema `slice.knowledge/v1` records the skeleton (with per-joint
confidence and observed/predicted state), body ratios, the selected
statistical body model, and an OpenPose-style x,y,c keypoint array for
interoperability.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Optional

from .landmarks import BONES, JOINTS
from .skeleton import OBSERVED, PREDICTED, Skeleton

SCHEMA = "slice.knowledge/v1"


def build(skel: Skeleton, ratios: dict, pose: Optional[dict] = None,
          *, image_sha256: str = "", source_name: str = "",
          engine: dict) -> dict:
    joints = skel.joints
    flat = []
    for name in JOINTS:
        j = joints.get(name)
        flat += [j.x, j.y, j.confidence] if j else [0.0, 0.0, 0.0]
    return {
        "schema": SCHEMA,
        "id": "k_" + secrets.token_hex(6),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": engine,
        "source": {
            "name": source_name,
            "sha256": image_sha256,
            "image_retained": False,
        },
        "skeleton": skel.to_dict(),
        "pose": pose or {},
        "ratio": ratios,
        "prediction": {
            "observed": [n for n, j in joints.items() if j.state == OBSERVED],
            "predicted": [n for n, j in joints.items()
                          if j.state == PREDICTED],
        },
        # how much of the document rests on image evidence — the
        # honesty contract as numbers, not just colors
        "coverage": {
            "joints_total": len(JOINTS),
            "observed": sum(1 for j in joints.values()
                            if j.state == OBSERVED),
            "predicted": sum(1 for j in joints.values()
                             if j.state == PREDICTED),
            "unfilled": len(JOINTS) - len(joints),
            "observed_ratio": round(
                sum(1 for j in joints.values() if j.state == OBSERVED)
                / len(JOINTS), 3),
            "mean_observed_confidence": round(
                sum(j.confidence for j in joints.values()
                    if j.state == OBSERVED)
                / max(1, sum(1 for j in joints.values()
                             if j.state == OBSERVED)), 3),
        },
        "export": {
            "keypoints_2d": flat,
            "keypoint_order": JOINTS,
            "bones": [list(b) for b in BONES],
        },
    }


def validate(doc: dict) -> list:
    """Return a list of schema problems; empty means valid."""
    errors = []
    if doc.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    for key in ("id", "created_at", "engine", "skeleton", "export"):
        if key not in doc:
            errors.append(f"missing {key}")
    joints = (doc.get("skeleton") or {}).get("joints") or {}
    for name, j in joints.items():
        for f in ("x", "y", "confidence", "state"):
            if f not in j:
                errors.append(f"joint {name} missing {f}")
        if j.get("state") not in (OBSERVED, PREDICTED):
            errors.append(f"joint {name} bad state {j.get('state')}")
        c = j.get("confidence")
        if not isinstance(c, (int, float)) or not 0 <= c <= 1:
            errors.append(f"joint {name} bad confidence {c}")
    return errors


INDEX_NAME = "_index.json"


def _list_entry(doc: dict) -> dict:
    return {"id": doc.get("id"),
            "created_at": doc.get("created_at"),
            "body_model": (doc.get("skeleton") or {})
            .get("body_model", {}).get("name")}


class KnowledgeStore:
    """File-backed store: one <id>.json per analysis, with a cached
    listing manifest so `list()` does not have to open every document."""

    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def save(self, doc: dict) -> str:
        errors = validate(doc)
        if errors:
            raise ValueError("invalid knowledge: " + "; ".join(errors))
        path = os.path.join(self.root, doc["id"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        self._index_add(doc)
        return doc["id"]

    def get(self, kid: str) -> dict:
        if not re.fullmatch(r"k_[0-9a-f]{12}", kid):
            raise KeyError(kid)
        path = os.path.join(self.root, kid + ".json")
        if not os.path.isfile(path):
            raise KeyError(kid)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _index_path(self) -> str:
        return os.path.join(self.root, INDEX_NAME)

    def _index_load(self) -> Optional[dict]:
        """Load the cached index -> {kid: entry}, or None if unusable."""
        try:
            with open(self._index_path(), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(d, dict) or not isinstance(d.get("entries"), dict):
            return None
        return d["entries"]

    def _index_add(self, doc: dict) -> None:
        """Best-effort index update; a broken index self-heals in list()."""
        entries = self._index_load()
        if entries is None:
            entries = {}
        entries[doc["id"]] = _list_entry(doc)
        try:
            with open(self._index_path(), "w", encoding="utf-8") as f:
                json.dump({"schema": "slice.index/v1", "entries": entries},
                          f, ensure_ascii=False)
        except OSError:
            pass

    def list(self) -> list:
        files = [fn for fn in sorted(os.listdir(self.root))
                 if fn.endswith(".json") and fn != INDEX_NAME]
        indexed = self._index_load()
        out, healed = [], indexed is None
        entries = dict(indexed) if indexed else {}
        for fn in files:
            kid = fn[:-5]
            ent = entries.pop(kid, None)
            if ent is None:
                healed = True
                try:
                    with open(os.path.join(self.root, fn),
                              encoding="utf-8") as f:
                        d = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(d, dict):
                    continue
                ent = _list_entry(d)
            out.append(ent)
        if healed or entries:  # index was missing/stale -> rewrite it
            known = {e.get("id"): e for e in out if e.get("id")}
            try:
                with open(self._index_path(), "w", encoding="utf-8") as f:
                    json.dump({"schema": "slice.index/v1",
                               "entries": known}, f, ensure_ascii=False)
            except OSError:
                pass
        return out


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
