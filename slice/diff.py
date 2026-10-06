"""Knowledge document diff — what changed between two analyses.

Dataset QA needs to answer "is this second result actually
different?" without eyeballing JSON. `diff` compares two Knowledge
documents field by field: joints added / removed / moved, state
flips (observed -> predicted is a downgrade worth flagging),
confidence drift, body-model and pose-label changes.

A moved joint lists its displacement in pixels; a joint whose
`state` changed lists from -> to so regressions (observed becoming
predicted) are visible, not just motion.
"""

from __future__ import annotations

from typing import Optional

_MOVE_EPS = 0.5     # px below which a joint "didn't move"
_CONF_EPS = 0.01    # confidence delta worth reporting


def diff(a: dict, b: dict) -> dict:
    """Field-level diff of two Knowledge documents."""
    ja = ((a.get("skeleton") or {}).get("joints")) or {}
    jb = ((b.get("skeleton") or {}).get("joints")) or {}
    added = sorted(set(jb) - set(ja))
    removed = sorted(set(ja) - set(jb))
    moved, state_changed, conf_delta = [], [], {}
    for name in sorted(set(ja) & set(jb)):
        x0, y0 = ja[name].get("x", 0), ja[name].get("y", 0)
        x1, y1 = jb[name].get("x", 0), jb[name].get("y", 0)
        dist = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if dist > _MOVE_EPS:
            moved.append({
                "joint": name,
                "dx": round(x1 - x0, 2),
                "dy": round(y1 - y0, 2),
                "dist": round(dist, 2),
            })
        sa, sb = ja[name].get("state"), jb[name].get("state")
        if sa != sb:
            state_changed.append(
                {"joint": name, "from": sa, "to": sb})
        dc = jb[name].get("confidence", 0) - ja[name].get(
            "confidence", 0)
        if abs(dc) > _CONF_EPS:
            conf_delta[name] = round(dc, 3)
    moved.sort(key=lambda m: -m["dist"])

    fa = (a.get("skeleton") or {}).get("frame") or {}
    fb = (b.get("skeleton") or {}).get("frame") or {}
    ma = ((a.get("skeleton") or {}).get("body_model") or {}).get("name")
    mb = ((b.get("skeleton") or {}).get("body_model") or {}).get("name")
    pa = (a.get("pose") or {}).get("label")
    pb = (b.get("pose") or {}).get("label")

    out = {
        "joints": {
            "added": added,
            "removed": removed,
            "moved": moved,
            "state_changed": state_changed,
            "confidence_delta": conf_delta,
        },
        "n_common": len(set(ja) & set(jb)),
        "frame_changed": fa != fb,
        "model_changed": (
            {"from": ma, "to": mb} if ma != mb else None),
        "pose_changed": (
            {"from": pa, "to": pb} if pa != pb else None),
        "identical": _identical(a, b),
    }
    out["summary"] = _summary(out)
    return out


def _identical(a: dict, b: dict) -> bool:
    import json
    aa = {k: v for k, v in a.items() if k not in ("id", "created_at")}
    bb = {k: v for k, v in b.items() if k not in ("id", "created_at")}
    return json.dumps(aa, sort_keys=True) == json.dumps(
        bb, sort_keys=True)


def _summary(d: dict) -> str:
    parts = []
    j = d["joints"]
    if j["moved"]:
        parts.append("%d joints moved (max %.1fpx)" % (
            len(j["moved"]), j["moved"][0]["dist"]))
    if j["added"]:
        parts.append("added: %s" % ",".join(j["added"]))
    if j["removed"]:
        parts.append("removed: %s" % ",".join(j["removed"]))
    if j["state_changed"]:
        down = [s for s in j["state_changed"]
                if s["from"] == "observed"]
        parts.append("%d state flips%s" % (
            len(j["state_changed"]),
            " (%d observed->predicted downgrades)" % len(down)
            if down else ""))
    if d["model_changed"]:
        m = d["model_changed"]
        parts.append("model %s->%s" % (m["from"], m["to"]))
    if d["pose_changed"]:
        p = d["pose_changed"]
        parts.append("pose %s->%s" % (p["from"], p["to"]))
    return "; ".join(parts) if parts else "no differences"
