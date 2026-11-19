"""Canvas overlay regression checks for the web viewer."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path


class TestViewer(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is unavailable")
    def test_canvas_uses_shape_as_well_as_color(self):
        html = (Path(__file__).resolve().parents[1] /
                "slice" / "viewer.html").read_text(encoding="utf-8")
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        setup = """
const calls = [];
let dash = [], mark;
const context = {
  setLineDash: value => { dash = value; },
  drawImage() {}, beginPath() {}, lineTo() {},
  moveTo: () => { mark = 'bone'; },
  arc: () => { mark = 'joint'; },
  stroke: () => calls.push([mark, 'stroke', dash]),
  fill: () => calls.push([mark, 'fill', dash])
};
const toggle = {checked: true};
const document = {getElementById: id =>
  id === 'showPred' ? toggle : {getContext: () => context}};
class Image { width = 300; height = 300; }
"""
        exercise = """
doc = {skeleton: {frame: {width: 300, height: 300},
  bones: [['b', 'c'], ['a', 'b']], joints: {
    a: {x: 40, y: 100, state: 'observed'},
    b: {x: 120, y: 100, state: 'observed'},
    c: {x: 200, y: 100, state: 'predicted'}
}}};
draw();
const all = calls.splice(0);
toggle.checked = false;
toggle.onchange();
console.log(JSON.stringify({all, observed: calls}));
"""
        result = subprocess.run(["node", "-"], input=setup + script + exercise,
                                text=True, capture_output=True, check=True)
        observed_bone = ["bone", "stroke", []]
        observed_joint = ["joint", "fill", []]
        self.assertEqual(json.loads(result.stdout), {
            "all": [["bone", "stroke", [6, 4]], observed_bone,
                    observed_joint, observed_joint, ["joint", "stroke", []]],
            "observed": [observed_bone, observed_joint, observed_joint],
        })
