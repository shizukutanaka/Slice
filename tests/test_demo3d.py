"""Test for the Phase-3 end-to-end demo."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from slice import evaluate, pose

_SPEC = importlib.util.spec_from_file_location(
    "demo_3d",
    os.path.join(os.path.dirname(__file__), "..", "examples",
                 "demo_3d.py"))
demo = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo)

_BLENDER = os.environ.get("BLENDER_BIN") or shutil.which("blender")


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

    @unittest.skipUnless(_BLENDER, "Blender not found; set BLENDER_BIN")
    def test_blender_import(self):
        with tempfile.TemporaryDirectory() as directory:
            gltf = demo.run(directory)["gltf"]
            report = Path(directory) / "blender-report.json"
            code = f"""\
import bpy
import json
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
result = bpy.ops.import_scene.gltf(filepath={gltf!r})
if result != {{"FINISHED"}}:
    raise RuntimeError(f"glTF import returned {{result}}")
bpy.context.view_layer.update()
objects = {{obj.name: {{
    "type": obj.type,
    "parent": obj.parent.name if obj.parent else None,
    "location": list(obj.matrix_world.translation),
    "extras": dict(obj.items()),
}} for obj in bpy.context.scene.objects}}
Path({str(report)!r}).write_text(json.dumps(objects), encoding="utf-8")
"""
            result = subprocess.run(
                [_BLENDER, "--background", "--factory-startup",
                 "--python-exit-code", "1", "--python-expr", code],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(report.is_file(), result.stdout)
            objects = json.loads(report.read_text(encoding="utf-8"))
            nodes = json.loads(Path(gltf).read_text(encoding="utf-8"))["nodes"]

        self.assertEqual(set(objects), {n["name"] for n in nodes})
        parents = {i: n for n in nodes for i in n.get("children", [])}
        for i, n in enumerate(nodes):
            with self.subTest(joint=n["name"]):
                obj = objects[n["name"]]
                parent = parents.get(i)
                self.assertEqual(obj["type"], "EMPTY")
                self.assertEqual(obj["parent"],
                                 parent["name"] if parent else None)
                self.assertEqual(obj["extras"], n["extras"])
                x, y, z = n["translation"]
                origin = (objects[parent["name"]]["location"]
                          if parent else (0, 0, 0))
                # Blender converts glTF Y-up to Z-up: (x, y, z) -> (x, -z, y).
                for actual, offset, delta in zip(obj["location"], origin,
                                                 (x, -z, y)):
                    self.assertAlmostEqual(actual, offset + delta, places=4)


if __name__ == "__main__":
    unittest.main()
