import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from slice import bitmap, knowledge, pipeline
from slice.__main__ import main
from tests import synthetic_person


def _png(bmp):
    p = tempfile.mktemp(suffix=".png")
    with open(p, "wb") as f:
        f.write(bitmap.encode_png(bmp))
    return p


class TestReproCli(unittest.TestCase):
    def setUp(self):
        self.p = _png(synthetic_person())
        self.addCleanup(lambda: os.path.exists(self.p)
                        and os.unlink(self.p))
        raw = open(self.p, "rb").read()
        doc = pipeline.analyze(raw)
        for k in list(doc):
            if k.startswith("_"):
                del doc[k]
        self.d = tempfile.mktemp(suffix=".json")
        with open(self.d, "w") as f:
            json.dump(doc, f)
        self.addCleanup(lambda: os.path.exists(self.d)
                        and os.unlink(self.d))

    def test_reproducible(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["repro", self.d, self.p]), 0)
        res = json.loads(buf.getvalue())
        self.assertEqual(res["verdict"], "reproducible")
        self.assertGreater(res["joints_compared"], 10)

    def test_changed_doc_fails(self):
        doc = json.load(open(self.d))
        doc["skeleton"]["joints"]["head"]["x"] += 50
        alt = tempfile.mktemp(suffix=".json")
        self.addCleanup(lambda: os.path.exists(alt)
                        and os.unlink(alt))
        with open(alt, "w") as f:
            json.dump(doc, f)
        self.assertEqual(main(["repro", alt, self.p]), 1)


if __name__ == "__main__":
    unittest.main()
