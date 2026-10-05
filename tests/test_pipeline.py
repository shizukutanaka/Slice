import unittest

from tests import synthetic_person

from slice import bitmap, pipeline


class TestPipelineModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.png = bitmap.encode_png(synthetic_person(240, 420))

    def test_auto_model_is_estimated(self):
        doc = pipeline.strip_runtime(pipeline.analyze(self.png))
        self.assertEqual(doc["skeleton"]["body_model"]["state"], "estimated")

    def test_forced_model(self):
        doc = pipeline.strip_runtime(
            pipeline.analyze(self.png, model="child"))
        bm = doc["skeleton"]["body_model"]
        self.assertEqual(bm["name"], "child")
        self.assertEqual(bm["state"], "forced")
        self.assertIn("measured_head_ratio", bm)

    def test_unknown_model_rejected(self):
        with self.assertRaises(ValueError):
            pipeline.analyze(self.png, model="giant")


if __name__ == "__main__":
    unittest.main()
