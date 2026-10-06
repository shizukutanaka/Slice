import json
import os
import tempfile
import unittest

from tests import synthetic_person

from slice import bitmap, knowledge, pipeline
from slice.landmarks import JOINTS


def analyze_synth():
    raw = bitmap.encode_png(synthetic_person())
    return pipeline.analyze(raw, source_name="synth.png")


class TestKnowledge(unittest.TestCase):
    def test_schema_valid(self):
        doc = pipeline.strip_runtime(analyze_synth())
        self.assertEqual(knowledge.validate(doc), [])

    def test_observed_predicted_split(self):
        doc = analyze_synth()
        p = doc["prediction"]
        self.assertTrue(p["observed"])
        for n in p["observed"]:
            self.assertEqual(doc["skeleton"]["joints"][n]["state"],
                             "observed")
        for n in p["predicted"]:
            self.assertEqual(doc["skeleton"]["joints"][n]["state"],
                             "predicted")

    def test_coverage_metrics(self):
        doc = analyze_synth()
        cov = doc["coverage"]
        self.assertEqual(cov["joints_total"], len(JOINTS))
        self.assertEqual(
            cov["observed"] + cov["predicted"] + cov["unfilled"],
            len(JOINTS))
        self.assertGreater(cov["observed"], 0)
        self.assertTrue(0 < cov["observed_ratio"] <= 1)
        self.assertTrue(0 < cov["mean_observed_confidence"] <= 1)

    def test_keypoints_flat_layout(self):
        doc = analyze_synth()
        flat = doc["export"]["keypoints_2d"]
        self.assertEqual(len(flat), len(JOINTS) * 3)

    def test_store_roundtrip(self):
        doc = pipeline.strip_runtime(analyze_synth())
        with tempfile.TemporaryDirectory() as d:
            store = knowledge.KnowledgeStore(d)
            kid = store.save(doc)
            self.assertTrue(os.path.isfile(os.path.join(d, kid + ".json")))
            back = store.get(kid)
            self.assertEqual(back["id"], doc["id"])
            self.assertIn(kid, {i["id"] for i in store.list()})
            with self.assertRaises(KeyError):
                store.get("k_ffffffffffff")
            with self.assertRaises(KeyError):
                store.get("../etc/passwd")

    def test_validate_catches_bad(self):
        self.assertTrue(knowledge.validate({"schema": "x"}))
        doc = pipeline.strip_runtime(analyze_synth())
        doc["skeleton"]["joints"]["head"]["confidence"] = 2
        self.assertTrue(knowledge.validate(doc))


if __name__ == "__main__":
    unittest.main()
