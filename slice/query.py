"""Pose search by example — rank skeletons by bone-direction match.

Given a query skeleton and a list of candidates, rank them by the
mean cosine similarity of shared bone directions. Direction, not
position: a small person doing the same pose ranks the same as a
large one. Missing bones simply don't vote — a query with no arms
can't judge arm similarity, and says so via `compared`.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .landmarks import BONES
from .skeleton import Skeleton


def _dirs(skel: Skeleton) -> dict:
    out = {}
    for a, b in BONES:
        pa, pb = skel.point(a), skel.point(b)
        if pa and pb:
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            n = math.hypot(dx, dy)
            if n:
                out[(a, b)] = (dx / n, dy / n)
    return out


def similarity(query: Skeleton, other: Skeleton) -> Optional[dict]:
    """{score (0-1), compared, skipped} — mean cosine over shared
    bones, shifted to 0..1. None if no bone exists in both."""
    qa, ob = _dirs(query), _dirs(other)
    shared = [k for k in qa if k in ob]
    if not shared:
        return None
    s = sum(qa[k][0] * ob[k][0] + qa[k][1] * ob[k][1] for k in shared)
    score = (s / len(shared) + 1.0) / 2.0
    return {"score": round(score, 4),
            "compared": len(shared),
            "skipped": len(BONES) - len(shared)}


def rank(query: Skeleton,
         candidates: List[Skeleton]) -> List[dict]:
    """Candidates sorted best-first: [{index, score, compared}]."""
    out = []
    for i, c in enumerate(candidates):
        s = similarity(query, c)
        if s is not None:
            out.append({"index": i, **s})
    out.sort(key=lambda r: -r["score"])
    return out
