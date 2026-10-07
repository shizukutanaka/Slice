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


class TestSmoothCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        for i in range(3):
            with open(os.path.join(self.d,
                                   f"f{i}.png"), "wb") as f:
                f.write(bitmap.encode_png(synthetic_person()))

    def test_jitter_report_and_smoothed_output(self):
        out = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(out, True))
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["smooth", self.d, "-o", out]), 0)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["frames"], 3)
        self.assertIn("mean_jitter", res)
        docs = [f for f in os.listdir(out)
                if f.endswith(".json")]
        self.assertEqual(len(docs), 3)
        doc = json.load(open(os.path.join(
            out, sorted(docs)[0])))
        self.assertIn("joints", doc)

    def test_empty_dir_fails(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(empty, True))
        self.assertEqual(main(["smooth", empty]), 1)


if __name__ == "__main__":
    unittest.main()
