"""Medial axis — the silhouette's own skeleton.

Zhang–Suen thinning peels the foreground one border layer at a
time until only the centerline remains: the shape's medial axis.
On it, endpoints mark extremities (head top, hand tips, feet) and
branchpoints mark junctions (neck, crotch). This is the classic
shape-skeleton the joint model is meant to explain — a second,
bottom-up route to "where are the limbs".

Counts endpoints / branchpoints and returns the thinned pixel
set. Downscales hard first: thinning is O(border × iterations).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator

# P2..P9 clockwise from north
_N = ((0, -1), (1, -1), (1, 0), (1, 1),
      (0, 1), (-1, 1), (-1, 0), (-1, -1))


def _thin(mask: List[bytearray], w: int, h: int) -> None:
    """In-place Zhang–Suen thinning."""
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            kill = []
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if not mask[y][x]:
                        continue
                    p = [mask[y + dy][x + dx] for dx, dy in _N]
                    b = sum(p)
                    if b < 2 or b > 6:
                        continue
                    a = sum(1 for i in range(8)
                            if p[i] == 0 and p[(i + 1) % 8] == 1)
                    if a != 1:
                        continue
                    if step == 0:
                        if p[0] * p[2] * p[4] or p[2] * p[4] * p[6]:
                            continue
                    else:
                        if p[0] * p[2] * p[6] or p[0] * p[4] * p[6]:
                            continue
                    kill.append((x, y))
            for x, y in kill:
                mask[y][x] = 0
            changed = changed or bool(kill)


def _count(mask: List[bytearray], w: int, h: int,
           px: int, py: int) -> Tuple[int, int]:
    """(neighbors, transitions) on the 8-neighborhood."""
    p = [mask[py + dy][px + dx] for dx, dy in _N]
    b = sum(p)
    return b, p


def analyze(bmp: Bitmap) -> Optional[dict]:
    """{pixels, endpoints, branchpoints, endpoint_xy,
    branchpoint_xy} — thinned centerline summary."""
    small = bmp.downscale(128)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width,
                                      small.height)
    if size == 0:
        return None
    w, h = small.width, small.height
    _thin(comp, w, h)
    ep, bp, pix = [], [], 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not comp[y][x]:
                continue
            pix += 1
            b, _ = _count(comp, w, h, x, y)
            if b == 1:
                ep.append((x, y))
            elif b >= 3:
                bp.append((x, y))
    return {"pixels": pix,
            "endpoints": len(ep),
            "branchpoints": len(bp),
            "endpoint_xy": ep,
            "branchpoint_xy": bp,
            "state": "observed",
            "basis": "Zhang-Suen thinned foreground mask"}
