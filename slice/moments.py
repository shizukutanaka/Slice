"""Image moments — the silhouette as a statistical ellipse.

Raw moments (m00 area, m10/m01 → centroid) and central moments
(mu20/mu02/mu11 → covariance) reduce a silhouette to a handful of
numbers. From the covariance we get the equivalent ellipse:
orientation angle, major/minor axes, eccentricity — a pose-tolerant
shape description that hull (boundary) and contour (outline)
don't capture.

This is the stdlib equivalent of OpenCV's `cv2.moments` +
`cv2.fitEllipse`, computed directly on the foreground mask.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator


def describe(bmp: Bitmap) -> Optional[dict]:
    """{area, centroid, angle_deg, major, minor, eccentricity}."""
    small = bmp.downscale(512)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width,
                                      small.height)
    if size == 0:
        return None
    sx = sy = sxx = syy = sxy = 0.0
    for y, row in enumerate(comp):
        for x, v in enumerate(row):
            if v:
                sx += x
                sy += y
                sxx += x * x
                syy += y * y
                sxy += x * y
    n = float(size)
    cx, cy = sx / n, sy / n
    mu20 = sxx / n - cx * cx
    mu02 = syy / n - cy * cy
    mu11 = sxy / n - cx * cy
    # ellipse axes from covariance eigenvalues
    tr = mu20 + mu02
    disc = math.hypot(mu20 - mu02, 2 * mu11)
    l1 = (tr + disc) / 2.0
    l2 = (tr - disc) / 2.0
    angle = 0.5 * math.degrees(math.atan2(2 * mu11, mu20 - mu02))
    major = 4.0 * math.sqrt(max(l1, 0.0))
    minor = 4.0 * math.sqrt(max(l2, 0.0))
    ecc = math.sqrt(1.0 - l2 / l1) if l1 > 0 else 0.0
    return {"area_px": int(n),
            "centroid": [round(cx, 1), round(cy, 1)],
            "angle_deg": round(angle, 1),
            "major_px": round(major, 1),
            "minor_px": round(minor, 1),
            "eccentricity": round(ecc, 3),
            "state": "observed",
            "basis": "foreground mask central moments"}
