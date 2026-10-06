"""Unified severity for every audit layer's verdict vocabulary.

Each audit layer answers in its own dialect — `adequate`, `stable`,
`covered`, `consistent`, `reproducible`, `sane`, `compliant`... A
consumer that wants "is this analysis OK?" shouldn't need to know
each dialect. `verdict` maps every known verdict string onto four
severity levels:

- `ok`         — measured and fine
- `advisory`   — measured, worth noting, not disqualifying
- `problem`    — measured and wrong
- `unmeasured` — the layer could not or did not judge (never counts
                 against the subject — refusing to judge is honest)

`grade({name: layer_result})` aggregates a dict of layer outputs
(each carrying a `verdict` or a `state`) into {layers, overall,
worst, unmapped} — `unmapped` lists vocab this table has never seen
so new layers surface the need to extend it, rather than silently
grading unknowns.
"""

from __future__ import annotations

from typing import Dict, Optional

LEVELS = ("unmeasured", "ok", "advisory", "problem")

_OK = {
    "pass", "adequate", "stable", "covered", "consistent", "sane",
    "reproducible", "compliant", "good", "unbiased", "measurable",
    "kept", "supported",
}
_ADVISORY = {
    "warn", "marginal", "sensitive", "hypermobile", "drifted",
    "systematic", "suspicious", "borderline",
}
_PROBLEM = {
    "fail", "inadequate", "unstable", "gaps", "broken", "mismatch",
    "contradicted", "overextended", "implausible", "changed",
    "unsupported", "off",
}
_UNMEASURED = {
    "unmeasurable", "insufficient", "single_run", "unknown",
    "unaudited", "heuristic", "skipped",
}

_VOCAB = ({v: "ok" for v in _OK}
          | {v: "advisory" for v in _ADVISORY}
          | {v: "problem" for v in _PROBLEM}
          | {v: "unmeasured" for v in _UNMEASURED})


def severity_of(verdict: Optional[str]) -> str:
    """Map a layer verdict word to a severity level."""
    if not verdict:
        return "unmeasured"
    return _VOCAB.get(verdict, "unmeasured")


def _verdict_of(result: dict) -> Optional[str]:
    return result.get("verdict") or result.get("state")


def grade(layers: Dict[str, dict]) -> dict:
    """Aggregate named layer results into a unified grade."""
    graded: Dict[str, dict] = {}
    unmapped = []
    measured_levels = []
    for name, result in layers.items():
        word = _verdict_of(result or {})
        sev = severity_of(word)
        mapped = bool(word and word in _VOCAB)
        if word and not mapped:
            unmapped.append("%s: %s" % (name, word))
        graded[name] = {"verdict": word, "severity": sev}
        if sev != "unmeasured":
            measured_levels.append(sev)
    if not measured_levels:
        overall = "unmeasured"
    elif "problem" in measured_levels:
        overall = "problem"
    elif "advisory" in measured_levels:
        overall = "advisory"
    else:
        overall = "ok"
    worst = [n for n, g in graded.items() if g["severity"] == overall]
    return {
        "layers": graded,
        "overall": overall,
        "worst": worst,
        "n_layers": len(graded),
        "unmapped": unmapped,
    }


def acceptable(result: dict, minimum: str = "advisory") -> bool:
    """Is the overall grade at least `minimum`?

    ok > advisory > problem; unmeasured passes at any minimum —
    no evidence isn't evidence of failure.
    """
    overall = result["overall"]
    if overall == "unmeasured":
        return True
    rank = {"ok": 0, "advisory": 1, "problem": 2}
    return rank[overall] <= rank[minimum]
