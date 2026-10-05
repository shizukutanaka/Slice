"""Analysis quality grade — how much to trust one skeleton.

Every downstream claim inherits the weakness of the skeleton it
was built on. This aggregates that weakness into a single 0–1
score + letter grade:

  score = w_obs * observed_ratio
        + w_conf * mean_confidence(observed only)
        + w_spread * evidence_spread

Evidence spread penalizes results whose observations concentrate
in one region (e.g. only head+torso seen while all limbs are
predicted) — measured as the share of the four body regions
(head / torso / arms / legs) that have at least one observed joint.

The grade is honest about what it measures: it grades the
skeleton's evidence, never "how correct the pose is".
"""

from __future__ import annotations

from typing import Optional

from .skeleton import Skeleton

_REGIONS = {
    "head": ("head", "neck"),
    "torso": ("chest", "pelvis"),
    "arms": ("shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
             "wrist_l", "wrist_r"),
    "legs": ("hip_l", "hip_r", "knee_l", "knee_r",
             "ankle_l", "ankle_r", "foot_l", "foot_r"),
}

_W_OBS, _W_CONF, _W_SPREAD = 0.5, 0.3, 0.2
_GRADES = ((0.85, "A"), (0.7, "B"), (0.5, "C"), (0.3, "D"))


def grade(skel: Skeleton) -> dict:
    """{score, grade, observed_ratio, mean_confidence, regions} —
    the evidence-based trust score for this analysis."""
    joints = list(skel.joints.values())
    if not joints:
        return {"score": 0.0, "grade": "E",
                "observed_ratio": 0.0, "mean_confidence": None,
                "regions": {}}
    obs = [j for j in joints if j.state == "observed"]
    obs_ratio = len(obs) / len(joints)
    mean_conf = (sum(j.confidence for j in obs) / len(obs)
                 if obs else 0.0)
    regions = {name: any(skel.joints[n].state == "observed"
                         for n in names if n in skel.joints)
               for name, names in _REGIONS.items()}
    spread = sum(regions.values()) / len(regions)
    score = (_W_OBS * obs_ratio + _W_CONF * mean_conf
             + _W_SPREAD * spread)
    g = next((letter for thr, letter in _GRADES if score >= thr), "E")
    return {"score": round(score, 3), "grade": g,
            "observed_ratio": round(obs_ratio, 3),
            "mean_confidence": round(mean_conf, 3),
            "regions": regions,
            "state": "estimated",
            "basis": "aggregate of joint evidence, not pose truth"}
