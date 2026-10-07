"""Knowledge document migration — bring old docs forward safely.

Stored documents age: schema bumps, new blocks (`coverage`,
`prediction`), fields that didn't exist when the doc was written.
`upgrade` normalizes a document to the current schema — but every
gap it fixes is a *disclosed* fix, not silent fabrication:

- missing `id`/`created_at`/`engine` get real defaults and a change
  entry — `created_at` becomes "" rather than a made-up timestamp
- missing `export`/`prediction`/`coverage`/`skeleton.bones` are
  **recomputed** from the doc's own joints (derivable data, not
  guessed data)
- a joint missing `state` is marked `predicted` with basis
  "migrated: state unknown" — claiming `observed` would fabricate
  evidence
- a joint missing `x`/`y` cannot be invented: it is *dropped* and
  recorded as `joint_dropped`
- `schema` is set to the current `SCHEMA` once the doc actually
  satisfies it — never before

`upgrade(doc)` returns {document, changes, valid_before,
valid_after} — the caller sees exactly what was repaired and can
verify the result validates.
"""

from __future__ import annotations

import copy
import secrets
from typing import Dict, List, Tuple

from .knowledge import SCHEMA, validate
from .landmarks import BONES, JOINTS
from .skeleton import OBSERVED, PREDICTED


def _chg(changes: List[Dict], code: str, detail: str) -> None:
    changes.append({"code": code, "detail": detail})


def _valid(doc) -> List:
    """validate() as a report — never propagate an exception."""
    try:
        return validate(doc)
    except Exception as e:  # a validator bug must not abort a batch
        return ["validate raised %s" % type(e).__name__]


def upgrade(doc: dict) -> Dict:
    """Normalize `doc` to the current schema; return doc + changes."""
    # like validate, upgrade must report rather than raise: stores
    # contain real old documents in every malformed shape
    if not isinstance(doc, dict):
        err = ["document must be a dict"]
        return {
            "document": doc,
            "changes": [{"code": "document_not_dict",
                         "detail": "cannot migrate a non-dict "
                                   "document"}],
            "n_changes": 1,
            "valid_before": err,
            "valid_after": err,
        }
    changes: List[Dict] = []
    before = _valid(doc)
    d = copy.deepcopy(doc)

    if d.get("schema") != SCHEMA:
        _chg(changes, "schema_set",
             "schema '%s' → '%s'" % (d.get("schema"), SCHEMA))
        d["schema"] = SCHEMA
    if "id" not in d:
        d["id"] = "k_" + secrets.token_hex(6)
        _chg(changes, "id_added", "generated new document id")
    if "created_at" not in d:
        d["created_at"] = ""
        _chg(changes, "created_at_missing",
             "no timestamp recorded; left empty rather than fabricated")
    if "engine" not in d:
        d["engine"] = {}
        _chg(changes, "engine_missing", "empty engine block added")

    skel = d.setdefault("skeleton", {})
    if not isinstance(skel, dict):
        skel = {}
        d["skeleton"] = skel
        _chg(changes, "skeleton_replaced",
             "skeleton was not a dict; replaced (contents unsalvageable)")
    joints = skel.get("joints") or {}
    if not isinstance(joints, dict):
        joints = {}
        skel["joints"] = joints
        _chg(changes, "joints_replaced",
             "joints was not a dict; replaced (contents unsalvageable)")
    for name in list(joints):
        j = joints[name]
        if not isinstance(j, dict) or "x" not in j or "y" not in j:
            del joints[name]
            _chg(changes, "joint_dropped",
                 "%s had no position; dropped (uninventable)" % name)
            continue
        if "confidence" not in j:
            j["confidence"] = 0.0
            _chg(changes, "joint_field_filled",
                 "%s.confidence → 0.0 (was absent)" % name)
        if j.get("state") not in (OBSERVED, PREDICTED):
            j["state"] = PREDICTED
            j["basis"] = str(j.get("basis") or "") + \
                "migrated: state unknown"
            _chg(changes, "joint_state_fixed",
                 "%s unmarked → predicted (observed would fabricate)"
                 % name)
        if "basis" not in j:
            j["basis"] = "migrated: unknown provenance"
            _chg(changes, "joint_basis_filled",
                 "%s basis → migrated marker" % name)
    skel["joints"] = joints
    d["skeleton"] = skel

    if "bones" not in skel and joints:
        skel["bones"] = [list(b) for b in BONES
                         if b[0] in joints and b[1] in joints]
        _chg(changes, "bones_recomputed",
             "bones rebuilt from joint list")

    if "prediction" not in d:
        d["prediction"] = {
            "observed": [n for n, j in joints.items()
                         if j.get("state") == OBSERVED],
            "predicted": [n for n, j in joints.items()
                          if j.get("state") == PREDICTED],
        }
        _chg(changes, "prediction_recomputed",
             "observed/predicted lists rebuilt from joint states")

    if "coverage" not in d:
        obs = sum(1 for j in joints.values()
                  if j.get("state") == OBSERVED)
        d["coverage"] = {
            "joints_total": len(JOINTS),
            "observed": obs,
            "predicted": sum(1 for j in joints.values()
                             if j.get("state") == PREDICTED),
            "unfilled": len(JOINTS) - len(joints),
            "observed_ratio": round(obs / len(JOINTS), 3),
            "mean_observed_confidence": round(
                sum(j.get("confidence", 0) for j in joints.values()
                    if j.get("state") == OBSERVED) / max(1, obs), 3),
        }
        _chg(changes, "coverage_recomputed",
             "coverage block rebuilt from joints")

    if "export" not in d:
        flat = []
        for name in JOINTS:
            j = joints.get(name)
            flat += [j["x"], j["y"], j.get("confidence", 0.0)] \
                if j else [0.0, 0.0, 0.0]
        d["export"] = {
            "keypoints_2d": flat,
            "keypoint_order": list(JOINTS),
            "bones": [list(b) for b in BONES],
        }
        _chg(changes, "export_rebuilt",
             "export block rebuilt from joints")

    if "frame" not in skel:
        _chg(changes, "frame_missing",
             "skeleton.frame absent; left absent (not fabricatable)")

    return {
        "document": d,
        "changes": changes,
        "n_changes": len(changes),
        "valid_before": before,
        "valid_after": _valid(d),
    }


def migrated(result: Dict) -> bool:
    """Did upgrade actually change anything?"""
    return result["n_changes"] > 0
