"""`slice consistency` — skeleton plausibility audit."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from slice import bitmap
from slice.__main__ import main
from tests import synthetic_person


def _png(bmp) -> str:
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(bitmap.encode_png(bmp))
    return path


class ConsistencyCliTest(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))

    def test_consistent(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["consistency", self.p])
        res = json.loads(buf.getvalue())
        self.assertEqual(res["verdict"], "consistent")
        self.assertEqual(res["issues"], [])
        self.assertEqual(rc, 0)

    def test_blank_fails(self):
        blank = _png(bitmap.Bitmap.new(
            80, 80, (128, 128, 128, 255)))
        self.addCleanup(lambda: os.path.exists(blank)
                        and os.unlink(blank))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["consistency", blank]), 1)


if __name__ == "__main__":
    unittest.main()
