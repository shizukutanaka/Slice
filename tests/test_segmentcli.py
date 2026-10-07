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


class TestSegmentCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_summary_and_label_map(self):
        out = tempfile.mktemp(suffix=".png")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["segment", self.p, "-o", out]), 0)
        res = json.loads(buf.getvalue())
        self.assertGreater(res["total_pixels"], 0)
        self.assertIn("torso", res["parts"])
        bmp = bitmap.decode(open(out, "rb").read())
        self.assertEqual(
            (bmp.width, bmp.height), (160, 300))

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        self.assertEqual(main(["segment", blank]), 1)


if __name__ == "__main__":
    unittest.main()
