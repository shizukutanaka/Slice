import json
import os
import shutil
import tempfile
import unittest

from slice import bitmap, knowledge, pipeline
from slice.__main__ import main
from tests import synthetic_person


class TestBundleCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        self.store = knowledge.KnowledgeStore(self.d)
        doc = pipeline.strip_runtime(pipeline.analyze(
            bitmap.encode_png(synthetic_person())))
        self.kid = self.store.save(doc)

    def test_pack_unpack_roundtrip(self):
        zp = os.path.join(self.d, "out.zip")
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["bundle", "pack", zp, self.d]), 0)
        target = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(target, True))
        self.assertEqual(
            main(["bundle", "unpack", zp, target]), 0)
        st = knowledge.KnowledgeStore(target)
        ids = [i["id"] for i in st.list()]
        self.assertIn(self.kid, ids)

    def test_manifest_reads_bundle(self):
        zp = os.path.join(self.d, "out.zip")
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            main(["bundle", "pack", zp, self.d])
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["bundle", "manifest", zp]), 0)
        man = json.loads(buf.getvalue())
        self.assertEqual(man["count"], 1)


if __name__ == "__main__":
    unittest.main()
