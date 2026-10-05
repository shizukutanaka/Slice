"""Hu moments — the silhouette's invariant fingerprint.

Seven combinations of normalized central moments that stay fixed
under translation, scale, and rotation (the first six; the
seventh additionally under reflection, sign aside). Two crops of
the same person at different sizes produce nearly the same vector
— which is exactly what a shape signature needs. `match` uses the
classic log-space distance (cv2.matchShapes I1).

Computed on the foreground mask; a synthetic straight-on figure
lands where upright humanoids land.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator


def _central(comp: List[bytearray], size: int):
    sx = sy = 0.0
    xs = ys = 0.0
    for y, row in enumerate(comp):
        for x, v in enumerate(row):
            if v:
                sx += x
                sy += y
    n = float(size)
    cx, cy = sx / n, sy / n
    mu = {}
    for p, q in ((2, 0), (0, 2), (1, 1), (3, 0), (0, 3),
                 (2, 1), (1, 2)):
        s = 0.0
        for y, row in enumerate(comp):
            dy = y - cy
            for x, v in enumerate(row):
                if v:
                    s += ((x - cx) ** p) * (dy ** q)
        mu[(p, q)] = s / n
    return n, mu


def _nu(mu, n, p, q):
    """Scale-normalized central moment. `mu` here is already
    divided by the pixel count, so the remaining scale factor is
    n**((p+q)/2)."""
    return mu[(p, q)] / (n ** ((p + q) / 2.0))


def moments(bmp: Bitmap) -> Optional[List[float]]:
    """The 7 Hu invariants (h7 signed). None if no foreground."""
    small = bmp.downscale(512)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width,
                                      small.height)
    if size == 0:
        return None
    n, mu = _central(comp, size)
    nu = {(p, q): _nu(mu, n, p, q)
          for p, q in ((2, 0), (0, 2), (1, 1), (3, 0), (0, 3),
                       (2, 1), (1, 2))}
    n20, n02, n11 = nu[2, 0], nu[0, 2], nu[1, 1]
    n30, n03, n21, n12 = nu[3, 0], nu[0, 3], nu[2, 1], nu[1, 2]
    h1 = n20 + n02
    h2 = (n20 - n02) ** 2 + 4 * n11 ** 2
    h3 = (n30 - 3 * n12) ** 2 + (3 * n21 - n03) ** 2
    h4 = (n30 + n12) ** 2 + (n21 + n03) ** 2
    h5 = ((n30 - 3 * n12) * (n30 + n12)
          * ((n30 + n12) ** 2 - 3 * (n21 + n03) ** 2)
          + (3 * n21 - n03) * (n21 + n03)
          * (3 * (n30 + n12) ** 2 - (n21 + n03) ** 2))
    h6 = ((n20 - n02) * ((n30 + n12) ** 2 - (n21 + n03) ** 2)
          + 4 * n11 * (n30 + n12) * (n21 + n03))
    h7 = ((3 * n21 - n03) * (n30 + n12)
          * ((n30 + n12) ** 2 - 3 * (n21 + n03) ** 2)
          - (n30 - 3 * n12) * (n21 + n03)
          * (3 * (n30 + n12) ** 2 - (n21 + n03) ** 2))
    return [h1, h2, h3, h4, h5, h6, h7]


def match(a: List[float], b: List[float]) -> float:
    """cv2.matchShapes(I1)-style distance on log-magnitudes."""
    def t(v):
        return math.copysign(math.log10(abs(v)), v) if v else 0.0
    return sum(abs(t(x) - t(y)) for x, y in zip(a, b))
