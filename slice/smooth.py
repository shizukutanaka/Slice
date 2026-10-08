"""Temporal smoothing of joint tracks across a frame series.

Per-frame estimates jitter — a wrist jumps a few pixels frame to
frame even when the person is still. `smooth` applies a symmetric
moving average over each joint's track, cutting jitter while
keeping real motion. Missing frames break nothing: a joint absent
from a window's frames just averages what exists, and frames where
the joint is missing stay missing — smoothing never invents a
position. And an observed centre averages only observed neighbours:
predicted guesses in the window must not pull a measured joint
toward a fabricated location.

Frames may differ in resolution — a neighbour in a different frame
space is rescaled into the centre frame's space before averaging
(px positions are frame-relative), and `jitter` reports
displacement in the earlier frame's space for the same reason.
"""

from __future__ import annotations

from typing import List

from .skeleton import OBSERVED, Joint, Skeleton


def smooth(series: List[Skeleton], radius: int = 1) -> List[Skeleton]:
    """Return per-frame skeletons with positions averaged over
    [t-radius, t+radius]. Confidence and state are taken from the
    center frame — only position is smoothed."""
    n = len(series)
    out: List[Skeleton] = []
    for t in range(n):
        src = series[t]
        dst = Skeleton(src.image_width, src.image_height)
        dst.body_model = dict(src.body_model)
        dst.orientation = dict(src.orientation)
        # the mask centroid is a measured point in this frame's
        # space — dropping it would leave downstream consumers
        # (track's anchor, norm's transform) with nothing
        dst.centroid = src.centroid
        lo, hi = max(0, t - radius), min(n, t + radius + 1)
        for name, j in src.joints.items():
            xs, ys, cnt = 0.0, 0.0, 0
            for tt in range(lo, hi):
                o = series[tt].joints.get(name)
                if o is None:
                    continue
                # an observed centre averages only observed
                # neighbours — predicted guesses must not pull a
                # measured joint toward a fabricated location
                if j.state == OBSERVED and o.state != OBSERVED:
                    continue
                ot = series[tt]
                ox, oy = o.x, o.y
                if (ot.image_width != src.image_width
                        or ot.image_height != src.image_height):
                    # a px position means nothing outside its own
                    # frame space — rescale into the centre frame's
                    ox *= src.image_width / ot.image_width
                    oy *= src.image_height / ot.image_height
                xs += ox
                ys += oy
                cnt += 1
            dst.set(Joint(name, xs / cnt, ys / cnt, j.confidence,
                          state=j.state, basis=j.basis))
        out.append(dst)
    return out


def jitter(series: List[Skeleton], joint: str = "pelvis") -> float:
    """Mean frame-to-frame displacement of a joint — a jitter metric."""
    steps = []
    for t in range(1, len(series)):
        a = series[t - 1].joints.get(joint)
        b = series[t].joints.get(joint)
        if a and b:
            fa, fb = series[t - 1], series[t]
            bx, by = b.x, b.y
            if (fa.image_width != fb.image_width
                    or fa.image_height != fb.image_height):
                # report in the earlier frame's space — a raw px
                # diff across resolutions counts the resize as
                # motion (and hides real motion the other way)
                bx *= fa.image_width / fb.image_width
                by *= fa.image_height / fb.image_height
            steps.append(((bx - a.x) ** 2 + (by - a.y) ** 2) ** 0.5)
    return round(sum(steps) / len(steps), 3) if steps else 0.0
