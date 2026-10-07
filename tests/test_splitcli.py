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


class TestSplitCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_single_figure(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["split", self.p]), 0)
        res = json.loads(buf.getvalue())
        self.assertGreaterEqual(res["figures"], 1)
        self.assertGreater(
            res["results"][0]["observed"], 10)

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        self.assertEqual(main(["split", blank]), 1)


if __name__ == "__main__":
    unittest.main()
