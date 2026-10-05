"""Ratio Engine: anatomical proportions and balance from a skeleton."""

from __future__ import annotations

import math
from typing import Optional, Tuple

from .skeleton import Skeleton


def _dist(a: Optional[Tuple[float, float]],
          b: Optional[Tuple[float, float]]) -> Optional[float]:
    if a is None or b is None:
        return None
    return math.hypot(a[0] - b[0], a[1] - b[1])


def analyze(skel: Skeleton, *, centroid: Optional[Tuple[float, float]] = None
            ) -> dict:
    """Return normalized body ratios (all /body height) plus balance."""
    top = skel.point("head")
    feet = [p for p in (skel.point("foot_l"), skel.point("foot_r")) if p]
    if not top or not feet:
        return {"error": "insufficient joints"}
    bottom_y = max(p[1] for p in feet)
    body_h = bottom_y - _top_y(skel)
    if body_h <= 0:
        return {"error": "degenerate skeleton"}

    def norm(d):
        return round(d / body_h, 4) if d is not None else None

    head_px = _head_height(skel)
    ratios = {
        "body_height_px": round(body_h, 2),
        "head_to_body": round(body_h / head_px, 2) if head_px else None,
        "shoulder_width": norm(_dist(skel.point("shoulder_l"),
                                     skel.point("shoulder_r"))),
        "hip_width": norm(_dist(skel.point("hip_l"), skel.point("hip_r"))),
        "torso_length": norm(abs((skel.point("pelvis") or (0, 0))[1]
                                 - (skel.point("neck") or (0, 0))[1])
                             if skel.point("pelvis") and skel.point("neck")
                             else None),
        "arm_l": norm(_dist(skel.point("shoulder_l"), skel.point("wrist_l"))),
        "arm_r": norm(_dist(skel.point("shoulder_r"), skel.point("wrist_r"))),
        "leg_l": norm(_dist(skel.point("hip_l"), skel.point("ankle_l"))),
        "leg_r": norm(_dist(skel.point("hip_r"), skel.point("ankle_r"))),
    }
    sym = _symmetry(skel)
    ratios["limb_symmetry"] = round(sym, 3) if sym is not None else None
    if centroid:
        ratios["center_of_mass"] = {
            "x": round(centroid[0], 2), "y": round(centroid[1], 2),
            "y_ratio": round((centroid[1] - _top_y(skel)) / body_h, 3),
        }
    return ratios


def _top_y(skel: Skeleton) -> float:
    ys = [j.y for j in skel.joints.values()]
    return min(ys) if ys else 0.0


def _head_height(skel: Skeleton) -> Optional[float]:
    head = skel.get("head")
    neck = skel.get("neck")
    if not head:
        return None
    if neck and neck.y > head.y:
        return (neck.y - head.y) * 2
    return head.y - _top_y(skel) + (head.y - _top_y(skel))


def _symmetry(skel: Skeleton) -> Optional[float]:
    pairs = [("arm_l", "arm_r"), ("leg_l", "leg_r")]
    vals = []
    for a, b in pairs:
        la = _limb_len(skel, a)
        lb = _limb_len(skel, b)
        if la and lb and max(la, lb) > 0:
            vals.append(1 - abs(la - lb) / max(la, lb))
    return sum(vals) / len(vals) if vals else None


def _limb_len(skel: Skeleton, name: str) -> Optional[float]:
    if name.startswith("arm"):
        s = "shoulder_" + name[-1]
        return _dist(skel.point(s), skel.point("wrist_" + name[-1]))
    s = "hip_" + name[-1]
    return _dist(skel.point(s), skel.point("ankle_" + name[-1]))
