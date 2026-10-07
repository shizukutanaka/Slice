import unittest

from tests import synthetic_person

from slice import bitmap, pipeline


class TestPipeline(unittest.TestCase):
    def test_analyze_produces_document(self):
        doc = pipeline.analyze(
            bitmap.encode_png(synthetic_person()), source_name="x.png")
        out = pipeline.strip_runtime(doc)
        for key in ("schema", "skeleton", "pose", "style", "ratio",
                    "prediction", "warnings"):
            self.assertIn(key, out, key)
        self.assertIsInstance(out["warnings"], list)

    def test_warnings_for_sparse_evidence(self):
        # an image with almost no figure should warn
        bmp = bitmap.Bitmap.new(60, 60, (255, 255, 255, 255))
        doc = pipeline.analyze(bitmap.encode_png(bmp))
        self.assertIn("few_observed_joints", doc["warnings"])

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
