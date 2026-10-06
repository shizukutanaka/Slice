"""Weight dominance — which leg carries the load.

Contrapposto is visible in a single frame: the pelvis shifts over
the stance leg. Pelvis x vs the ankle midpoint approximates where
mass sits. Two cues combine — pelvis offset toward a side, and
knee flexion unloading a leg — each reported as evidence with a
direction and strength, not a bare label.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .skeleton import Skeleton


def cues(skel: Skeleton) -> List[dict]:
    """[{cue, side, strength 0-1}] — evidence, honest direction."""
    out: List[dict] = []
    pelvis = skel.point("pelvis")
    al = skel.point("ankle_l")
    ar = skel.point("ankle_r")
    if pelvis and al and ar:
        mid = (al[0] + ar[0]) / 2.0
        span = abs(ar[0] - al[0]) or 1.0
        off = (pelvis[0] - mid) / (span / 2.0)  # -1..1 of half-span
        if abs(off) > 0.15:
            # +x = right-shifted → right dominant
            out.append({"cue": "pelvis_shift",
                        "side": "r" if off > 0 else "l",
                        "strength": round(min(abs(off), 1.0), 2)})
        else:
            out.append({"cue": "pelvis_centered",
                        "side": "even", "strength": 0.5})

    for side in ("l", "r"):
        hip = skel.point(f"hip_{side}")
        knee = skel.point(f"knee_{side}")
        ankle = skel.point(f"ankle_{side}")
        if not (hip and knee and ankle):
            continue
        # flexed knee unloads that leg → other side dominant
        straight = abs(ankle[0] - hip[0])
        leg = (abs(knee[0] - hip[0]) + abs(ankle[0] - knee[0])) or 1.0
        bend = straight / leg
        if bend < 0.5:
            out.append({"cue": f"unloaded_{side}",
                        "side": "r" if side == "l" else "l",
                        "strength": 0.7})
    return out


def assess(skel: Skeleton) -> dict:
    """{dominant, confidence, cues} — dominant in l|r|even|unknown."""
    c = cues(skel)
    votes: Dict[str, float] = {"l": 0.0, "r": 0.0, "even": 0.0}
    for cue in c:
        votes[cue["side"]] = votes.get(cue["side"], 0.0) + cue["strength"]
    total = sum(votes.values())
    if total < 0.5:
        return {"dominant": "unknown", "confidence": 0.0, "cues": c}
    side = max(votes, key=votes.get)
    conf = round(votes[side] / total, 2)
    return {"dominant": side, "confidence": conf, "cues": c}
