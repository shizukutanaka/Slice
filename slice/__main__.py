"""Slice CLI.

    python -m slice analyze <image> [-o knowledge.json]
        [--model adult|child|deformed] [--robust] [--overlay out.png]
        [--store DIR]
    python -m slice batch <dir> --store DIR [--model M] [--robust] [-r]
    python -m slice audit <image> [--model M] [--robust] [-o audit.json]
        — run every quality layer over one image and print a verdict
    python -m slice audit --store DIR  — audit the stored documents
          (honesty lint, near-duplicates, joint observed-rate)
    python -m slice calib
        — confidence calibration vs ground-truth fixtures
    python -m slice bias
        — per-joint systematic vs random error on fixtures
    python -m slice serve [--port 8000] [--store DIR]
    python -m slice list [--store DIR]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

from . import (__version__, bitmap, calib, evaluate, knowledge, limbcov, 
               pipeline, render, rest, rig, selfcheck, storechk)
||||||| 8b1d0d7
from . import (__version__, bitmap, calib, evaluate, knowledge, limbcov,
               pipeline, render, rest, selfcheck, storechk)
from . import (__version__, axis, bias, bitmap, calib, contact, dominance,
               evaluate, extjoints, framefit, ground, handpos, horizon,
               knowledge, limbcov, limbs, mass, mirror, pipeline, plumb, reach,
               render, rest, rom, selfcheck, storechk)
from .anatomy import BODY_MODELS


def _cmd_analyze(a) -> int:
    with open(a.image, "rb") as f:
        raw = f.read()
    if a.multi:
        return _cmd_analyze_multi(a, raw)
    try:
        doc = pipeline.analyze(raw, model=a.model, source_name=a.image,
                               robust=a.robust)
    except bitmap.UnsupportedFormat as e:
        print(f"unsupported image: {e}", file=sys.stderr)
        return 2
    out = pipeline.strip_runtime(doc)
    if a.store:
        kid = knowledge.KnowledgeStore(a.store).save(out)
        print(f"saved: {kid}", file=sys.stderr)
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {a.output}", file=sys.stderr)
    else:
        print(text)
    if a.overlay:
        png = render.overlay_png(doc["_bitmap"], doc["_skeleton"])
        with open(a.overlay, "wb") as f:
            f.write(png)
        print(f"wrote {a.overlay}", file=sys.stderr)
    j = doc["skeleton"]["joints"]
    obs = sum(1 for v in j.values() if v["state"] == "observed")
    pred = sum(1 for v in j.values() if v["state"] == "predicted")
    pose_l = (doc.get("pose") or {}).get("label", "?")
    style_l = (doc.get("style") or {}).get("label", "?")
    bm = doc["skeleton"].get("body_model") or {}
    print(f"joints: {obs} observed / {pred} predicted", file=sys.stderr)
    print(f"pose: {pose_l} | style: {style_l} | model: "
          f"{bm.get('label', '?')} ({bm.get('state', '?')})",
          file=sys.stderr)
    warns = out.get("warnings") or []
    if warns:
        print("warnings: " + ", ".join(warns), file=sys.stderr)
    return 0


def _cmd_batch(a) -> int:
    """Analyze every image under a directory into a KnowledgeStore."""
    import os
    store = knowledge.KnowledgeStore(a.store)
    exts = (".png", ".bmp", ".jpg", ".jpeg", ".webp")
    paths = []
    if a.recursive:
        for root, _dirs, files in os.walk(a.dir):
            paths += [os.path.join(root, f) for f in files]
    else:
        paths = [os.path.join(a.dir, f) for f in os.listdir(a.dir)]
    paths = sorted(p for p in paths
                   if p.lower().endswith(exts))
    saved = failed = 0
    for p in paths:
        try:
            with open(p, "rb") as f:
                raw = f.read()
            doc = pipeline.analyze(raw, model=a.model, source_name=p,
                                   robust=a.robust)
            kid = store.save(pipeline.strip_runtime(doc))
            obs = doc["coverage"]["observed"]
            print(f"{p}: {kid} ({obs} observed)")
            saved += 1
        except (bitmap.UnsupportedFormat, OSError, ValueError) as e:
            print(f"{p}: FAILED {e}", file=sys.stderr)
            failed += 1
    print(f"batch: {saved} saved, {failed} failed "
          f"({len(paths)} images)", file=sys.stderr)
    return 0 if saved else 1


def _cmd_analyze_multi(a, raw) -> int:
    try:
        docs = pipeline.analyze_multi(raw, model=a.model,
                                      source_name=a.image,
                                      robust=a.robust)
    except bitmap.UnsupportedFormat as e:
        print(f"unsupported image: {e}", file=sys.stderr)
        return 2
    outs = []
    for d in docs:
        out = pipeline.strip_runtime(d)
        if a.store:
            kid = knowledge.KnowledgeStore(a.store).save(out)
            print(f"saved: {kid}", file=sys.stderr)
        outs.append(out)
    text = json.dumps(outs, ensure_ascii=False, indent=2)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {a.output}", file=sys.stderr)
    else:
        print(text)
    if a.overlay:
        print("multi: --overlay skipped (per-person overlay not written)",
              file=sys.stderr)
    print(f"people: {len(outs)}", file=sys.stderr)
    return 0


def _cmd_audit(a) -> int:
    if a.store:
        return _cmd_audit_store(a)
    if not a.image:
        print("audit: image path or --store DIR required",
              file=sys.stderr)
        return 2
    with open(a.image, "rb") as f:
        raw = f.read()
    try:
        res = selfcheck.run(raw, model=a.model, source_name=a.image,
                            robust=a.robust)
    except bitmap.UnsupportedFormat as e:
        print(f"unsupported image: {e}", file=sys.stderr)
        return 2
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"wrote {a.output}", file=sys.stderr)
    else:
        print(json.dumps({k: res[k] for k in
                          ("verdict", "severity", "reasons")},
                         ensure_ascii=False, indent=2))
    print(f"verdict: {res['verdict']} "
          f"({res['n_reasons']} reasons)", file=sys.stderr)
    return 0 if res["verdict"] != "fail" else 1


def _cmd_rig(a) -> int:
    """Animation rig: bone hierarchy, lengths, directions."""
    est = (pipeline.ROBUST_ESTIMATOR if a.robust
           else pipeline.ESTIMATOR)
    try:
        with open(a.image, "rb") as f:
            bmp = bitmap.decode(f.read())
    except (bitmap.UnsupportedFormat, OSError) as e:
        print(f"cannot load {a.image}: {e}", file=sys.stderr)
        return 2
    skel = est.estimate(bmp, a.model or "adult")
    if not skel.joints:
        print("no person detected", file=sys.stderr)
        return 1
    bones = rig.build(skel)
    res = {"bones": bones,
           "hierarchy": rig.hierarchy(bones),
           "total_bone_length": rig.total_bone_length(bones),
           "frame": {"width": skel.image_width,
                     "height": skel.image_height},
           "basis": "bone endpoints observed/predicted as given; "
                    "no lengths inferred"}
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"wrote {a.output}", file=sys.stderr)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


||||||| 8b1d0d7
def _probe_dispatch(layer, skel, mask):
    """layer name -> result dict, or None on unknown layer."""
    if layer == "axis":
        return {"principal": axis.principal(skel),
                "tilt": axis.tilt(skel)}
    if layer == "plumb":
        return {"line": plumb.line(skel),
                "forward_head": plumb.forward_head(skel),
                "assess": plumb.assess(skel)}
    if layer == "limbs":
        return limbs.profile(skel)
    if layer == "rom":
        return {"check": rom.check(skel),
                "violations": rom.violations(skel)}
    if layer == "contact":
        return contact.summary(skel)
    if layer == "dominance":
        return {"assess": dominance.assess(skel),
                "cues": dominance.cues(skel)}
    if layer == "handpos":
        return {"summary": handpos.summary(skel),
                "positions": handpos.positions(skel)}
    if layer == "framefit":
        return framefit.assess(skel)
    if layer == "ground":
        return {"estimate": ground.estimate(
                    skel, skel.image_height),
                "clearance": ground.clearance(skel)}
    if layer == "reach":
        return reach.workspace(skel)
    if layer == "horizon":
        return horizon.estimate(skel)
    if layer == "mass":
        area = sum(r.count(True) for r in mask)
        return {"estimate": mass.estimate(skel, area),
                "bmi": mass.bmi(skel, area),
                "area_px": area}
    if layer == "extjoints":
        derived = extjoints.derive(skel)
        return {"joints": {n: {"x": j.x, "y": j.y,
                               "confidence": j.confidence,
                               "state": j.state,
                               "basis": j.basis}
                           for n, j in derived.items()},
                "vocabulary": extjoints.vocabulary()}
    return None
_PROBE_LAYERS = ("axis", "plumb", "limbs", "rom", "contact",
                 "dominance", "handpos", "framefit", "ground",
                 "reach", "horizon", "mass", "extjoints")
def _cmd_probe(a) -> int:
    """Run one semantic layer directly on an image."""
    small = bmp.downscale(est.max_dim)
    mask = est._mask(small)
    res = _probe_dispatch(a.layer, skel, mask)
    if res is None:
        print(f"unknown layer: {a.layer}", file=sys.stderr)
    print(json.dumps({"layer": a.layer, "result": res},
                     ensure_ascii=False, indent=2))
def _cmd_mirror(a) -> int:
    """Estimator left/right consistency: est(flip(img)) vs flip(est(img))."""
    skel_a = est.estimate(bmp, a.model or "adult")
    if not skel_a.joints:
    expected = mirror.flip_skeleton(skel_a)
    actual = est.estimate(mirror.flip_bitmap(bmp),
                          a.model or "adult")
    drift = {}
    for name, je in expected.joints.items():
        ja = actual.joints.get(name)
        if ja is None:
            drift[name] = None
            continue
        drift[name] = round(math.hypot(
            ja.x - je.x, ja.y - je.y), 2)
    vals = [v for v in drift.values() if v is not None]
    res = {
        "joints_compared": len(vals),
        "missing_in_flipped": [n for n, v in drift.items()
                               if v is None],
        "mean_drift_px": round(
            sum(vals) / len(vals), 2) if vals else 0.0,
        "max_drift": ({"joint": max(drift, key=lambda n:
                                   drift[n] or -1),
                       "px": max(vals)} if vals else None),
        "per_joint": drift,
        "verdict": ("symmetric"
                    if vals and max(vals) <= a.tolerance
                    else "drifted"),
        "tolerance_px": a.tolerance,
        "state": "derived",
        "basis": "est(flip(image)) vs flip(est(image)); "
                 "nonzero drift = estimator left/right bias",
    }
    return 0 if res["verdict"] == "symmetric" else 1
def _cmd_audit_store(a) -> int:
    res = storechk.audit_store(a.store)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"wrote {a.output}", file=sys.stderr)
    else:
        out = {k: res[k] for k in ("verdict", "n_docs", "blind_joints",
                                   "reasons")}
        out["reasons"] = out["reasons"][:10]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"store: {res['n_docs']} docs, verdict={res['verdict']} "
          f"({res['n_reasons']} reasons)", file=sys.stderr)
    return 0 if res["verdict"] != "fail" else 1


def _cmd_limbcov(a) -> int:
    """Bone-level silhouette coverage: bones crossing background."""
    est = (pipeline.ROBUST_ESTIMATOR if a.robust
           else pipeline.ESTIMATOR)
    try:
        with open(a.image, "rb") as f:
            bmp = bitmap.decode(f.read())
    except (bitmap.UnsupportedFormat, OSError) as e:
        print(f"cannot load {a.image}: {e}", file=sys.stderr)
        return 2
    skel = est.estimate(bmp, a.model or "adult")
    if not skel.joints:
        print("no person detected", file=sys.stderr)
        return 1
    small = bmp.downscale(est.max_dim)
    m = est._mask(small)
    res = limbcov.check(skel, m)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if res["verdict"] == "insufficient":
        return 1
    return 0 if res["verdict"] == "covered" else 1


def _cmd_calib(a) -> int:
    """Confidence calibration: measured hit rate per reported bin."""
    pairs = [evaluate.draw_case(),
             evaluate.draw_case(width=240, height=320)]
    rep = calib.report(pairs)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    # overconfidence is the dangerous direction: reporting 0.9 when the
    # empirical hit rate is 0.5. Underconfidence is merely conservative.
    # An all-empty table measured nothing — fail rather than pass mute.
    measured = any(b["n"] for b in rep["bins"])
    return 1 if rep["overconfident_bins"] or not measured else 0


def _cmd_bias(a) -> int:
    """Per-joint systematic-error profile over ground-truth fixtures."""
    est = pipeline.ESTIMATOR
    pairs = []
    for bmp, truth in (evaluate.draw_case(),
                       evaluate.draw_case(width=240, height=320)):
        pairs.append((est.estimate(bmp).joints, truth))
    rep = bias.profile(pairs)
    measured = bool(rep.get("joints"))
    rep["state"] = "estimated" if measured else "unmeasured"
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    # unmeasured must not pass; a worst joint beyond the bench gate is
    # a real estimator defect
    worst = rep.get("worst_joint") or {}
    if not measured or (worst.get("mean_error_px") or 0) > 10.0:
        return 1
    return 0


def _cmd_serve(a) -> int:
    rest.serve(port=a.port, store_dir=a.store, token=a.token)
    return 0


def _cmd_list(a) -> int:
    for item in knowledge.KnowledgeStore(a.store).list():
        print(item["id"], item["created_at"], item.get("body_model"))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="slice", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="analyze one image")
    a.add_argument("image")
    a.add_argument("-o", "--output")
    a.add_argument("--model", choices=sorted(BODY_MODELS), default=None,
                   help="body model to force (default: estimator's own pick)")
    a.add_argument("--robust", action="store_true",
                   help="robust profile: adaptive threshold, shadow "
                        "rejection, mask cleanup (for real photos)")
    a.add_argument("--overlay")
    a.add_argument("--store")
    a.add_argument("--multi", action="store_true",
                   help="detect every foreground person (JSON array out)")
    a.set_defaults(fn=_cmd_analyze)

    b = sub.add_parser("batch", help="analyze a directory of images")
    b.add_argument("dir")
    b.add_argument("--store", required=True,
                   help="KnowledgeStore directory to write into")
    b.add_argument("--model", choices=sorted(BODY_MODELS), default=None)
    b.add_argument("-r", "--recursive", action="store_true")
    b.add_argument("--robust", action="store_true",
                   help="robust estimation profile")
    b.set_defaults(fn=_cmd_batch)

    au = sub.add_parser("audit", help="run all quality layers on one image")
    au.add_argument("image", nargs="?",
                    help="image file (a store dir needs --store)")
    au.add_argument("--store",
                    help="audit a KnowledgeStore directory instead "
                         "of an image")
    au.add_argument("--model", choices=sorted(BODY_MODELS), default=None)
    au.add_argument("--robust", action="store_true",
                    help="robust estimation profile")
    au.add_argument("-o", "--output",
                    help="write the full audit JSON (all layers + doc)")
    au.set_defaults(fn=_cmd_audit)

    rg = sub.add_parser(
        "rig", help="animation rig export (bones + hierarchy)")
    rg.add_argument("image")
    rg.add_argument("--model", choices=sorted(BODY_MODELS),
                    default=None)
    rg.add_argument("--robust", action="store_true",
                    help="robust estimation profile")
    rg.add_argument("-o", "--output",
                    help="write the rig JSON here")
    rg.set_defaults(fn=_cmd_rig)

||||||| 8b1d0d7
    pr = sub.add_parser(
        "probe", help="run one semantic layer on an image")
    pr.add_argument("layer", choices=sorted(_PROBE_LAYERS))
    pr.add_argument("image")
    pr.add_argument("--model", choices=sorted(BODY_MODELS),
    pr.add_argument("--robust", action="store_true",
    pr.set_defaults(fn=_cmd_probe)
    mi = sub.add_parser(
        "mirror",
        help="estimator left/right consistency audit")
    mi.add_argument("image")
    mi.add_argument("--model", choices=sorted(BODY_MODELS),
    mi.add_argument("--robust", action="store_true",
    mi.add_argument("--tolerance", type=float, default=4.0,
                    help="max per-joint drift px for 'symmetric'")
    mi.set_defaults(fn=_cmd_mirror)
    lc = sub.add_parser(
        "limbcov", help="bone coverage vs silhouette")
    lc.add_argument("image")
    lc.add_argument("--model", choices=sorted(BODY_MODELS),
                    default=None)
    lc.add_argument("--robust", action="store_true",
                    help="robust estimation profile")
    lc.set_defaults(fn=_cmd_limbcov)

    cb = sub.add_parser(
        "calib", help="confidence calibration vs ground truth")
    cb.set_defaults(fn=_cmd_calib)

    bi = sub.add_parser(
        "bias", help="per-joint systematic vs random error profile")
    bi.set_defaults(fn=_cmd_bias)

    s = sub.add_parser("serve", help="run the REST viewer server")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--store", default="knowledge")
    s.add_argument("--token", default=None,
                   help="require 'Authorization: Bearer TOKEN' on API "
                        "routes (default: SLICE_TOKEN env, else open)")
    s.set_defaults(fn=_cmd_serve)

    l = sub.add_parser("list", help="list stored knowledge")
    l.add_argument("--store", default="knowledge")
    l.set_defaults(fn=_cmd_list)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
