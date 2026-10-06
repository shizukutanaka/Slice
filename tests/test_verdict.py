"""Tests for slice.verdict — unified severity aggregation."""
import unittest

from slice import verdict


class TestVerdict(unittest.TestCase):
    def test_severity_map(self):
        self.assertEqual(verdict.severity_of("stable"), "ok")
        self.assertEqual(verdict.severity_of("sensitive"), "advisory")
        self.assertEqual(verdict.severity_of("broken"), "problem")
        self.assertEqual(verdict.severity_of("single_run"),
                         "unmeasured")
        self.assertEqual(verdict.severity_of(None), "unmeasured")

    def test_grade_aggregation(self):
        r = verdict.grade({
            "imgqual": {"verdict": "adequate"},
            "fit": {"verdict": "good"},
            "evid": {"verdict": "supported"},
        })
        self.assertEqual(r["overall"], "ok")
        self.assertEqual(r["n_layers"], 3)

    def test_worst_wins(self):
        r = verdict.grade({
            "a": {"verdict": "stable"},
            "b": {"verdict": "mismatch"},
            "c": {"verdict": "sensitive"},
        })
        self.assertEqual(r["overall"], "problem")
        self.assertEqual(r["worst"], ["b"])

    def test_unmeasured_not_counted(self):
        r = verdict.grade({
            "a": {"verdict": "unmeasurable"},
            "b": {"verdict": "stable"},
        })
        self.assertEqual(r["overall"], "ok")

    def test_unmapped_vocab_reported(self):
        r = verdict.grade({"x": {"verdict": "flibberty"}})
        self.assertEqual(r["unmapped"], ["x: flibberty"])
        self.assertEqual(r["overall"], "unmeasured")

    def test_acceptable(self):
        r = verdict.grade({"a": {"verdict": "sensitive"}})
        self.assertTrue(verdict.acceptable(r, "advisory"))
        self.assertFalse(verdict.acceptable(r, "ok"))
        empty = verdict.grade({})
        self.assertTrue(verdict.acceptable(empty))


if __name__ == "__main__":
    unittest.main()
