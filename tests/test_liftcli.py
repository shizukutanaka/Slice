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


class TestLiftCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_lifted_joints(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["lift", self.p]), 0)
        res = json.loads(buf.getvalue())
        j = res["joints"]
        self.assertGreater(len(j), 10)
        for v in j.values():
            self.assertIn("z", v)
            self.assertIn("basis", v)
        self.assertIn("depth_spread", res)

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        self.assertEqual(main(["lift", blank]), 1)


if __name__ == "__main__":
    unittest.main()
