import json
import os
import shutil
import tempfile
import unittest

from slice import bitmap, motion, pipeline
from slice.__main__ import main
from tests import synthetic_person


def _png(bmp):
    p = tempfile.mktemp(suffix=".png")
    with open(p, "wb") as f:
        f.write(bitmap.encode_png(bmp))
    return p


class TestMotionCli(unittest.TestCase):
    def setUp(self):
        self.pa = _png(synthetic_person())
        self.pb = _png(synthetic_person(width=200, height=380))
        self.addCleanup(lambda: os.path.exists(self.pa)
                        and os.unlink(self.pa))
        self.addCleanup(lambda: os.path.exists(self.pb)
                        and os.unlink(self.pb))

    def test_same_frame_zero_motion(self):
        out = tempfile.mktemp(suffix=".json")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        self.assertEqual(
            main(["motion", self.pa, self.pa, "-o", out]), 0)
        res = json.load(open(out))
        self.assertEqual(res["mean_speed"], 0.0)
        self.assertGreater(res["joints"], 0)
        self.assertIn("head", res["vectors"])

    def test_no_person_reports_failure(self):
        from slice import bitmap as _bmp
        blank = _bmp.Bitmap.new(80, 80, (128, 128, 128, 255))
        p = _png(blank)
        self.addCleanup(lambda: os.path.exists(p) and os.unlink(p))
        self.assertEqual(main(["motion", p, self.pa]), 1)


if __name__ == "__main__":
    unittest.main()
