"""Tests for slice.imgqual — input adequacy assessment."""
import unittest

from slice import evaluate, imgqual
from slice.bitmap import Bitmap


class TestImgqual(unittest.TestCase):
    def test_clean_fixture_adequate(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = imgqual.assess(bmp)
        self.assertEqual(r["verdict"], "adequate")
        self.assertTrue(imgqual.adequate(r))
        self.assertEqual(r["failed"], [])

    def test_flat_frame_flagged(self):
        bmp = Bitmap.new(200, 300, (200, 200, 200, 255))
        r = imgqual.assess(bmp)
        self.assertFalse(r["verdict"] == "adequate")
        codes = [f["code"] for f in r["flags"] if not f["ok"]]
        self.assertIn("dynamic", codes)
        self.assertIn("contrast", codes)

    def test_tiny_frame_flagged(self):
        bmp = Bitmap.new(64, 80, (0, 0, 0, 255))
        r = imgqual.assess(bmp)
        self.assertIn("size", r["failed"])

    def test_blurred_flagged(self):
        # smooth gradient → near-zero laplacian, nonzero dynamic range
        bmp = Bitmap.new(200, 300, (0, 0, 0, 255))
        for y in range(300):
            v = int(255 * y / 299)
            for x in range(200):
                bmp.set(x, y, (v, v, v, 255))
        r = imgqual.assess(bmp)
        self.assertIn("blur", r["failed"])

    def test_lone_outlier_cannot_pass_contrast(self):
        # a few bright pixels in a centre that otherwise matches the
        # border must not satisfy the contrast gate — the declared
        # statistic is median-ish, so sparse outliers cannot carry it
        bmp = Bitmap.new(200, 300, (60, 60, 60, 255))
        for y in range(300):
            for x in range(200):
                if (x * 31 + y * 17) % 23 == 0:
                    v = 60 + (x * y) % 40  # mild texture for dynamic
                    bmp.set(x, y, (v, v, v, 255))
        for y in range(75, 225, 12):
            for x in range(50, 150, 12):
                bmp.set(x, y, (255, 255, 255, 255))  # sparse outliers
        r = imgqual.assess(bmp)
        self.assertIn("contrast", r["failed"])

    def test_flag_values_measured(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = imgqual.assess(bmp)
        for f in r["flags"]:
            self.assertIn("value", f)
            self.assertIn("limit", f)
        self.assertEqual(r["state"], "measured")


if __name__ == "__main__":
    unittest.main()
