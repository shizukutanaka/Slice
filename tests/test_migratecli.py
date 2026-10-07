import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

from slice import bitmap, knowledge, pipeline
from slice.__main__ import main
from tests import synthetic_person


class TestMigrateCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        st = knowledge.KnowledgeStore(self.d)
        doc = pipeline.strip_runtime(pipeline.analyze(
            bitmap.encode_png(synthetic_person())))
        self.kid = st.save(doc)
        # an "old" doc dropped in by hand: no schema/coverage blocks
        old = dict(doc)
        old["id"] = "k_deadbeef0002"
        old.pop("coverage", None)
        with open(os.path.join(
                self.d, "k_deadbeef0002.json"), "w") as f:
            json.dump(old, f)

    def _run(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(list(argv))
        return rc, json.loads(buf.getvalue())

    def test_dry_run_reports_without_writing(self):
        rc, res = self._run("migrate", "--store", self.d)
        self.assertEqual(rc, 0)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["docs"], 2)
        self.assertEqual(res["changed"], 1)
        # file unchanged on disk
        raw = json.load(open(os.path.join(
            self.d, "k_deadbeef0002.json")))
        self.assertNotIn("coverage", raw)

    def test_write_repairs_in_place(self):
        rc, res = self._run("migrate", "--store", self.d,
                            "--write")
        self.assertEqual(rc, 0)
        self.assertEqual(res["written"], 1)
        st = knowledge.KnowledgeStore(self.d)
        doc = st.get("k_deadbeef0002")
        self.assertFalse(knowledge.validate(doc))
        raw = json.load(open(os.path.join(
            self.d, "k_deadbeef0002.json")))
        self.assertIn("coverage", raw)


if __name__ == "__main__":
    unittest.main()
