"""Pseudo-3D lift — honest z coordinates for a 2D skeleton.

A 2D image can't show depth, but the facing estimate carries a weak
depth cue: in a side/profile view one side of the body is farther
from the camera. `lift` assigns every joint (x, y, z):

- facing "front"/"three-quarter"/"unknown" → z = 0 everywhere
  (the honest default: no depth evidence means a flat estimate)
- facing "side" → joints on the image's far side get z = +half the
  shoulder width (they sit behind the sagittal plane)

Every z is tagged with its basis ("no_depth_cue" / "facing_side")
so consumers know the depth is a prior, not a measurement.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .skeleton import OBSERVED, Skeleton

# joints on a lateral side get pushed back in side view
_LATERAL = ("shoulder", "elbow", "wrist", "hip", "knee", "ankle",
            "foot")


def lift(skel: Skeleton) -> Dict[str, dict]:
    """{joint: {x, y, z, basis}} pseudo-3D coordinates."""
    ori = skel.orientation or {}
    facing = ori.get("facing", "unknown")

    # depth scale comes only from observed shoulder/hip widths —
    # a predicted endpoint is prior geometry, so borrowing it would
    # write the model table into the z axis as if it were measured
    half = 0.0
    for a, b in (("shoulder_l", "shoulder_r"), ("hip_l", "hip_r")):
        ja, jb = skel.joints.get(a), skel.joints.get(b)
        if (ja and jb and ja.state == OBSERVED
                and jb.state == OBSERVED):
            half = max(half, abs(jb.x - ja.x) / 2.0)

    out: Dict[str, dict] = {}
    far_left = facing == "side" and ori.get("side", "") == "left"

    for name, j in skel.joints.items():
        z, basis = 0.0, "no_depth_cue"
        if facing == "side" and half > 0:
            stem = name.rsplit("_", 1)
            lateral = len(stem) == 2 and stem[0] in _LATERAL
            if lateral:
                left = stem[1] == "l"
                # far side = the side facing away in the image
                if left != far_left:
                    z, basis = half, "facing_side"
        out[name] = {"x": round(j.x, 1), "y": round(j.y, 1),
                     "z": round(z, 1), "basis": basis}
    return out


def depth_spread(lifted: Dict[str, dict]) -> float:
    """Max z minus min z across the figure (0 = flat estimate)."""
    zs = [v["z"] for v in lifted.values()]
    return round(max(zs) - min(zs), 1) if zs else 0.0
