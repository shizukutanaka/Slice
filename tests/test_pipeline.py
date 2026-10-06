import unittest

from tests import synthetic_person

from slice import bitmap, pipeline


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
        self.assertIsNone(doc["analysis"]["frame"])

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


if __name__ == "__main__":
    unittest.main()
