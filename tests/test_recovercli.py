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


class TestRecoverCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))
        self.addCleanup(lambda: os.path.exists(self.blank)
                        and os.unlink(self.blank))

    def test_primary_rung(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["recover", self.p]), 0)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["method"], "primary")
        self.assertEqual(res["state"], "observed")
        self.assertNotIn("skeleton", res)

    def test_blank_fails_honestly(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["recover", self.blank]), 1)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["state"], "failed")
        self.assertEqual(res["attempts"], 3)


if __name__ == "__main__":
    unittest.main()
