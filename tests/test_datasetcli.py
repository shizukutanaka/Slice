import json
import os
import shutil
import tempfile
import unittest

from slice import bitmap, knowledge, pipeline
from slice.__main__ import main
from tests import synthetic_person


class TestDatasetCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        st = knowledge.KnowledgeStore(self.d)
        doc = pipeline.strip_runtime(pipeline.analyze(
            bitmap.encode_png(synthetic_person())))
        self.kid = st.save(doc)

    def test_csv_export(self):
        out = os.path.join(self.d, "d.csv")
        self.assertEqual(
            main(["dataset", "--store", self.d, "-o", out]), 0)
        lines = open(out).read().strip().split("\n")
        self.assertIn("id,", lines[0])
        self.assertIn(self.kid, lines[1])

    def test_jsonl_export(self):
        out = os.path.join(self.d, "d.jsonl")
        self.assertEqual(
            main(["dataset", "--store", self.d,
                  "--format", "jsonl", "-o", out]), 0)
        doc = json.loads(open(out).readline())
        self.assertEqual(doc["id"], self.kid)

    def test_joint_rows(self):
        out = os.path.join(self.d, "j.csv")
        self.assertEqual(
            main(["dataset", "--store", self.d,
                  "--format", "csv-joints", "-o", out]), 0)
        text = open(out).read()
        self.assertIn("joint,", text.splitlines()[0])
        self.assertIn("head", text)


if __name__ == "__main__":
    unittest.main()
