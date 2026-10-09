"""Age cue — head-to-body ratio as a developmental indicator.

The single most reliable visual age cue is head proportion: an
infant's head is ~1/4 of total height, a child's ~1/5, an adult's
~1/7.5 (8 heads tall in classical canon). Body model selection
picks a skeleton scale; this reports the continuous ratio as a
development band with honest `estimated` marking.
"""

from __future__ import annotations

from typing import Optional

from .skeleton import Skeleton

# ratio -> (band, note). Boundaries are priors, not hard lines.
_BANDS = (
    (0.28, "infant",   "head ≈ 1/4 of height"),
    (0.22, "child",    "head ≈ 1/5 of height"),
    (0.16, "juvenile", "head ≈ 1/6.5 of height"),
    (0.11, "adult",    "head ≈ 1/7.5–8 of height"),
    (0.0,  "senior_doubt", "unusually small head fraction"),
)


def ratio(skel: Skeleton) -> Optional[float]:
    """head_length / body_height as a 0-1 fraction."""
    head = skel.point("head")
    neck = skel.point("neck")
    if not head or not neck:
        return None
    lo = max((j.y for j in skel.joints.values()), default=0.0)
    body_h = lo - head[1]
    if body_h <= 0:
        return None
    head_len = (neck[1] - head[1]) * 1.2  # crown to jaw ≈ head height
    return head_len / body_h


def estimate(skel: Skeleton) -> Optional[dict]:
    """{ratio, band, note, state} — None without head+neck."""
    r = ratio(skel)
    if r is None:
        return None
    for bound, band, note in _BANDS:
        if r >= bound:
            return {"ratio": round(r, 3), "band": band,
                    "note": note, "state": "estimated"}
    return None


def heads_tall(skel: Skeleton) -> Optional[float]:
    """How many head-lengths tall the figure is — the canon unit."""
    r = ratio(skel)
    return round(1.0 / r, 2) if r else None
