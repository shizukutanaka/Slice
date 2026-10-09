"""Pose distance between two Knowledge documents, in torso units."""
from __future__ import annotations

import math
from typing import Dict, Optional, Tuple


def _valid_joints(doc: dict) -> Dict:
    sk = doc.get("skeleton") if isinstance(doc, dict) else None
    raw = sk.get("joints") if isinstance(sk, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {n: j for n, j in raw.items()
            if isinstance(j, dict)
            and isinstance(j.get("x"), (int, float))
            and isinstance(j.get("y"), (int, float))}


def _norm_joints(joints: Dict) -> Optional[Dict[str, Tuple[float, float]]]:
    pelvis, neck = joints.get("pelvis"), joints.get("neck")
    if not pelvis or not neck:
        return None
    unit = math.hypot(pelvis["x"] - neck["x"], pelvis["y"] - neck["y"])
    if unit < 1e-6:
        return None
    return {n: ((j["x"] - pelvis["x"]) / unit,
                (j["y"] - pelvis["y"]) / unit)
            for n, j in joints.items()}


def pose_distance(doc_a: dict, doc_b: dict,
                  *, min_confidence: float = 0.0) -> Optional[dict]:
    """Mean per-joint distance in torso units, or None when either
    document lacks a normalizable skeleton."""
    ja, jb = _valid_joints(doc_a), _valid_joints(doc_b)
    a, b = _norm_joints(ja), _norm_joints(jb)
    if a is None or b is None:
        return None
    common = [n for n in a if n in b
              and ja[n].get("state") != "predicted"
              and jb[n].get("state") != "predicted"
              and isinstance(ja[n].get("confidence", 1.0), (int, float))
              and isinstance(jb[n].get("confidence", 1.0), (int, float))
              and ja[n].get("confidence", 1.0) >= min_confidence
              and jb[n].get("confidence", 1.0) >= min_confidence]
    if not common:
        return None
    per_joint = {n: round(math.hypot(a[n][0] - b[n][0],
                                     a[n][1] - b[n][1]), 4)
                 for n in common}
    return {
        "distance": round(sum(per_joint.values()) / len(per_joint), 4),
        "joints_compared": len(common),
        "per_joint": per_joint,
    }
