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


class TestModelchkCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_audit_fields(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["modelchk", self.p])
        res = json.loads(buf.getvalue())
        self.assertEqual(
            rc, 0 if res["verdict"] == "consistent" else 1)
        self.assertEqual(res["chosen"], "adult")
        self.assertIn("dimensions", res)
        self.assertIn("total_rel_error", res)
        off = [k for k, d in res["dimensions"].items()
               if d["verdict"] == "off"]
        for k in off:
            self.assertIn("rel_error", res["dimensions"][k])

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        self.assertEqual(main(["modelchk", blank]), 1)


if __name__ == "__main__":
    unittest.main()
