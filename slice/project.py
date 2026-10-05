"""Projection profiles — the silhouette as two histograms.

Sum the foreground mask along each axis and the body becomes two
1-D curves: the vertical profile swells at shoulders, narrows at
the waist, splits at the crotch; the horizontal profile marks
where mass sits left-to-right. Peaks and valleys in those curves
are pose-independent structure — the shadow grammar underneath
the skeleton.

Local maxima above a fraction of the global peak are reported
with their positions; `bands` splits the vertical profile into
named thirds so callers can ask "where does the mass live".
"""

from __future__ import annotations

from typing import List, Optional

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator


def _peaks(prof: List[int], frac: float = 0.5) -> List[dict]:
    if not prof:
        return []
    hi = max(prof)
    if hi == 0:
        return []
    out = []
    for i in range(1, len(prof) - 1):
        if (prof[i] >= prof[i - 1] and prof[i] >= prof[i + 1]
                and prof[i] >= hi * frac):
            if out and prof[i] == prof[out[-1]["at"]]:
                continue
            out.append({"at": i, "value": prof[i]})
    return out


def analyze(bmp: Bitmap) -> Optional[dict]:
    """{rows, cols, v_peaks, h_peaks, bands, widest_row} or None."""
    small = bmp.downscale(256)
    est = HeuristicPoseEstimator()
    mask = est._mask(small)
    comp, size = est._largest_component(mask, small.width,
                                      small.height)
    if size == 0:
        return None
    w, h = small.width, small.height
    rows = [sum(comp[y]) for y in range(h)]
    cols = [sum(comp[y][x] for y in range(h)) for x in range(w)]
    top = next(i for i, v in enumerate(rows) if v)
    bot = h - 1 - next(i for i, v in enumerate(reversed(rows)) if v)
    span = bot - top
    bands = {}
    if span > 0:
        third = span / 3.0
        for name, y0, y1 in (("upper", top, top + third),
                             ("middle", top + third, top + 2 * third),
                             ("lower", top + 2 * third, bot + 1)):
            bands[name] = sum(rows[int(y0):int(y1)])
    return {"rows": rows,
            "cols": cols,
            "v_peaks": _peaks(rows),
            "h_peaks": _peaks(cols),
            "bands": bands,
            "widest_row": rows.index(max(rows)),
            "bbox_rows": [top, bot],
            "state": "observed",
            "basis": "foreground mask projections"}
