"""End-to-end pipeline: image bytes -> Knowledge dict.

Import -> Pose -> Skeleton -> Prediction -> Ratio -> Knowledge.
Shared by the CLI and the REST layer so both produce identical output.
"""

from __future__ import annotations

from typing import Optional

from . import (__version__, angles, balance, bitmap, classify, dynamics,
               framepos, gesture, knowledge, occlusion, pose, predict,
               ratio, spine, style, symmetry)
from .skeleton import OBSERVED, PREDICTED

ESTIMATOR = pose.HeuristicPoseEstimator()


def analyze(raw: bytes, *, model: Optional[str] = None,
            source_name: str = "") -> dict:
    bmp = bitmap.decode(raw)
    skel = ESTIMATOR.estimate(bmp, model or "adult")
    added = predict.complete(skel, model)
    ratios = ratio.analyze(skel, centroid=skel.centroid)
    cls = classify.analyze(skel)
    doc = knowledge.build(
        skel, ratios, cls,
        image_sha256=knowledge.sha256(raw),
        source_name=source_name,
        engine={"name": ESTIMATOR.name, "version": ESTIMATOR.version,
                "slice": __version__},
    )
    doc["prediction"]["filled"] = [j.name for j in added]
    doc["style"] = style.analyze(bmp)
    doc["analysis"] = {
        "angles": angles.analyze(skel),
        "symmetry": symmetry.score(skel),
        "balance": balance.assess(skel),
        "spine": spine.classify(skel),
        "gesture": gesture.summarize(skel),
        "dynamics": dynamics.score(skel),
        "occlusion": occlusion.audit(skel),
        "frame": framepos.analyze(skel, skel.image_width,
                                  skel.image_height),
    }
    doc["warnings"] = _warnings(skel)
    doc["_bitmap"] = bmp      # runtime only: overlay rendering
    doc["_skeleton"] = skel   # runtime only
    return doc


def _warnings(skel) -> list:
    """Evidence-thinness flags: which parts of the document rest on
    prediction rather than on anything visible in the image."""
    obs = {n for n, j in skel.joints.items() if j.state == OBSERVED}
    w = []
    if len(obs) < 8:
        w.append("few_observed_joints")
    if not any(n.startswith("wrist") for n in obs):
        w.append("no_observed_wrists")
    if not any(n.startswith("ankle") or n.startswith("foot") for n in obs):
        w.append("no_observed_feet")
    return w


def strip_runtime(doc: dict) -> dict:
    """Knowledge JSON is the product; drop non-serializable internals."""
    return {k: v for k, v in doc.items() if not k.startswith("_")}


def observed_count(doc: dict) -> int:
    return len(doc["prediction"]["observed"])


def predicted_count(doc: dict) -> int:
    return len(doc["prediction"]["predicted"])
