"""Convex hull — the silhouette wrapped tight.

The hull is the smallest convex shape containing every foreground
pixel. Its descriptors complement the contour's: solidity
(area / hull_area) drops when limbs carve deep concavities —
spread arms, bent knees, hand-on-hip triangles — while the hull
itself gives a posture-tolerant bounding shape that ignores holes.

Graham scan over the foreground pixel set (deduped, sorted).
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator


def _points(mask: List[bytearray]) -> List[Tuple[int, int]]:
    pts = []
    for y, row in enumerate(mask):
        for x, v in enumerate(row):
            if v:
                pts.append((x, y))
    return pts


def _cross(o, a, b) -> int:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _hull(pts: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Andrew monotone chain — hull vertices CCW."""
    pts = sorted(set(pts))
    if len(pts) <= 1:
        return pts
    lo = []
    for p in pts:
        while len(lo) >= 2 and _cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    hi = []
    for p in reversed(pts):
        while len(hi) >= 2 and _cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _poly_area(h: List[Tuple[int, int]]) -> float:
    if len(h) < 3:
        return 0.0
    s = 0
    for i, (x1, y1) in enumerate(h):
        x2, y2 = h[(i + 1) % len(h)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def describe(bmp: Bitmap) -> Optional[dict]:
    """{vertices, area_px, hull_area_px, solidity, centroid} or None."""
    small = bmp.downscale(512)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width, small.height)
    if size == 0:
        return None
    pts = _points(comp)
    h = _hull(pts)
    ha = _poly_area(h)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return {"vertices": len(h),
            "area_px": size,
            "hull_area_px": round(ha, 1),
            "solidity": round(size / ha, 3) if ha else None,
            "centroid": [round(cx, 1), round(cy, 1)],
            "state": "observed",
            "basis": "foreground silhouette convex hull"}
