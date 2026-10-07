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


class TestSignatureCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.q = _png(synthetic_person(arms_down=False))
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))
        self.addCleanup(lambda: os.path.exists(self.q)
                        and os.unlink(self.q))

    def test_single_signature(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["signature", self.p]), 0)
        sig = json.loads(buf.getvalue())["signature"]
        self.assertGreater(len(sig), 10)

    def test_same_pose_zero_distance(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["signature", self.p, self.p]), 0)
        self.assertEqual(
            json.loads(buf.getvalue())["distance"], 0.0)

    def test_different_pose_nonzero_distance(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["signature", self.p, self.q]), 0)
        self.assertGreater(
            json.loads(buf.getvalue())["distance"], 0.0)


if __name__ == "__main__":
    unittest.main()
