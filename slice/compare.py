"""Pose similarity between two Knowledge documents.

Comparison happens in normalized space — pelvis at the origin, one unit
= neck–pelvis length — so framing and resolution cannot dominate the
distance. Only joints observed (and confident enough) in both documents
contribute — a predicted joint is a prior fill, and counting it would
measure the prior, not the poses; the result reports which joints were
compared so a small overlap cannot masquerade as a close match.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple


def _norm_joints(doc: dict) -> Optional[Tuple[Dict, Dict]]:
    sk = doc.get("skeleton") if isinstance(doc, dict) else None
    raw = sk.get("joints") if isinstance(sk, dict) else None
    joints = {n: j for n, j in (raw or {}).items()
              if isinstance(j, dict)
              and isinstance(j.get("x"), (int, float))
              and isinstance(j.get("y"), (int, float))} \
        if isinstance(raw, dict) else {}
    pelvis, neck = joints.get("pelvis"), joints.get("neck")
    if not pelvis or not neck:
        return None
    unit = math.hypot(pelvis["x"] - neck["x"], pelvis["y"] - neck["y"])
    if unit < 1e-6:
        return None
    return ({n: ((j["x"] - pelvis["x"]) / unit,
                 (j["y"] - pelvis["y"]) / unit)
             for n, j in joints.items()}, joints)


def pose_distance(doc_a: dict, doc_b: dict,
                  *, min_confidence: float = 0.0) -> Optional[dict]:
    """Mean per-joint distance in torso units, or None when either
    document lacks a normalizable skeleton."""
    na, nb = _norm_joints(doc_a), _norm_joints(doc_b)
    if na is None or nb is None:
        return None
    (a, ja), (b, jb) = na, nb
    ja = (doc_a["skeleton"]["joints"])
    jb = doc_b["skeleton"]["joints"]
    common = [n for n in a if n in b
              and isinstance(ja[n].get("confidence", 1.0),
                             (int, float))
              and ja[n].get("state") != "predicted"
              and jb[n].get("state") != "predicted"
              and ja[n].get("confidence", 1.0) >= min_confidence
              and isinstance(jb[n].get("confidence", 1.0),
                             (int, float))
              and jb[n].get("confidence", 1.0) >= min_confidence]
              and jb[n].get("confidence", 1.0)
              >= min_confidence]
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
