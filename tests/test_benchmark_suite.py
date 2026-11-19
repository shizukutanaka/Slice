"""Smoke tests for the adoption benchmark suite.

The suite (benchmarks/run_benchmark.py) is a reporting tool, not a
gate; these tests pin only that it runs end to end on a small subset
and that its report keeps the shape docs/BENCHMARK.md is generated
from, so the published numbers cannot silently rot.
"""
import importlib.util
import unittest
from pathlib import Path

from slice import bitmap, evaluate, knowledge, pipeline
from slice.skeleton import OBSERVED, PREDICTED

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "run_benchmark", ROOT / "benchmarks" / "run_benchmark.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class BenchmarkSuiteTest(unittest.TestCase):
    def test_report_shape_on_small_subset(self):
        rb = _load()
        full = rb.build_cases()
        small = [c for c in full
                 if c["name"] in ("stand-flat-160x300-stand",
                                  "blank-background")]
        self.assertEqual(len(small), 2)
        rb.build_cases = lambda: small
        report = rb.run(repeats=1)
        self.assertEqual(set(report["summary"]), {"clean", "negative"})
        clean = report["summary"]["clean"]
        self.assertEqual(clean["success_rate"], 1.0)
        self.assertGreater(clean["detection_rate"], 0.9)
        # the blank image must not gain a fabricated skeleton
        self.assertEqual(report["summary"]["negative"]["success_rate"],
                         1.0)
        md = rb.to_markdown(report, "2000-01-01")
        self.assertIn("stand-flat-160x300-stand", md)
        self.assertIn("Not measured", md)


class LargeCaseArmRegressionTest(unittest.TestCase):
    """Regression: large figures used to lose both elbows and both
    wrists (detection 0.7778, `no_observed_wrists`) because the
    512 px downscale compresses the arm/torso gap to one column,
    inside the arm scan's old two-column separation margin. The
    1200x1800 left arm has no distinct run at all — it is fused
    into the torso run — and is recovered by the excess-width
    inference in `slice.pose._fused_arm_joints`."""

    def test_large_cases_keep_their_arms(self):
        rb = _load()
        large = [c for c in rb.build_cases()
                 if c["category"] == "large"]
        self.assertEqual(len(large), 2)
        rb.build_cases = lambda: large
        report = rb.run(repeats=1)
        summary = report["summary"]["large"]
        self.assertEqual(summary["success_rate"], 1.0)
        self.assertEqual(summary["detection_rate"], 1.0)
        self.assertEqual(summary["observed_rate"], 0.9445)
        by_name = {c["name"]: c for c in report["cases"]}
        for name, observed in (("stand-flat-640x960", 19),
                               ("stand-flat-1200x1800", 17)):
            case = by_name[name]
            self.assertEqual(case["accuracy"]["detection_rate"], 1.0)
            self.assertEqual(case["observed_joints"], observed)
            self.assertNotIn("no_observed_wrists", case["warnings"])

    def test_fused_arm_is_preserved_as_prediction_in_knowledge(self):
        bmp, _ = evaluate.draw_case(1200, 1800)
        doc = pipeline.strip_runtime(pipeline.analyze(bitmap.encode_png(bmp)))
        joints = doc["skeleton"]["joints"]
        prediction = doc["prediction"]
        for part in ("elbow", "wrist"):
            left, right = f"{part}_l", f"{part}_r"
            self.assertEqual(joints[left]["state"], PREDICTED)
            self.assertIn("inferred", joints[left]["basis"])
            self.assertIn(left, prediction["predicted"])
            self.assertNotIn(left, prediction["observed"])
            self.assertNotIn(left, prediction["filled"])
            self.assertEqual(joints[right]["state"], OBSERVED)
            self.assertIn(right, prediction["observed"])
        self.assertEqual(knowledge.validate(doc), [])


if __name__ == "__main__":
    unittest.main()
