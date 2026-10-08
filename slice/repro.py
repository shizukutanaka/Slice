"""Reproducibility check — does the same input still give this output?

A knowledge document claims "this image, this engine, these joints".
Nothing verifies the claim is stable: library changes, threshold
tweaks, or silent nondeterminism could make a re-run produce a
different skeleton without anyone noticing. `verify` re-estimates
from the recorded source image and diffs the result against the
stored skeleton, joint by joint.

What it catches:
- `position_drift` — recorded vs re-estimated position beyond
  `TOLERANCE_PX` (engine changed)
- `state_flip` — observed↔predicted flip (evidence reclassified)
- `missing` — joint present in doc, absent on re-run
- `added` — joint absent in doc, produced on re-run

verdict: `reproducible` (all joints within tolerance),
`drifted` (positions moved but no structural change),
`changed` (flips/misses/adds), `unverifiable` (no recorded frame
— position distances can't be checked at all). Positions are
compared in the *recorded* frame — re-estimated joints are
rescaled when the downscale differs, so resolution changes alone
don't count as drift.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

from .anatomy import DEFAULT_MODEL
from .bitmap import Bitmap
from .pose import HeuristicPoseEstimator
from .skeleton import OBSERVED, PREDICTED

TOLERANCE_PX = 2.0


def verify(doc: dict, bmp: Bitmap,
           estimator: Optional[HeuristicPoseEstimator] = None,
           tolerance: float = TOLERANCE_PX) -> Dict:
    """Re-estimate `bmp` and diff against `doc`'s recorded skeleton.

    The document's frame size and joint list come from
    `doc["skeleton"]`; the model from `doc["engine"]`-adjacent fields
    is not part of schema v1, so `model` falls back to the estimator
    default — disclosed in `basis`.
    """
    rec = (doc.get("skeleton") or {}).get("joints") or {}
    frame = (doc.get("skeleton") or {}).get("frame") or {}
    model = ((doc.get("skeleton") or {}).get("body_model") or {}) \
        .get("name") or DEFAULT_MODEL

    est = estimator or HeuristicPoseEstimator()
    sk = est.estimate(bmp, model)
    fw, fh = frame.get("width"), frame.get("height")
    # A doc without recorded frame dims gives no coordinate space to
    # verify against: `or 1.0` would silently assume the re-estimate's
    # space and compute px distances between unrelated frames —
    # fabricated drifts on one side, real ones hidden on the other —
    # while `basis` still claimed "frame-rescaled". Missing/added/flips
    # are space-independent and stay verifiable; px distances don't.
    frame_verified = bool(fw and fh)
    sx = sk.image_width / fw if frame_verified else 1.0
    sy = sk.image_height / fh if frame_verified else 1.0

    drifts, flips, missing, added = [], [], [], []
    compared = 0
    for name, rj in rec.items():
        ej = sk.get(name)
        if ej is None:
            missing.append(name)
            continue
        compared += 1
        if ej.state != rj.get("state"):
            flips.append({"joint": name,
                          "was": rj.get("state"), "now": ej.state})
        if frame_verified:
            d = math.hypot(ej.x / sx - rj["x"], ej.y / sy - rj["y"])
            if d > tolerance:
                drifts.append({"joint": name,
                               "drift_px": round(d, 2)})
    for name in sk.joints:
        if name not in rec:
            added.append(name)

    verdict = ("changed" if flips or missing or added else
               "drifted" if drifts else
               "reproducible" if frame_verified else "unverifiable")
    return {
        "verdict": verdict,
        "joints_compared": compared,
        "frame_verified": frame_verified,
        "drifts": drifts,
        "state_flips": flips,
        "missing": sorted(missing),
        "added": sorted(added),
        "tolerance_px": tolerance,
        "state": "measured",
        "basis": ("re-estimate on source image vs recorded joints "
                  "(frame-rescaled)" if frame_verified else
                  "re-estimate on source image vs recorded joints "
                  "(frame unrecorded — px distances unverifiable)"),
    }


def reproducible(result: Dict) -> bool:
    return result["verdict"] == "reproducible"
