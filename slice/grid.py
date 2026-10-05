"""Occupancy grid — the silhouette as a K×K density map.

Clip the figure's bounding box into a grid and record how full
each cell is. Where radial signature measures "how far does mass
extend in each direction", the grid records "where inside the
figure's own frame does mass sit" — arms-up puts weight in the
outer-top cells, sitting puts it in the middle.

The vector is scale-invariant (cells are bbox fractions, not
pixels) and translation-invariant. `match` is plain L1 distance —
no rotation trick: a sideways person is genuinely different.
"""

from __future__ import annotations

from typing import List, Optional

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator

K = 8


def descriptor(bmp: Bitmap) -> Optional[List[float]]:
    """K*K fg-density vector over the largest component's bbox."""
    small = bmp.downscale(256)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width,
                                      small.height)
    if size == 0:
        return None
    xs = [x for y, row in enumerate(comp)
          for x, v in enumerate(row) if v]
    ys = [y for y, row in enumerate(comp)
          for v in row if v]
    x0, x1 = min(xs), max(xs) + 1
    y0, y1 = min(ys), max(ys) + 1
    cw = (x1 - x0) / K
    ch = (y1 - y0) / K
    counts = [[0] * K for _ in range(K)]
    cell_area = [[0] * K for _ in range(K)]
    for y in range(y0, y1):
        gy = min(int((y - y0) / ch), K - 1)
        for x in range(x0, x1):
            gx = min(int((x - x0) / cw), K - 1)
            cell_area[gy][gx] += 1
            if comp[y][x]:
                counts[gy][gx] += 1
    out = []
    for gy in range(K):
        for gx in range(K):
            a = cell_area[gy][gx]
            out.append(round(counts[gy][gx] / a, 3) if a else 0.0)
    return out


def match(a: List[float], b: List[float]) -> float:
    """Mean absolute difference of two grid vectors (0..1)."""
    n = min(len(a), len(b))
    if n == 0:
        return float("inf")
    return round(sum(abs(x - y) for x, y in zip(a, b)) / n, 4)
