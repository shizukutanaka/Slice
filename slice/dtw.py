"""Dynamic time warping — compare pose sequences at any speed.

Two clips of "the same wave" differ in tempo. Frame-by-frame
distance says they're different; DTW finds the cheapest temporal
alignment — each frame may map to a run of frames on the other
side. The classic O(n·m) DP with the standard (1,1),(0,1),(1,0)
steps; distance between two frames is mean joint displacement
over their shared observed joints.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .skeleton import Skeleton

_INF = float("inf")


def frame_dist(a: Skeleton, b: Skeleton) -> float:
    """Mean per-joint Euclidean distance over common joints.
    Missing in either = not counted; if nothing overlaps the
    frames are simply incomparable (inf)."""
    tot = cnt = 0
    for name, ja in a.joints.items():
        jb = b.joints.get(name)
        if jb is None:
            continue
        tot += math.hypot(jb.x - ja.x, jb.y - ja.y)
        cnt += 1
    return tot / cnt if cnt else _INF


def align(seq_a: List[Skeleton],
          seq_b: List[Skeleton]) -> Optional[dict]:
    """{cost, path_len, per_frame, path} — normalized cost per
    aligned frame pair."""
    n, m = len(seq_a), len(seq_b)
    if not n or not m:
        return None
    dp = [[_INF] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = frame_dist(seq_a[i - 1], seq_b[j - 1])
            if d == _INF:
                d = 1e6  # incomparable frames cost a lot but don't block
            dp[i][j] = d + min(dp[i - 1][j], dp[i][j - 1],
                               dp[i - 1][j - 1])
    # backtrack
    i, j, path = n, m, []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        i, j = min(((i - 1, j - 1), (i - 1, j), (i, j - 1)),
                   key=lambda ij: dp[ij[0]][ij[1]])
    path.reverse()
    cost = dp[n][m]
    return {"cost": round(cost, 2),
            "path_len": len(path),
            "per_frame": round(cost / len(path), 2) if path else None,
            "path": path}
