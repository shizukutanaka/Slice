"""Person candidates — every foreground component, ranked.

`estimate` looks at the single largest connected component and
assumes it is the person. `candidates` enumerates ALL components of
the foreground mask and ranks them, so a frame with two people (or a
person plus a prop) stops pretending there is only one blob.

Honesty note: a component is not a person — two overlapping people
merge into one blob, and a detached hat becomes a fake third. The
output says "candidate components", never "people detected".
"""

from __future__ import annotations

from collections import deque
from typing import List

from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator

_MIN_FRAC = 0.005


def _components(mask: List[bytearray], w: int, h: int) -> List[dict]:
    labels = [[0] * w for _ in range(h)]
    comps: List[dict] = []
    for y0 in range(h):
        for x0 in range(w):
            if not mask[y0][x0] or labels[y0][x0]:
                continue
            idx = len(comps) + 1
            size = 0
            lx, ty, rx, by = x0, y0, x0, y0
            q = deque([(x0, y0)])
            labels[y0][x0] = idx
            while q:
                x, y = q.popleft()
                size += 1
                lx, rx = min(lx, x), max(rx, x)
                ty, by = min(ty, y), max(by, y)
                for nx, ny in ((x + 1, y), (x - 1, y),
                               (x, y + 1), (x, y - 1)):
                    if (0 <= nx < w and 0 <= ny < h
                            and mask[ny][nx] and not labels[ny][nx]):
                        labels[ny][nx] = idx
                        q.append((nx, ny))
            comps.append({"size": size,
                          "bbox": (lx, ty, rx - lx + 1, by - ty + 1)})
    return comps


def candidates(bmp: Bitmap, est: HeuristicPoseEstimator = None,
               min_frac: float = _MIN_FRAC,
               top_k: int = 8) -> dict:
    """Rank foreground components as person candidates."""
    est = est or HeuristicPoseEstimator()
    small = bmp.downscale(est.max_dim)
    w, h = small.width, small.height
    mask = est._mask(small)
    frame = w * h
    comps = _components(mask, w, h)
    out = []
    for i, c in enumerate(sorted(comps, key=lambda c: -c["size"])):
        if c["size"] < frame * min_frac:
            continue
        lx, ty, bw, bh = c["bbox"]
        out.append({
            "rank": len(out),
            "size_px": c["size"],
            "fraction": round(c["size"] / frame, 4),
            "bbox": {"x": lx, "y": ty, "w": bw, "h": bh},
            "aspect": round(bw / max(1, bh), 3),
            "touches_edge": (lx == 0 or ty == 0
                             or lx + bw == w or ty + bh == h),
        })
        if len(out) >= top_k:
            break
    return {
        "n_components": len(comps),
        "n_candidates": len(out),
        "candidates": out,
        "dominant_share": (round(out[0]["size_px"] / frame, 4)
                           if out else 0.0),
        "note": "components are candidates, not confirmed people — "
                "overlap merges, detached parts inflate the count",
        "basis": "est._mask + 4-conn components @%dx%d" % (w, h),
    }
