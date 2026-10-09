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


class TestMaskCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_mask_png(self):
        out = tempfile.mktemp(suffix=".png")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["mask", self.p, "-o", out]), 0)
        res = json.loads(buf.getvalue())
        self.assertGreater(res["coverage"], 0.1)
        bmp = bitmap.decode(open(out, "rb").read())
        self.assertEqual(
            (bmp.width, bmp.height), (160, 300))

    def test_cutout_zeroes_bg(self):
        out = tempfile.mktemp(suffix=".png")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["mask", self.p, "-o", out,
                      "--cutout"]), 0)
        bmp = bitmap.decode(open(out, "rb").read())
        self.assertEqual(bmp.get(0, 0)[3], 0)


if __name__ == "__main__":
    unittest.main()
