import unittest

from tests import synthetic_person

from slice import bitmap, selfcheck


class TestSelfCheck(unittest.TestCase):
    def test_synth_person_passes_or_warns(self):
        raw = bitmap.encode_png(synthetic_person())
        r = selfcheck.run(raw)
        self.assertIn(r["verdict"], ("pass", "warn"))
        for layer in ("imgqual", "human", "evid", "limbcov", "fit",
                      "stability", "contrad", "gate"):
            self.assertIn(layer, r["layers"], layer)
            self.assertIn(layer, r["severity"], layer)
        self.assertIn("skeleton", r["doc"])

    def test_blank_image_fails_via_detection(self):
        bmp = bitmap.Bitmap.new(60, 60, (255, 255, 255, 255))
        r = selfcheck.run(bitmap.encode_png(bmp))
        self.assertEqual(r["verdict"], "fail")
        self.assertIn("detection:no_person", r["reasons"])
        # unmeasurable layers do not fake a verdict
        self.assertNotIn("evid", r["layers"])

    def test_robust_profile_runs(self):
        raw = bitmap.encode_png(synthetic_person())
        r = selfcheck.run(raw, robust=True)
        self.assertEqual(r["doc"]["engine"]["profile"], "robust")
        self.assertIn(r["verdict"], ("pass", "warn", "fail"))


if __name__ == "__main__":
    unittest.main()
