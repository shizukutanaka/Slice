"""Hand position semantics — where each hand sits on the body map.

Above the head, at the face, by the chest, at the waist, near the
knee, hanging below, or hidden behind the body — a hand's zone
says more about intent than its raw coordinates. Zones are defined
relative to observed landmarks (head top, chest, pelvis, knee) so
they scale with the body, and predicted wrists are never zoned.
"""

from __future__ import annotations

from typing import Dict, Optional

from .skeleton import Skeleton


def _zone(skel: Skeleton, side: str) -> Optional[str]:
    j = skel.joints.get(f"wrist_{side}")
    if not j or j.state != "observed":
        return None
    w = (j.x, j.y)
    head = skel.point("head")
    chest = skel.point("chest")
    pelvis = skel.point("pelvis")
    knee = skel.point(f"knee_{side}")
    hip = skel.point(f"hip_{side}")

    def near(p, frac_of: float, ref: float) -> bool:
        return abs(w[1] - p[1]) < frac_of * ref

    span = 0.0
    if head and pelvis:
        span = abs(pelvis[1] - head[1])
    if head and w[1] < head[1] - 0.15 * max(span, 1.0):
        return "above_head"
    if head and near(head, 0.30, max(span, 1.0)):
        return "at_head"
    if chest and near(chest, 0.35, max(span, 1.0)):
        return "at_chest"
    if pelvis and near(pelvis, 0.30, max(span, 1.0)):
        return "at_waist"
    if hip and near(hip, 0.25, max(span, 1.0)):
        return "at_hip"
    if knee and abs(w[1] - knee[1]) < 0.2 * max(span, 1.0):
        return "at_knee"
    return "hanging"


def positions(skel: Skeleton) -> Dict[str, Optional[str]]:
    """{l: zone|None, r: zone|None} — None = not observed."""
    return {side: _zone(skel, side) for side in ("l", "r")}


def summary(skel: Skeleton) -> dict:
    """{zones, symmetric, observed_hands} for knowledge output."""
    p = positions(skel)
    zones = {s: z for s, z in p.items() if z}
    obs = len(zones)
    sym = obs == 2 and len(set(zones.values())) == 1
    return {"zones": zones, "observed_hands": obs,
            "symmetric": sym}
