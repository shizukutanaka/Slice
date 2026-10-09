import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from slice import bitmap
from slice.__main__ import main
from tests import synthetic_person


def _dir(names_bmps):
    d = tempfile.mkdtemp()
    for name, bmp in names_bmps:
        with open(os.path.join(d, name), "wb") as f:
            f.write(bitmap.encode_png(bmp))
    return d


class TestGaitCli(unittest.TestCase):
    def test_per_frame_phases(self):
        d = _dir([("f0.png", synthetic_person()),
                  ("f1.png", synthetic_person())])
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["gait", d]), 0)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["analyzed"], 2)
        self.assertIn("legs", res["frames"][0])

    def test_empty_dir_fails(self):
        self.assertEqual(main(["gait", tempfile.mkdtemp()]), 2)


if __name__ == "__main__":
    unittest.main()
