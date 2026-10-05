"""Radial signature — the silhouette as a polar distance curve.

From the foreground centroid, cast N rays and record how far each
travels before leaving the figure. Arms stretching out lengthen
their rays; a compact pose is flat. Normalized by the longest ray,
the vector is translation- and scale-invariant; `match` compares
signatures over all circular shifts, which cancels rotation.

A "star" signature: cheap, whole-shape, and complementary to the
skeleton (it doesn't care where joints are, only where mass
extends). None when there is no foreground.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator

N = 64


def _inside(comp: List[bytearray], w: int, h: int,
            x: int, y: int) -> bool:
    return 0 <= x < w and 0 <= y < h and comp[y][x]


def signature(bmp: Bitmap) -> Optional[List[float]]:
    """N-dim normalized radial distances from the fg centroid."""
    small = bmp.downscale(256)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width,
                                      small.height)
    if size == 0:
        return None
    w, h = small.width, small.height
    cx = cy = 0.0
    for y, row in enumerate(comp):
        for x, v in enumerate(row):
            if v:
                cx += x
                cy += y
    cx, cy = cx / size, cy / size
    if not _inside(comp, w, h, int(cx), int(cy)):
        # concave shapes can push the centroid outside; nudge to
        # the nearest fg pixel instead of giving up
        best = min(((x, y) for y in range(h) for x in range(w)
                    if comp[y][x]),
                   key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        cx, cy = float(best[0]), float(best[1])
    sig = []
    for i in range(N):
        ang = 2 * math.pi * i / N
        dx, dy = math.cos(ang), math.sin(ang)
        t = 0.0
        while _inside(comp, w, h,
                      int(round(cx + dx * t)),
                      int(round(cy + dy * t))):
            t += 1.0
        sig.append(t)
    peak = max(sig) or 1.0
    return [round(v / peak, 3) for v in sig]


def match(a: List[float], b: List[float]) -> float:
    """Best L1 distance over all circular shifts (rotation-free)."""
    if not a or not b:
        return float("inf")
    n = min(len(a), len(b))
    best = float("inf")
    for s in range(n):
        d = sum(abs(a[i] - b[(i + s) % n]) for i in range(n)) / n
        if d < best:
            best = d
    return round(best, 4)
