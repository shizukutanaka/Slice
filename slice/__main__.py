"""Slice CLI.

    python -m slice analyze <image> [-o knowledge.json]
        [--model adult|child|deformed] [--robust] [--overlay out.png]
        [--store DIR]
    python -m slice batch <dir> --store DIR [--model M] [-r]
    python -m slice audit <image> [--model M] [--robust] [-o audit.json]
        — run every quality layer over one image and print a verdict
    python -m slice serve [--port 8000] [--store DIR]
    python -m slice list [--store DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import (__version__, bitmap, knowledge, pipeline, render, rest,
               contour, selfcheck)
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
            doc = pipeline.analyze(raw, model=a.model, source_name=p)
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


def _cmd_contour(a) -> int:
    """Silhouette contour trace + shape descriptors."""
    est = (pipeline.ROBUST_ESTIMATOR if a.robust
           else pipeline.ESTIMATOR)
    try:
        with open(a.image, "rb") as f:
            bmp = bitmap.decode(f.read())
    except (bitmap.UnsupportedFormat, OSError) as e:
        print(f"cannot load {a.image}: {e}", file=sys.stderr)
        return 2
    small = bmp.downscale(est.max_dim)
    m = est._mask(small)
    res = contour.features(m)
    if a.output:
        pts = contour.trace(m)
        with open(a.output, "w", encoding="utf-8") as f:
            json.dump({"contour": pts,
                       "frame": [small.width, small.height]},
                      f)
        print(f"wrote {a.output} ({len(pts)} points)",
              file=sys.stderr)
    res["frame"] = [small.width, small.height]
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["area"] else 1


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
    b.set_defaults(fn=_cmd_batch)

    au = sub.add_parser("audit", help="run all quality layers on one image")
    au.add_argument("image")
    au.add_argument("--model", choices=sorted(BODY_MODELS), default=None)
    au.add_argument("--robust", action="store_true",
                    help="robust estimation profile")
    au.add_argument("-o", "--output",
                    help="write the full audit JSON (all layers + doc)")
    au.set_defaults(fn=_cmd_audit)

    ct = sub.add_parser(
        "contour", help="silhouette contour + descriptors")
    ct.add_argument("image")
    ct.add_argument("--robust", action="store_true",
                    help="robust estimation profile")
    ct.add_argument("-o", "--output",
                    help="write the traced contour points JSON")
    ct.set_defaults(fn=_cmd_contour)

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
