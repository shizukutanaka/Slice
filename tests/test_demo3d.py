"""Test for the Phase-3 end-to-end demo."""
import importlib.util
import json
import os
import tempfile
import unittest

from slice import evaluate, pose

_SPEC = importlib.util.spec_from_file_location(
    "demo_3d",
    os.path.join(os.path.dirname(__file__), "..", "examples",
                 "demo_3d.py"))
demo = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo)


class TestDemo3d(unittest.TestCase):
    def test_full_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            out = demo.run(directory)
            with open(out["gltf"]) as f:
                doc = json.load(f)
            with open(out["bvh"]) as f:
                bvh_text = f.read()
            with open(out["bvh_report"]) as f:
                sidecar = json.load(f)
        self.assertGreaterEqual(out["joints"], 17)
        self.assertGreaterEqual(out["bones"], 15)
        self.assertTrue(out["bvh"].endswith(".bvh"))
        self.assertEqual(doc["asset"]["version"], "2.0")
        self.assertGreater(len(doc["nodes"]), 10)
        self.assertIn("ROOT", bvh_text[:64])

        bmp, _ = evaluate.draw_case()
        source = pose.HeuristicPoseEstimator().estimate(bmp)
        px, py = source.point("pelvis")
        cx, cy = source.point("chest")
        dx, dy = (cx - px) * 1.15, (cy - py) * 1.15
        chest = next(n for n in doc["nodes"] if n["name"] == "chest")
        self.assertEqual(chest["translation"],
                         [round(dx, 3), round(-dy, 3), 0.0])
        self.assertIn(f"JOINT chest\n\t{{\n\t\tOFFSET {dx:.2f} {dy:.2f} 0.00",
                      bvh_text)
        self.assertEqual({n["extras"]["state"] for n in doc["nodes"]},
                         {"predicted"})
        self.assertEqual(set(sidecar["predicted"]),
                         {n["name"] for n in doc["nodes"]})
        self.assertEqual(sidecar["n_joints"], out["joints"])


if __name__ == "__main__":
    unittest.main()
