"""Pose retargeting — transfer a pose onto different proportions.

Retargeting takes the bone *directions* of a source skeleton and
rebuilds positions with the *bone lengths* of a target figure — the
same pose on a different body. Output joints are state=predicted:
the result is synthesized geometry, never observed evidence.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

from .skeleton import Joint, Skeleton

# kinematic children, pelvis-rooted (same tree as bvh/rig)
_CHILDREN = {
    "pelvis": ["chest", "hip_l", "hip_r"],
    "chest": ["neck"],
    "neck": ["head", "shoulder_l", "shoulder_r"],
    "shoulder_l": ["elbow_l"], "elbow_l": ["wrist_l"],
    "shoulder_r": ["elbow_r"], "elbow_r": ["wrist_r"],
    "hip_l": ["knee_l"], "knee_l": ["ankle_l"], "ankle_l": ["foot_l"],
    "hip_r": ["knee_r"], "knee_r": ["ankle_r"], "ankle_r": ["foot_r"],
}


def _vec(a, b) -> Optional[Tuple[float, float]]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dx / L, dy / L, L) if L > 1e-9 else None


def retarget(src: Skeleton, dst: Skeleton) -> Skeleton:
    """Source directions × target lengths, walked from pelvis down."""
    out = Skeleton(dst.image_width, dst.image_height)
    out.body_model = dict(dst.body_model)
    out.orientation = dict(src.orientation)
    root = dst.point("pelvis") or src.point("pelvis")
    if root is None:
        raise ValueError("pelvis required in source or target")
    pos: Dict[str, tuple] = {"pelvis": root}
    out.set(Joint("pelvis", root[0], root[1], 0.5,
                  state="predicted", basis="retargeted root"))
    queue = ["pelvis"]
    while queue:
        parent = queue.pop(0)
        for child in _CHILDREN.get(parent, []):
            sv = None
            sp, sc = src.point(parent), src.point(child)
            if sp and sc:
                sv = _vec(sp, sc)
            dp, dc = dst.point(parent), dst.point(child)
            dv = _vec(dp, dc) if dp and dc else None
            if sv is None and dv is None:
                continue
            dx, dy = sv[:2] if sv else dv[:2]
            length = dv[2] if dv else sv[2]
            x = pos[parent][0] + dx * length
            y = pos[parent][1] + dy * length
            pos[child] = (x, y)
            # basis records where each half came from: a missing
            # source bone means the direction is the target's own
            # geometry — "retargeted" alone would hide that
            basis = "retargeted" if sv else "retargeted (target dir)"
            if sv and "predicted" in (src.joints[parent].state,
                                      src.joints[child].state):
                # direction rode on a guessed bone — same disclosure
                # as predict's "(predicted anchor)"
                basis = "retargeted (predicted bone)"
            if dv is None:
                basis += " (source len)"
            out.set(Joint(child, x, y, 0.5, state="predicted",
                          basis=basis))
            queue.append(child)
    return out
