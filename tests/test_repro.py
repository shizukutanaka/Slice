"""Tests for slice.repro — deterministic reproducibility check."""
import unittest

from slice import evaluate, knowledge, repro
from slice.bitmap import Bitmap
from slice.pose import HeuristicPoseEstimator


def _doc(bmp, est=None):
    est = est or HeuristicPoseEstimator()
    sk = est.estimate(bmp)
    doc = knowledge.build(sk, {}, source_name="t",
                          engine={"name": "t", "version": "0"})
    return doc, sk


class TestRepro(unittest.TestCase):
    def test_same_pipeline_reproduces(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        r = repro.verify(doc, bmp)
        self.assertEqual(r["verdict"], "reproducible")
        self.assertTrue(repro.reproducible(r))
        self.assertEqual(r["drifts"], [])

    def test_position_drift_detected(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        doc["skeleton"]["joints"]["head"]["x"] += 20
        r = repro.verify(doc, bmp)
        self.assertEqual(r["verdict"], "drifted")
        self.assertIn("head", [d["joint"] for d in r["drifts"]])

    def test_state_flip_detected(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        for j in doc["skeleton"]["joints"].values():
            if j["state"] == "observed":
                j["state"] = "predicted"
                break
        r = repro.verify(doc, bmp)
        self.assertEqual(r["verdict"], "changed")
        self.assertTrue(r["state_flips"])

    def test_missing_joint_detected(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        doc["skeleton"]["joints"]["fake_joint"] = {
            "x": 1, "y": 1, "confidence": 0.5,
            "state": "observed", "basis": "x"}
        r = repro.verify(doc, bmp)
        self.assertIn("fake_joint", r["missing"])
        self.assertEqual(r["verdict"], "changed")

    def test_added_joint_detected(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        del doc["skeleton"]["joints"]["neck"]
        r = repro.verify(doc, bmp)
        self.assertIn("neck", r["added"])

    def test_unrecorded_frame_is_unverifiable(self):
        """A doc with no frame block gives no coordinate space to
        verify positions against — `or 1.0` silently assumed the
        re-estimate's space, computing px distances between unrelated
        frames while basis still claimed "frame-rescaled"."""
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        del doc["skeleton"]["frame"]
        r = repro.verify(doc, bmp)
        self.assertFalse(r["frame_verified"])
        self.assertEqual(r["verdict"], "unverifiable")
        self.assertEqual(r["drifts"], [])
        self.assertNotIn("frame-rescaled", r["basis"])

    def test_unrecorded_frame_still_checks_structure(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        del doc["skeleton"]["frame"]
        del doc["skeleton"]["joints"]["neck"]
        r = repro.verify(doc, bmp)
        self.assertIn("neck", r["added"])
        self.assertEqual(r["verdict"], "changed")

    def test_recorded_frame_still_verified(self):
        bmp, _ = evaluate.draw_case(160, 300)
        doc, _ = _doc(bmp)
        r = repro.verify(doc, bmp)
        self.assertTrue(r["frame_verified"])
        self.assertEqual(r["verdict"], "reproducible")


if __name__ == "__main__":
    unittest.main()
