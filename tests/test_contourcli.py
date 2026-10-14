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


class TestContourCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_descriptors(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["contour", self.p]), 0)
        res = json.loads(buf.getvalue())
        for k in ("area", "perimeter", "bbox",
                  "aspect", "compactness", "centroid"):
            self.assertIn(k, res)
        self.assertGreater(res["perimeter"], 0)

    def test_trace_output(self):
        out = tempfile.mktemp(suffix=".json")
        self.addCleanup(lambda: os.path.exists(out)
                        and os.unlink(out))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["contour", self.p, "-o", out]), 0)
        doc = json.load(open(out))
        self.assertGreater(len(doc["contour"]), 100)


if __name__ == "__main__":
    unittest.main()
