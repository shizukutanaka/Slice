"""Plumb-line alignment — posture quality, not posture category.

Classical posture analysis drops a vertical line through the ear:
shoulder, hip and ankle should stack under it. Head forward of the
line is forward-head posture; pelvis forward is sway-back. Works on
the skeleton's x-coordinates at each height — a continuous quality
measure where pose classification only says "standing".
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .skeleton import Skeleton

# landmarks on the plumb chain, top to bottom
_CHAIN = ("head", "neck", "chest", "pelvis")


def _obs(skel: Skeleton, name: str):
    """Observed-only lookup: a predicted joint is prior fill — a
    chord-placed chest or "foot below ankle" ankle would fabricate a
    plumb offset, so it is excluded like a missing joint."""
    j = skel.joints.get(name)
    if j is None or j.state != "observed":
        return None
    return (j.x, j.y)


def line(skel: Skeleton) -> Optional[dict]:
    """{x, joints, offsets} — plumb x = head/neck average (the
    reference); offsets = each joint's horizontal deviation in px
    and as a fraction of body height."""
    head = _obs(skel, "head")
    neck = _obs(skel, "neck")
    if not head or not neck:
        return None
    ref_x = (head[0] + neck[0]) / 2.0
    lo = max((j.y for j in skel.joints.values()
              if j.state == "observed"), default=0.0)
    body_h = max(lo - head[1], 1.0)

    offsets: Dict[str, dict] = {}
    for name in _CHAIN:
        p = _obs(skel, name)
        if not p:
            continue
        dx = p[0] - ref_x
        offsets[name] = {"dx": round(dx, 1),
                         "of_body_h": round(dx / body_h, 3)}
    # support reference: mean ankle x
    ankles = [p for p in (_obs(skel, "ankle_l"), _obs(skel, "ankle_r"))
              if p]
    if ankles:
        ax = sum(p[0] for p in ankles) / len(ankles)
        offsets["base"] = {"dx": round(ax - ref_x, 1),
                           "of_body_h": round((ax - ref_x) / body_h, 3)}
    return {"plumb_x": round(ref_x, 1), "offsets": offsets}


def forward_head(skel: Skeleton) -> Optional[dict]:
    """Head ahead of the torso line — the tech-neck measure."""
    r = line(skel)
    if not r or "head" not in r["offsets"] or "chest" not in r["offsets"]:
        return None
    d = r["offsets"]["head"]["dx"] - r["offsets"]["chest"]["dx"]
    return {"dx": round(d, 1),
            "posture": "forward_head" if abs(d) > 0.08 * _span(skel) else "neutral"}


def _span(skel: Skeleton) -> float:
    top = _obs(skel, "head")
    lo = max((j.y for j in skel.joints.values()
              if j.state == "observed"), default=0.0)
    return (lo - top[1]) if top else 200.0


def assess(skel: Skeleton) -> dict:
    """{plumb, forward_head, stack_score} — stack_score = mean
    |offset| of torso chain in body-h fractions (lower = better)."""
    r = line(skel)
    fh = forward_head(skel)
    out = {"plumb": r, "forward_head": fh, "stack_score": None}
    if r:
        vals = [abs(v["of_body_h"]) for k, v in r["offsets"].items()
                if k in _CHAIN]
        if vals:
            out["stack_score"] = round(sum(vals) / len(vals), 3)
    return out
