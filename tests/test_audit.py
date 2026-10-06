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

    def test_confidence_suspect(self):
        doc = _doc()
        for j in doc["skeleton"]["joints"].values():
            if j["state"] == "observed":
                j["confidence"] = 1.0
        a = audit(doc)
        codes = [w["code"] for w in a["warnings"]]
        self.assertIn("confidence_suspect", codes)

    def test_invalid_schema_verdict(self):
        a = audit({"no": "schema"})
        self.assertEqual(a["verdict"], "invalid")
        self.assertNotEqual(a["errors"], [])


if __name__ == "__main__":
    unittest.main()
