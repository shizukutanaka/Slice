import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from slice import bitmap
from slice.__main__ import main
from tests import synthetic_person


def _png(bmp):
    p = tempfile.mktemp(suffix=".png")
    with open(p, "wb") as f:
        f.write(bitmap.encode_png(bmp))
    return p


class TestRetargetCli(unittest.TestCase):
    def setUp(self):
        self.src = _png(synthetic_person())
        self.dst = _png(synthetic_person(320, 600))
        self.addCleanup(lambda: os.path.exists(self.src)
                        and os.unlink(self.src))
        self.addCleanup(lambda: os.path.exists(self.dst)
                        and os.unlink(self.dst))

    def test_retargeted_skeleton_all_predicted(self):
        out = tempfile.mktemp(suffix=".json")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["retarget", self.src, self.dst,
                      "-o", out]), 0)
        doc = json.load(open(out))
        self.assertGreater(len(doc["joints"]), 10)
        self.assertTrue(all(
            j["state"] == "predicted"
            for j in doc["joints"].values()))

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        self.assertEqual(
            main(["retarget", blank, self.dst]), 1)


if __name__ == "__main__":
    unittest.main()
