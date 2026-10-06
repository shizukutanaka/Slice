"""Skeleton plausibility audit — catch geometrically impossible output.

The estimator can emit joints that individually look reasonable but
together violate anatomy (a thigh twice the prior length, a joint
outside the image, grossly asymmetric limbs). `audit` reports such
violations as named issues so callers can flag or filter the doc —
the mechanical counterpart of "this skeleton cannot be right".
"""

from __future__ import annotations

import math
from typing import List, Optional

from .anatomy import BODY_MODELS, DEFAULT_MODEL
from .skeleton import Skeleton

# (joint_a, joint_b, prior field, lo, hi) — segment must stay within
# [lo, hi] × prior × body height.
_SEGMENTS = [
    ("shoulder_l", "elbow_l", "upper_arm_ratio", 0.4, 2.5),
    ("elbow_l", "wrist_l", "forearm_ratio", 0.4, 2.5),
    ("shoulder_r", "elbow_r", "upper_arm_ratio", 0.4, 2.5),
    ("elbow_r", "wrist_r", "forearm_ratio", 0.4, 2.5),
    ("hip_l", "knee_l", "thigh_ratio", 0.4, 2.5),
    ("knee_l", "ankle_l", "shin_ratio", 0.4, 2.5),
    ("hip_r", "knee_r", "thigh_ratio", 0.4, 2.5),
    ("knee_r", "ankle_r", "shin_ratio", 0.4, 2.5),
]

# Bilateral pairs whose lengths should be roughly symmetric.
_PAIRS = [
    (("shoulder_l", "elbow_l"), ("shoulder_r", "elbow_r")),
    (("elbow_l", "wrist_l"), ("elbow_r", "wrist_r")),
    (("hip_l", "knee_l"), ("hip_r", "knee_r")),
    (("knee_l", "ankle_l"), ("knee_r", "ankle_r")),
]


def _d(skel: Skeleton, a: str, b: str) -> Optional[float]:
    pa, pb = skel.point(a), skel.point(b)
    if not pa or not pb:
        return None
    return math.hypot(pa[0] - pb[0], pa[1] - pb[1])


def audit(skel: Skeleton, model: Optional[str] = None) -> List[str]:
    """Return named plausibility issues; empty list = no violation."""
    prior = BODY_MODELS.get(
        model or (skel.body_model or {}).get("name") or DEFAULT_MODEL,
        BODY_MODELS[DEFAULT_MODEL])
    head = skel.point("head")
    feet = [p for p in (skel.point("foot_l"), skel.point("foot_r")) if p]
    issues: List[str] = []
    if not head or not feet:
        return ["no_body_extent"]
    body_h = max(f[1] for f in feet) - head[1]
    if body_h <= 0:
        return ["inverted_or_flat_body"]

    for name, j in skel.joints.items():
        if not (0 <= j.x <= skel.image_width
                and 0 <= j.y <= skel.image_height):
            issues.append(f"{name}_out_of_frame")

    for a, b, field, lo, hi in _SEGMENTS:
        d = _d(skel, a, b)
        if d is None:
            continue
        expected = prior[field] * body_h
        if d < expected * lo:
            issues.append(f"{a}_{b}_too_short")
        elif d > expected * hi:
            issues.append(f"{a}_{b}_too_long")

    for (a1, b1), (a2, b2) in _PAIRS:
        d1, d2 = _d(skel, a1, b1), _d(skel, a2, b2)
        if d1 and d2 and max(d1, d2) > max(1e-6, min(d1, d2)) * 2.5:
            issues.append(f"{a1}_asymmetric")

    return sorted(set(issues))
