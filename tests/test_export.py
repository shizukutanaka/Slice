import json
import tempfile
import unittest

from tests import synthetic_person

from slice import bitmap, export, knowledge, pipeline


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        store = knowledge.KnowledgeStore(cls._tmp.name)
        png = bitmap.encode_png(synthetic_person(240, 420))
        doc = pipeline.strip_runtime(
            pipeline.analyze(png, model="child", source_name="p.png"))
        store.save(doc)
        cls.store = store

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_flatten_fields(self):
        rec = next(iter(export.iter_dataset(self.store)))
        self.assertEqual(rec["labels"]["body_model"], "child")
        self.assertIn("pose", rec["labels"])
        self.assertGreater(rec["counts"]["observed"], 0)
        self.assertTrue(0 < rec["mean_observed_confidence"] <= 1)
        self.assertEqual(len(rec["keypoints_2d"]) % 3, 0)
        self.assertEqual(len(rec["keypoint_order"]),
                         len(rec["keypoints_2d"]) // 3)

    def test_jsonl_roundtrip(self):
        text = export.dump_jsonl(self.store)
        rows = [json.loads(l) for l in text.splitlines() if l]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"]["name"], "p.png")

    def test_empty_store(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(
                export.dump_jsonl(knowledge.KnowledgeStore(d)), "")


if __name__ == "__main__":
    unittest.main()
