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


class TestConsensusCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_runs_panel_and_disputed(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["consensus", self.p]), 0)
        res = json.loads(buf.getvalue())
        self.assertEqual(len(res["runs"]), 5)
        self.assertGreater(res["joints"], 0)
        self.assertIn("disputed", res)
        self.assertIn("state", res)

    def test_writes_skeleton_json(self):
        out = tempfile.mktemp(suffix=".json")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["consensus", self.p, "-o", out]), 0)
        sk = json.load(open(out))
        self.assertIn("joints", sk)
        # confidence is discounted by run fraction -> basis recorded
        self.assertTrue(any(
            "consensus" in j.get("basis", "")
            for j in sk["joints"].values()))

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["consensus", blank]), 1)


if __name__ == "__main__":
    unittest.main()
