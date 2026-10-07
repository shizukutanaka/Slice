import unittest

from tests import synthetic_person

from slice import bitmap, knowledge, pipeline


class TestPipeline(unittest.TestCase):
    def test_analyze_produces_document(self):
        doc = pipeline.analyze(
            bitmap.encode_png(synthetic_person()), source_name="x.png")
        out = pipeline.strip_runtime(doc)
        for key in ("schema", "skeleton", "pose", "style", "ratio",
                    "prediction", "warnings", "analysis"):
            self.assertIn(key, out, key)
        self.assertIsInstance(out["warnings"], list)

    def test_analysis_block_integrates_layers(self):
        doc = pipeline.analyze(
            bitmap.encode_png(synthetic_person()))
        a = doc["analysis"]
        for key in ("angles", "symmetry", "balance", "spine",
                    "gesture", "dynamics", "occlusion", "frame"):
            self.assertIn(key, a, key)
        self.assertIsNotNone(a["frame"])
        self.assertIn("elbow_l_flex", a["angles"])

    def test_analysis_degrades_on_empty_image(self):
        bmp = bitmap.Bitmap.new(60, 60, (255, 255, 255, 255))
        doc = pipeline.analyze(bitmap.encode_png(bmp))
        self.assertEqual(doc["analysis"]["gesture"]["count"], 0)
        self.assertNotIn("frame", doc["analysis"])
        self.assertEqual(
            knowledge.validate(pipeline.strip_runtime(doc)), [])

    def test_warnings_for_sparse_evidence(self):
        # an image with almost no figure should warn
        bmp = bitmap.Bitmap.new(60, 60, (255, 255, 255, 255))
        doc = pipeline.analyze(bitmap.encode_png(bmp))
        self.assertIn("few_observed_joints", doc["warnings"])
        self.assertIn("no_observed_torso", doc["warnings"])

    def test_warnings_when_torso_predicted(self):
        # limbs observed but the kinematic root fabricated — the
        # document must flag that its anchor is unmeasured
        from slice.skeleton import Joint, PREDICTED, Skeleton
        skel = Skeleton(100, 200)
        for n in ("pelvis", "chest", "neck", "head"):
            skel.set(Joint(n, 50, 60, 0.5, PREDICTED, "prior"))
        for i, n in enumerate(("shoulder_l", "elbow_l", "wrist_l",
                               "shoulder_r", "elbow_r", "wrist_r",
                               "hip_l", "knee_l", "ankle_l")):
            skel.set(Joint(n, 30 + i * 5, 80, 0.9))
        self.assertIn("no_observed_torso",
                      pipeline._warnings(skel))

    def test_strip_runtime_drops_internals(self):
        doc = pipeline.analyze(bitmap.encode_png(synthetic_person()))
        self.assertIn("_bitmap", doc)
        out = pipeline.strip_runtime(doc)
        self.assertFalse(any(k.startswith("_") for k in out))

    def test_robust_profile_recorded_and_detects(self):
        raw = bitmap.encode_png(synthetic_person())
        doc = pipeline.analyze(raw, robust=True)
        self.assertEqual(doc["engine"]["profile"], "robust")
        self.assertGreater(
            len(doc["prediction"]["observed"]), 8)
        # default profile stays default
        doc2 = pipeline.analyze(raw)
        self.assertEqual(doc2["engine"]["profile"], "default")


if __name__ == "__main__":
    unittest.main()
