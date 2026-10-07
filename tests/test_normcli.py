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


class TestNormCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_unit_coords(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["norm", self.p, "--unit"]), 0)
        res = json.loads(buf.getvalue())
        for j in res["joints"].values():
            self.assertGreaterEqual(j["x"], 0)
            self.assertLessEqual(j["x"], 1)
        self.assertEqual(res["norm"]["mode"],
                         "unit (0-1 per frame side)")

    def test_resize_scales(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["norm", self.p, "--resize", "320x600"]),
                0)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["norm"]["from"], [160, 300])


if __name__ == "__main__":
    unittest.main()
