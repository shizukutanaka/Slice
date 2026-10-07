"""Implied dynamics — does the still look mid-motion?

A camera freezes motion; body geometry keeps the signature. A leg
off its stance axis, arms far from the torso line, the body's
balance point outside the feet — each is a cue that the frame
caught movement rather than rest. The score is a weighted vote of
observed cues, labelled `implied`, never "the person is moving".
"""

from __future__ import annotations

import math
from typing import Dict, List

from .skeleton import Skeleton


def _d(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _obs(skel: Skeleton, name: str):
    """Observed-only lookup: a predicted joint is prior fill —
    a cue fired on prior geometry is a fabricated measurement."""
    j = skel.joints.get(name)
    if j is None or j.state != "observed":
        return None
    return (j.x, j.y)


def cues(skel: Skeleton) -> List[dict]:
    """[{cue, weight, detail}] — all on observed joints."""
    out: List[dict] = []
    pelvis = _obs(skel, "pelvis")
    for side in ("l", "r"):
        hip = _obs(skel, f"hip_{side}")
        ankle = _obs(skel, f"ankle_{side}")
        if hip and ankle:
            leg = _d(hip, ankle) or 1.0
            off = abs(ankle[0] - hip[0]) / leg
            if off > 0.3:
                out.append({"cue": f"leg_off_axis_{side}",
                            "weight": 0.25,
                            "detail": round(off, 2)})
        shoulder = _obs(skel, f"shoulder_{side}")
        wrist = _obs(skel, f"wrist_{side}")
        if shoulder and wrist and pelvis:
            # wrist far laterally from torso → arm swing
            far = abs(wrist[0] - pelvis[0]) > 0.6 * _d(shoulder, wrist)
            if far:
                out.append({"cue": f"arm_out_{side}",
                            "weight": 0.15, "detail": None})

    al, ar = _obs(skel, "ankle_l"), _obs(skel, "ankle_r")
    if pelvis and al and ar:
        mid = (al[0] + ar[0]) / 2.0
        span = abs(ar[0] - al[0]) or 1.0
        if abs(pelvis[0] - mid) > 0.5 * span:
            out.append({"cue": "com_outside_feet", "weight": 0.35,
                        "detail": round(abs(pelvis[0] - mid) / span, 2)})
        if span > 0.5 * _span(skel):
            out.append({"cue": "wide_step", "weight": 0.2,
                        "detail": round(span / _span(skel), 2)})
    return out


def _span(skel: Skeleton) -> float:
    # observed-only span with the torso-length fallback of
    # skeleton.body_span: a predicted head/foot is prior fill
    top = _obs(skel, "head")
    lo = max((j.y for j in skel.joints.values()
              if j.state == "observed"), default=0.0)
    if top and lo - top[1] > 0:
        return lo - top[1]
    n, p = _obs(skel, "neck"), _obs(skel, "pelvis")
    if n and p:
        return _d(n, p) or 200.0
    return 200.0


def score(skel: Skeleton) -> dict:
    """{score 0-1, verdict, cues} — score = Σweights capped at 1."""
    c = cues(skel)
    s = min(1.0, sum(x["weight"] for x in c))
    verdict = ("dynamic" if s >= 0.6 else
               "possibly_dynamic" if s >= 0.3 else "static")
    return {"score": round(s, 2), "verdict": verdict,
            "state": "implied", "cues": c}
