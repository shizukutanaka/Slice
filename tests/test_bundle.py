import json
import os
import tempfile
import unittest

from slice.bundle import manifest, pack, unpack
from slice.knowledge import KnowledgeStore, build
from slice.pose import HeuristicPoseEstimator
from tests import synthetic_person


def _doc():
    skel = HeuristicPoseEstimator().estimate(synthetic_person())
    return build(skel, {"shoulder_hip": 1.0}, {"label": "standing"},
                 engine={"name": "heuristic", "version": "1"})


class TestBundle(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(tmp)
            doc = _doc()
            store.save(doc)
            zpath = os.path.join(tmp, "out.zip")
            m = pack(store, zpath)
            self.assertEqual(m["count"], 1)
            docs = unpack(zpath)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]["id"], doc["id"])
            self.assertEqual(docs[0]["skeleton"]["joints"],
                             doc["skeleton"]["joints"])

    def test_manifest_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(tmp)
            store.save(_doc())
            zpath = os.path.join(tmp, "out.zip")
            pack(store, zpath)
            m = manifest(zpath)
            self.assertEqual(m["schema"], "slice.bundle/v1")
            self.assertEqual(m["documents"][0]["body_model"],
                             "adult")
            self.assertEqual(m["skipped"], 0)

    def test_invalid_files_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(tmp)
            store.save(_doc())
            with open(os.path.join(tmp, "broken.json"), "w") as f:
                f.write("{not json")
            with open(os.path.join(tmp, "badschema.json"),
                      "w") as f:
                json.dump({"no": "schema"}, f)
            zpath = os.path.join(tmp, "out.zip")
            m = pack(store, zpath)
            self.assertEqual(m["count"], 1)
            # broken.json never surfaces from store.list();
            # only the listed-but-id-less entry is counted
            self.assertEqual(m["skipped"], 1)
            self.assertEqual(len(unpack(zpath)), 1)

    def test_unpack_skips_corrupt_members(self):
        # one bad member must not abort the whole archive
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(tmp)
            doc = _doc()
            store.save(doc)
            zpath = os.path.join(tmp, "out.zip")
            pack(store, zpath)
            with zipfile.ZipFile(zpath, "a") as z:
                z.writestr("docs/corrupt.json", "{not json")
                z.writestr("docs/nondict.json", "[1, 2]")
            docs = unpack(zpath)
            self.assertEqual([d["id"] for d in docs], [doc["id"]])

    def test_pack_survives_unprocessable_doc(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(tmp)
            store.save(_doc())
            # validate raises inside on malformed internals — pack
            # must skip that doc, not die
            with open(os.path.join(tmp, "k_aaaaaaaaaaaa.json"),
                      "w") as f:
                json.dump({"id": "k_aaaaaaaaaaaa",
                           "skeleton": {"joints": {"head": 5}}}, f)
            m = pack(store, os.path.join(tmp, "out.zip"))
            self.assertEqual(m["count"], 1)
            self.assertEqual(m["skipped"], 1)

    def test_empty_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = KnowledgeStore(tmp)
            zpath = os.path.join(tmp, "out.zip")
            m = pack(store, zpath)
            self.assertEqual(m["count"], 0)
            self.assertEqual(unpack(zpath), [])


if __name__ == "__main__":
    unittest.main()
