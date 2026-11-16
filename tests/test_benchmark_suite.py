"""Smoke tests for the adoption benchmark suite.

The suite (benchmarks/run_benchmark.py) is a reporting tool, not a
gate; these tests pin only that it runs end to end on a small subset
and that its report keeps the shape docs/BENCHMARK.md is generated
from, so the published numbers cannot silently rot.
"""
import importlib.util
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
