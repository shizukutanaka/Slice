import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

from slice import bitmap
from slice.__main__ import main
from tests import synthetic_person


class TestStatsCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        for i in range(3):
            with open(os.path.join(self.d,
                                   f"f{i}.png"), "wb") as f:
                f.write(bitmap.encode_png(synthetic_person()))

    def test_summary_report(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["stats", self.d]), 0)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["cases"], 3)
        self.assertIn("per_joint", res)
        self.assertIn("weakest_joints", res)
        self.assertIn("head", res["per_joint"])

    def test_empty_dir_fails(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(empty, True))
        self.assertEqual(main(["stats", empty]), 1)


if __name__ == "__main__":
    unittest.main()
