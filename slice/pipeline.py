"""End-to-end pipeline: image bytes -> Knowledge dict.

Import -> Pose -> Skeleton -> Prediction -> Ratio -> Knowledge.
Shared by the CLI and the REST layer so both produce identical output.
"""

from __future__ import annotations

from typing import Optional

from . import __version__, bitmap, classify, knowledge, pose, predict, ratio, style
from .anatomy import BODY_MODELS
from .skeleton import PREDICTED

ESTIMATOR = pose.HeuristicPoseEstimator()


def analyze(raw: bytes, *, model: Optional[str] = None,
            source_name: str = "") -> dict:
    if model and model not in BODY_MODELS:
        raise ValueError(f"unknown body model {model!r} "
                         f"(expected one of {sorted(BODY_MODELS)})")
    bmp = bitmap.decode(raw)
    skel = ESTIMATOR.estimate(bmp, model or "adult")
    if model:
        # A user-selected model pins every prior AND the reported model —
        # mark it 'forced' so the JSON never reads it as an estimate.
        skel.body_model = {"name": model,
                           "label": BODY_MODELS[model]["label"],
                           "measured_head_ratio":
                               skel.body_model.get("measured_head_ratio"),
                           "state": "forced"}
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
    doc["_bitmap"] = bmp      # runtime only: overlay rendering
    doc["_skeleton"] = skel   # runtime only
    return doc


def strip_runtime(doc: dict) -> dict:
    """Knowledge JSON is the product; drop non-serializable internals."""
    return {k: v for k, v in doc.items() if not k.startswith("_")}


def observed_count(doc: dict) -> int:
    return len(doc["prediction"]["observed"])


def predicted_count(doc: dict) -> int:
    return len(doc["prediction"]["predicted"])
