"""Dataset export: Knowledge Store -> flat JSONL for training/analysis.

Each line is one self-contained sample (id, labels, ratios, keypoints).
The store stays the source of truth; export is a lossless-enough view —
fields that don't exist yet in a document are simply omitted.
"""

from __future__ import annotations

import json
from typing import Iterator, Optional

from .knowledge import KnowledgeStore


def flatten(doc: dict) -> dict:
    """One knowledge document -> one dataset row."""
    joints = doc["skeleton"]["joints"]
    obs_confs = [j["confidence"] for j in joints.values()
                 if j["state"] == "observed"]
    rec = {
        "id": doc["id"],
        "created_at": doc["created_at"],
        "source": doc.get("source"),
        "labels": {
            "pose": (doc.get("pose") or {}).get("pose"),
            "style": (doc.get("style") or {}).get("style"),
            "body_model": doc["skeleton"]["body_model"].get("name"),
            "facing": doc["skeleton"]["orientation"].get("facing"),
        },
        "counts": {
            "observed": len(obs_confs),
            "predicted": sum(1 for j in joints.values()
                             if j["state"] == "predicted"),
        },
        "mean_observed_confidence": (
            round(sum(obs_confs) / len(obs_confs), 3) if obs_confs else 0),
        "ratios": doc.get("ratio") or {},
        "keypoint_order": doc["export"]["keypoint_order"],
        "keypoints_2d": doc["export"]["keypoints_2d"],
    }
    return rec


def iter_dataset(store: KnowledgeStore) -> Iterator[dict]:
    for item in store.list():
        yield flatten(store.get(item["id"]))


def dump_jsonl(store: KnowledgeStore, out: Optional[str] = None):
    """Write JSONL to `out` (or return the string when out is None)."""
    lines = [json.dumps(r, ensure_ascii=False)
             for r in iter_dataset(store)]
    text = "\n".join(lines) + ("\n" if lines else "")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        return None
    return text
