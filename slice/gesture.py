"""Gesture recognition — rule-based detection on observed joints.

A pose answers "where is the body"; a gesture answers "what is it
doing". Each rule only fires on observed joints — a wave can only
be claimed when the raised wrist is actually seen, never inferred
from a predicted limb. Returns every matching gesture with its
evidence so a consumer can audit the call.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from .skeleton import Skeleton

Point = Tuple[float, float]


def _d(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _evidence(skel: Skeleton, names: List[str]) -> Optional[Dict[str, Point]]:
    out = {}
    for n in names:
        j = skel.joints.get(n)
        if not j or j.state != "observed":
            return None
        out[n] = (j.x, j.y)
    return out


def detect(skel: Skeleton) -> List[dict]:
    """[{gesture, side, evidence}] — observed-joint evidence only."""
    found = []
    head = skel.point("head")
    hip_l = skel.point("hip_l")
    hip_r = skel.point("hip_r")
    shoulder_l = skel.point("shoulder_l")
    shoulder_r = skel.point("shoulder_r")
    for side, shoulder in (("l", shoulder_l), ("r", shoulder_r)):
        wrist_n, elbow_n = f"wrist_{side}", f"elbow_{side}"
        sh_n = f"shoulder_{side}"
        ev = _evidence(skel, [wrist_n, elbow_n, sh_n])
        if ev is None or shoulder is None:
            continue
        w, e, s = ev[wrist_n], ev[elbow_n], ev[sh_n]
        arm_len = _d(s, e) + _d(e, w) or 1.0

        # wave: wrist clearly above the head line
        if head and w[1] < head[1] - 0.3 * arm_len:
            found.append({"gesture": "wave", "side": side,
                          "evidence": sorted(ev)})
            continue

        # hands on hips: wrist near same-side hip, elbow pushed wide
        hip = hip_l if side == "l" else hip_r
        if (hip and _d(w, hip) < 0.9 * arm_len
                and abs(e[0] - s[0]) > 0.5 * arm_len):
            found.append({"gesture": "hands_on_hips", "side": side,
                          "evidence": sorted(ev)})
            continue

        # point: arm roughly horizontal, extended near full length
        if (abs(w[1] - s[1]) < 0.4 * arm_len
                and _d(s, w) > 0.85 * arm_len):
            found.append({"gesture": "point", "side": side,
                          "evidence": sorted(ev)})
    return found


def summarize(skel: Skeleton) -> dict:
    """{gestures, count, bilateral} for knowledge output."""
    g = detect(skel)
    names = [x["gesture"] for x in g]
    bilateral = len(names) != len(set(names))
    return {"gestures": names, "count": len(g),
            "bilateral": bilateral}
