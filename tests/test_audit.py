import copy
import unittest

from slice.audit import audit
from slice.knowledge import build
from slice.pose import HeuristicPoseEstimator
from tests import synthetic_person


def _doc(pose=True):
    skel = HeuristicPoseEstimator().estimate(synthetic_person())
    return build(skel, {"shoulder_hip": 1.0},
                 {"label": "standing"} if pose else None,
                 engine={"name": "heuristic", "version": "1"})


class TestAudit(unittest.TestCase):
    def test_clean_doc_scores_high(self):
        a = audit(_doc())
        self.assertEqual(a["errors"], [])
        self.assertIn(a["verdict"], ("clean", "flagged"))
        self.assertGreater(a["score"], 0.5)

    def test_missing_basis_flagged(self):
        doc = _doc()
        doc["skeleton"]["joints"]["head"]["basis"] = ""
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertIn("no_basis", codes)
        self.assertIn("head", a["warnings"][
            codes.index("no_basis")]["joints"])

    def test_low_evidence_semantics(self):
        doc = _doc()
        for name, j in doc["skeleton"]["joints"].items():
            j["state"] = "predicted"
        doc["prediction"]["observed"] = []
        doc["prediction"]["predicted"] = list(
            doc["skeleton"]["joints"])
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertIn("low_observed", codes)
        self.assertIn("semantics_on_prediction", codes)

    def test_prediction_mismatch(self):
        doc = _doc()
        doc["prediction"]["observed"] = ["nonsense"]
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertIn("prediction_mismatch", codes)

    def test_prediction_predicted_list_checked(self):
        # the predicted list was never cross-checked: a stale doc
        # that drops a predicted joint looked clean
        doc = _doc()
        doc["skeleton"]["joints"]["wrist_l"]["state"] = "predicted"
        doc["prediction"]["predicted"] = []  # stale bookkeeping
        a = audit(doc)
        details = [w["detail"] for w in a["warnings"]
                   if w["code"] == "prediction_mismatch"]
        self.assertIn("prediction.predicted list disagrees with "
                      "joint states", details)

    def test_non_vocab_joint_no_false_mismatch(self):
        # build() fills the lists from all joints, so an observed
        # non-vocabulary joint listed honestly must not flag
        doc = _doc()
        doc["skeleton"]["joints"]["halo"] = {
            "x": 1.0, "y": 2.0, "confidence": 0.5,
            "state": "observed", "basis": "test"}
        doc["prediction"]["observed"].append("halo")
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertNotIn("prediction_mismatch", codes)

    def test_confidence_suspect(self):
        doc = _doc()
        for j in doc["skeleton"]["joints"].values():
            if j["state"] == "observed":
                j["confidence"] = 1.0
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertIn("confidence_suspect", codes)

    def test_stale_warning_flagged(self):
        # a doc claiming thin evidence it does not have is a stale
        # disclosure — the lint must say so
        doc = _doc()
        doc["warnings"] = ["few_observed_joints"]
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertIn("stale_warning", codes)

    def test_backed_warning_not_flagged(self):
        # a warning that matches the joint states is honest, keep it
        doc = _doc()
        for name, j in doc["skeleton"]["joints"].items():
            if not name.startswith(("ankle", "foot")):
                continue
            j["state"] = "predicted"
        doc["warnings"] = ["no_observed_feet"]
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertNotIn("stale_warning", codes)

    def test_unknown_warning_code_ignored(self):
        # codes outside the audited vocabulary are foreign, not stale
        doc = _doc()
        doc["warnings"] = ["some_future_code"]
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertNotIn("stale_warning", codes)

    def test_invalid_schema_verdict(self):
        a = audit({"no": "schema"})
        self.assertEqual(a["verdict"], "invalid")
        self.assertNotEqual(a["errors"], [])


if __name__ == "__main__":
    unittest.main()
