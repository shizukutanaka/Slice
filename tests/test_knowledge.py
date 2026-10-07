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

    def test_validate_catches_export_flat_mismatch(self):
        doc = pipeline.strip_runtime(analyze_synth())
        doc["export"]["keypoints_2d"] = doc["export"]["keypoints_2d"][:6]
        errors = knowledge.validate(doc)
        self.assertTrue(any("keypoints_2d" in e for e in errors))

    def test_validate_catches_export_state_contradiction(self):
        doc = pipeline.strip_runtime(analyze_synth())
        ex = doc["export"]
        # hand-write the flat-export state field (added after this
        # schema version) — the validator must still cross-check it
        sk = doc["skeleton"]["joints"]
        ex["keypoints_state"] = [
            "predicted" if sk.get(n, {}).get("state") == "observed"
            else "observed" for n in JOINTS]
        errors = knowledge.validate(doc)
        self.assertTrue(any("export state" in e for e in errors))

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

    def test_store_list_uses_index_and_heals(self):
        doc = pipeline.strip_runtime(analyze_synth())
        with tempfile.TemporaryDirectory() as d:
            store = knowledge.KnowledgeStore(d)
            kid = store.save(doc)
            idx = os.path.join(d, knowledge.INDEX_NAME)
            self.assertTrue(os.path.isfile(idx))
            with open(idx) as f:
                entries = json.load(f)["entries"]
            self.assertIn(kid, entries)
            # index itself is never reported as a document
            self.assertNotIn(knowledge.INDEX_NAME[:-5],
                             {i["id"] for i in store.list()})
            # deleting the index -> list() rescans and rebuilds it
            os.remove(idx)
            self.assertIn(kid, {i["id"] for i in store.list()})
            self.assertTrue(os.path.isfile(idx))
            # stale index entry for a deleted doc is pruned
            os.remove(os.path.join(d, kid + ".json"))
            self.assertNotIn(kid, {i["id"] for i in store.list()})

    def test_schema_v11_analysis_slot(self):
        doc = analyze_synth()
        self.assertEqual(doc["schema"], "slice.knowledge/v1")
        # analysis upgrades the document to v1.1
        doc11 = dict(doc)
        doc11["schema"] = "slice.knowledge/v1.1"
        doc11["analysis"] = {"angles": {"elbow_l_flex": 170.0},
                             "gesture": {"count": 0}}
        self.assertFalse(knowledge.validate(doc11))
        # v1 doc carrying analysis is tolerated (read compatibility
        # for documents written before the version bump)
        legacy = dict(doc)
        legacy["analysis"] = doc11["analysis"]
        self.assertFalse(knowledge.validate(legacy))
        # analysis layers must be dicts
        bad2 = dict(doc11)
        bad2["analysis"] = {"angles": [1, 2]}
        self.assertTrue(knowledge.validate(bad2))

    def test_save_is_atomic_no_tmp_leftover(self):
        doc = pipeline.strip_runtime(analyze_synth())
        with tempfile.TemporaryDirectory() as d:
            store = knowledge.KnowledgeStore(d)
            kid = store.save(doc)
            leftovers = [f for f in os.listdir(d) if f.endswith(".tmp")]
            self.assertEqual(leftovers, [])
            with open(os.path.join(d, kid + ".json"),
                      encoding="utf-8") as f:
                self.assertEqual(json.load(f)["id"], doc["id"])

    def test_validate_catches_bad(self):
        self.assertTrue(knowledge.validate({"schema": "x"}))
        doc = pipeline.strip_runtime(analyze_synth())
        doc["skeleton"]["joints"]["head"]["confidence"] = 2
        self.assertTrue(knowledge.validate(doc))


if __name__ == "__main__":
    unittest.main()
