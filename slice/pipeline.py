"""End-to-end pipeline: image bytes -> Knowledge dict.

Import -> Pose -> Skeleton -> Prediction -> Ratio -> Knowledge.
Shared by the CLI and the REST layer so both produce identical output.
"""

from __future__ import annotations

from typing import List, Optional

from . import (__version__, angles, balance, bitmap, classify, dynamics,
               framepos, gesture, knowledge, occlusion, pose, predict,
               ratio, spine, style, symmetry)
from .skeleton import OBSERVED, PREDICTED

ESTIMATOR = pose.HeuristicPoseEstimator()


def _build_doc(skel, bmp, image_sha: str, source_name: str,
               model: Optional[str]) -> dict:
    added = predict.complete(skel, model)
    ratios = ratio.analyze(skel, centroid=skel.centroid)
    cls = classify.analyze(skel)
    doc = knowledge.build(
        skel, ratios, cls,
        image_sha256=image_sha,
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


def analyze(raw: bytes, *, model: Optional[str] = None,
            source_name: str = "") -> dict:
    bmp = bitmap.decode(raw)
    skel = ESTIMATOR.estimate(bmp, model or "adult")
    return _build_doc(skel, bmp, knowledge.sha256(raw), source_name,
                      model)


def analyze_multi(raw: bytes, *, model: Optional[str] = None,
                  source_name: str = "", top_k: int = 4) -> List[dict]:
    """One Knowledge document per detected person.

    Each document is a complete v1 analysis of its own skeleton and
    carries a `people` block recording which foreground component it
    came from — same-image siblings, not a merged figure. The list
    may be shorter than the visible crowd (touching silhouettes are
    one component) or empty (nothing detected): the pixels decide.
    """
    bmp = bitmap.decode(raw)
    skels = ESTIMATOR.estimate_multi(bmp, model or "adult",
                                     top_k=top_k)
    sha = knowledge.sha256(raw)
    docs = [_build_doc(s, bmp, sha, source_name, model)
            for s in skels]
    for i, d in enumerate(docs):
        d["people"] = {"index": i, "count": len(docs),
                       "state": "observed",
                       "basis": "foreground component"}
    return docs


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


def people_count(doc_or_docs) -> int:
    """How many person documents an analysis produced (1 for `analyze`)."""
    return len(doc_or_docs) if isinstance(doc_or_docs, list) else 1
