"""Pose clustering — tiny k-means over bone-direction features.

Each skeleton becomes a 34-dim vector of its 17 bone unit
directions (missing bones = 0,0 — they cluster by absence too).
k-means++ seeding keeps the result deterministic via `seed`; a few
iterations suffice for small analysis sets. Returns the clusters
with the skeleton index each holds — group first, then look.
"""

from __future__ import annotations

import math
import random
from typing import List, Optional

from .landmarks import BONES
from .skeleton import Skeleton


def features(skel: Skeleton) -> List[float]:
    """34-dim bone-direction vector."""
    vec: List[float] = []
    for a, b in BONES:
        pa, pb = skel.point(a), skel.point(b)
        if pa and pb:
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            n = math.hypot(dx, dy) or 1.0
            vec += [dx / n, dy / n]
        else:
            vec += [0.0, 0.0]
    return vec


def _dist(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def cluster(skels: List[Skeleton], k: int = 3,
            iters: int = 12, seed: int = 0) -> Optional[list]:
    """[{centroid, members (indices), size}] or None if no data."""
    if not skels or k < 1:
        return None
    k = min(k, len(skels))
    X = [features(s) for s in skels]
    rng = random.Random(seed)

    # k-means++ seeding
    cents = [list(X[rng.randrange(len(X))])]
    while len(cents) < k:
        d2 = [min(_dist(x, c) ** 2 for c in cents) for x in X]
        tot = sum(d2) or 1.0
        r, acc, pick = rng.random() * tot, 0.0, 0
        for i, w in enumerate(d2):
            acc += w
            if acc >= r:
                pick = i
                break
        cents.append(list(X[pick]))

    for _ in range(iters):
        assign = [min(range(k), key=lambda c: _dist(x, cents[c]))
                  for x in X]
        new = [[0.0] * len(X[0]) for _ in range(k)]
        cnt = [0] * k
        for a, x in zip(assign, X):
            cnt[a] += 1
            for i, v in enumerate(x):
                new[a][i] += v
        moved = False
        for c in range(k):
            if cnt[c]:
                nc = [v / cnt[c] for v in new[c]]
                if _dist(nc, cents[c]) > 1e-6:
                    moved = True
                cents[c] = nc
        if not moved:
            break

    out = [{"centroid": [round(v, 3) for v in cents[c]],
            "members": [i for i, a in enumerate(assign) if a == c],
            "size": 0} for c in range(k)]
    for o in out:
        o["size"] = len(o["members"])
    return [o for o in out if o["size"]]
