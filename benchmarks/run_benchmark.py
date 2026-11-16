#!/usr/bin/env python3
"""Adoption benchmark suite for Slice.

Where `python -m slice.bench` is a narrow regression gate (two
fixture cases, estimator only), this suite answers the adopter's
questions end to end: for each representative input category, how
often does the full pipeline (PNG bytes -> Knowledge JSON) succeed,
how accurate is the skeleton against known ground truth, and how
long does one image take?

Every fixture is generated procedurally in this file (seeded, no
downloads, no external images), so anyone can reproduce the numbers:

    python3 benchmarks/run_benchmark.py                 # summary
    python3 benchmarks/run_benchmark.py --md out.md     # full report
    python3 benchmarks/run_benchmark.py --json out.json # raw results

Definitions
-----------
* pipeline success: `slice.pipeline.analyze` returns without raising
  and the stripped document passes `slice.knowledge.validate`
  (empty issue list).
* accuracy (categories with ground truth): detection / observed
  rates and mean positional error from `slice.evaluate.evaluate`,
  plus mean OKS from `slice.oks` — the same metrics the regression
  gate uses. Ground truth comes from `slice.evaluate.draw_case`,
  which records the exact joint coordinates it draws.
* negative success: for images with no person, success means the
  pipeline does NOT fabricate an observed skeleton
  (`pipeline.observed_count == 0`). Producing a document full of
  warnings is the honest outcome; inventing joints is failure.
* latency: wall time of one `pipeline.analyze` call on PNG bytes
  (decode included), median of `repeats` runs after one warm-up.
  Fixture generation and PNG encoding are not timed.
* positional error is measured in the estimator's working frame.
  For inputs taller than 512 px the estimator downscales, so
  large-category errors are working-frame pixels, not source pixels.

Categories marked "not measured" in the report are stated as such;
nothing is extrapolated to real photographs — the photo-like
category is synthetic (flat figure repainted with gradient / noise /
shadow backgrounds), a stand-in, not a photo corpus.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from slice import __version__, bitmap, evaluate, knowledge, oks, pipeline
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Joint, OBSERVED, Skeleton

BG = (235, 235, 235, 255)
DEFAULT_REPEATS = 5


# ------------------------------------------------------------------
# fixtures (deterministic; foreground shapes come from
# slice.evaluate.draw_case so ground truth is exact)
# ------------------------------------------------------------------

def _recolor_bg(bmp, fn):
    for y in range(bmp.height):
        for x in range(bmp.width):
            if bmp.get(x, y) == BG:
                bmp.set(x, y, fn(x, y))
    return bmp


def _gradient(bmp, depth=30):
    h = bmp.height

    def wall(x, y):
        v = int(235 - depth * (y / max(1, h - 1)))
        return (v, v, min(255, v + 4), 255)

    return _recolor_bg(bmp, wall)


def _noise(bmp, amp=12, seed=7):
    rng = random.Random(seed)

    def wall(x, y):
        v = max(0, min(255, 235 + rng.randint(-amp, amp)))
        return (v, v, v, 255)

    return _recolor_bg(bmp, wall)


def _shadow(bmp):
    cx, cy = bmp.width // 2, bmp.height - 8
    rx, ry = bmp.width * 0.30, 6.0

    def wall(x, y):
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        if d < 1.0:
            shade = int(235 - 60 * (1.0 - d))
            return (shade, shade, shade, 255)
        return BG

    return _recolor_bg(bmp, wall)


def _occluded(bmp):
    for y in range(int(bmp.height * 0.6), bmp.height):
        for x in range(int(bmp.width * 0.55), bmp.width):
            bmp.set(x, y, BG)
    return bmp


def _blank(width=160, height=300):
    return bitmap.Bitmap.new(width, height, BG), None


def _block(width=160, height=300):
    """A plain rectangle — a non-person foreground shape."""
    bmp = bitmap.Bitmap.new(width, height, BG)
    for y in range(60, 240):
        for x in range(50, 110):
            bmp.set(x, y, (60, 60, 60, 255))
    return bmp, None


def build_cases():
    """Return [{category, name, bitmap, truth|None, model, kind}].

    kind: "accuracy" (ground truth scored), "pipeline" (success and
    latency only), "negative" (success = no fabricated observation).
    """
    cases = []

    def add(category, name, bmp, truth, model="adult", kind="accuracy"):
        cases.append({"category": category, "name": name, "bitmap": bmp,
                      "truth": truth, "model": model, "kind": kind})

    # clean, flat-background figures (illustration-like)
    for pose in ("stand", "t"):
        bmp, truth = evaluate.draw_case(pose=pose)
        add("clean", f"stand-flat-160x300-{pose}", bmp, truth)
    bmp, truth = evaluate.draw_case(width=240, height=320)
    add("clean", "stand-flat-240x320", bmp, truth)

    # photo-like stand-ins: same figure, hostile backgrounds
    for name, fn in (("gradient-wall", _gradient),
                     ("sensor-noise", _noise),
                     ("cast-shadow", _shadow)):
        bmp, truth = evaluate.draw_case()
        add("photo_like", name, fn(bmp), truth)

    # partial body: lower-right quadrant erased
    bmp, truth = evaluate.draw_case()
    add("occluded", "lower-right-erased", _occluded(bmp), None,
        kind="pipeline")

    # body-model variants on the clean figure (the fixture is drawn
    # with adult proportions, so positional accuracy is not scored
    # for non-adult models — success / latency / observed count only)
    for model in ("child", "deformed"):
        bmp, _truth = evaluate.draw_case()
        add("models", f"model-{model}", bmp, None, model=model,
            kind="pipeline")

    # no person present
    bmp, _ = _blank()
    add("negative", "blank-background", bmp, None, kind="negative")
    bmp, _ = _block()
    add("negative", "rectangle-block", bmp, None, kind="negative")

    # latency scaling on clean figures
    for w, h in ((640, 960), (1200, 1800)):
        bmp, truth = evaluate.draw_case(width=w, height=h)
        add("large", f"stand-flat-{w}x{h}", bmp, truth)

    return cases


# ------------------------------------------------------------------
# measurement
# ------------------------------------------------------------------

def _truth_skeleton(truth, w, h):
    return Skeleton(w, h, {n: Joint(n, x, y, 1.0, OBSERVED,
                                    "ground truth fixture")
                           for n, (x, y) in truth.items()})


def measure_case(case, repeats):
    bmp = case["bitmap"]
    raw = bitmap.encode_png(bmp)
    model = case["model"]

    # accuracy at estimator level (same metrics as the gate).
    # The estimator works in a downscaled frame for large inputs
    # (max height 512), so truth is scaled into the skeleton's own
    # frame before scoring — errors are working-frame pixels.
    accuracy = None
    if case["kind"] == "accuracy":
        est = HeuristicPoseEstimator()
        skel = est.estimate(bmp)
        sx = skel.image_width / bmp.width
        sy = skel.image_height / bmp.height
        truth = {n: (x * sx, y * sy)
                 for n, (x, y) in case["truth"].items()}
        m = evaluate.evaluate([(bmp, truth)], est)
        gt = _truth_skeleton(truth, skel.image_width,
                             skel.image_height)
        v = oks.oks(gt, skel)
        accuracy = {
            "detection_rate": m["detection_rate"],
            "observed_rate": m["observed_rate"],
            "mean_error_px": m["mean_error_px"],
            "mean_oks": round(v, 4) if v is not None else None,
        }

    # end-to-end pipeline: success + latency
    error = None
    doc = None
    try:
        pipeline.analyze(raw, model=model, source_name=case["name"])
    except Exception as exc:  # warm-up doubles as the success probe
        error = f"{type(exc).__name__}: {exc}"
    times = []
    if error is None:
        for _ in range(max(1, repeats)):
            t0 = time.perf_counter()
            doc = pipeline.analyze(raw, model=model,
                                    source_name=case["name"])
            times.append((time.perf_counter() - t0) * 1000)

    observed = None
    warnings = None
    valid = None
    if doc is not None:
        observed = pipeline.observed_count(doc)
        warnings = doc.get("warnings", [])
        valid = knowledge.validate(pipeline.strip_runtime(doc)) == []

    if error is not None:
        success = False
    elif case["kind"] == "negative":
        success = observed == 0
    else:
        success = bool(valid)

    return {
        "category": case["category"],
        "name": case["name"],
        "model": model,
        "kind": case["kind"],
        "size": f"{bmp.width}x{bmp.height}",
        "success": success,
        "error": error,
        "observed_joints": observed,
        "warnings": warnings,
        "accuracy": accuracy,
        "ms_median": round(statistics.median(times), 1) if times else None,
        "ms_mean": round(statistics.mean(times), 1) if times else None,
    }


def run(repeats=DEFAULT_REPEATS):
    cases = build_cases()
    results = [measure_case(c, repeats) for c in cases]
    categories = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)
    summary = {}
    for cat, rs in categories.items():
        acc = [r["accuracy"] for r in rs if r["accuracy"]]
        summary[cat] = {
            "cases": len(rs),
            "success_rate": round(
                sum(1 for r in rs if r["success"]) / len(rs), 4),
            "ms_median_of_medians": round(statistics.median(
                [r["ms_median"] for r in rs if r["ms_median"] is not None
                 ]), 1) if any(r["ms_median"] is not None for r in rs)
            else None,
            "detection_rate": round(statistics.mean(
                a["detection_rate"] for a in acc), 4) if acc else None,
            "observed_rate": round(statistics.mean(
                a["observed_rate"] for a in acc), 4) if acc else None,
            "mean_error_px": round(statistics.mean(
                a["mean_error_px"] for a in acc), 2) if acc else None,
            "mean_oks": round(statistics.mean(
                a["mean_oks"] for a in acc if a["mean_oks"] is not None
            ), 4) if any(a["mean_oks"] is not None for a in acc) else None,
        }
    return {
        "slice_version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "repeats": repeats,
        "summary": summary,
        "cases": results,
    }


# ------------------------------------------------------------------
# reporting
# ------------------------------------------------------------------

CATEGORY_LABELS = {
    "clean": "Clean flat-background figures (illustration-like)",
    "photo_like": "Photo-like stand-ins (synthetic: gradient / noise / shadow backgrounds)",
    "occluded": "Partial body (lower-right quadrant erased)",
    "models": "Body-model variants (child / deformed) on the clean figure",
    "negative": "No person in the image",
    "large": "Large clean figures (latency scaling)",
}


def to_markdown(report, generated):
    lines = [
        "# Slice benchmark results",
        "",
        f"Generated: {generated} by `benchmarks/run_benchmark.py` "
        f"(Slice {report['slice_version']}, Python {report['python']}, "
        f"{report['platform']}, repeats={report['repeats']}).",
        "Absolute times are this machine's; ratios and rates are the "
        "portable signal. See the methodology in the script docstring "
        "of `benchmarks/run_benchmark.py`.",
        "",
        "| Category | Cases | Success rate | Median ms/image | "
        "Detection | Observed | Mean error (px) | Mean OKS |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for cat, s in report["summary"].items():
        def fmt(v, suffix=""):
            return "—" if v is None else f"{v}{suffix}"
        lines.append(
            f"| {CATEGORY_LABELS.get(cat, cat)} | {s['cases']} | "
            f"{s['success_rate']:.2f} | {fmt(s['ms_median_of_medians'])} | "
            f"{fmt(s['detection_rate'])} | {fmt(s['observed_rate'])} | "
            f"{fmt(s['mean_error_px'])} | {fmt(s['mean_oks'])} |")
    lines += ["", "## Per-case detail", "",
              "| Case | Model | Size | Success | Observed joints | "
              "Median ms | Mean ms | Error / note |",
              "|---|---|---|---|---|---|---|---|"]
    for r in report["cases"]:
        note = r["error"] or ""
        if r["kind"] == "negative" and r["success"]:
            note = "no skeleton fabricated (warnings issued)"
        elif r["warnings"]:
            note = (note + " " if note else "") + \
                "warnings: " + ", ".join(r["warnings"])
        lines.append(
            f"| {r['name']} | {r['model']} | {r['size']} | "
            f"{'yes' if r['success'] else 'NO'} | "
            f"{r['observed_joints']} | {r['ms_median']} | "
            f"{r['ms_mean']} | {note} |")
    lines += [
        "",
        "## Reading these numbers",
        "",
        "- Positional error is in the estimator's working frame; "
        "inputs taller than 512 px are downscaled first, so the "
        "`large` category's pixel errors are working-frame pixels.",
        "- A plain rectangle is reported as a failure in `negative`: "
        "the silhouette heuristic treats a person-sized blob as a "
        "person and marks joints `observed`. The blank background "
        "behaves honestly (0 observed joints, full warnings). "
        "Adopters must not treat `observed` as proof that a person "
        "was present.",
        "- Ground truth for `models` (child / deformed) is not "
        "scored: the fixture is drawn with adult proportions, so "
        "positional accuracy against it would not measure those "
        "models. Success, latency and observed-joint counts only.",
        "",
        "## Not measured",
        "",
        "- Real photographs: no redistributable photo corpus is "
        "bundled with this repository, so no number here describes "
        "performance on real photos. `photo_like` is a synthetic "
        "stand-in (same flat figure, hostile backgrounds).",
        "- JPEG / WebP input (requires Pillow), the REST server "
        "(`slice serve`) latency, multi-person images, and video.",
        "- Any form of identity: Slice reports anatomical "
        "inference, never who a person is, and this suite measures "
        "nothing identity-related by design.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    ap.add_argument("--md", help="write the full markdown report here")
    ap.add_argument("--json", help="write raw results JSON here")
    args = ap.parse_args(argv)

    report = run(repeats=args.repeats)
    for cat, s in report["summary"].items():
        print(f"{cat}: success={s['success_rate']:.2f} "
              f"median_ms={s['ms_median_of_medians']} "
              f"detection={s['detection_rate']} "
              f"error_px={s['mean_error_px']} oks={s['mean_oks']}")
    if args.json:
        Path(args.json).write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8")
    if args.md:
        generated = datetime.date.today().isoformat()
        Path(args.md).write_text(to_markdown(report, generated),
                                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
