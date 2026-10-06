"""Tests for slice.calib — confidence reliability measurement."""
import unittest

from slice import calib, evaluate, pose


def _pairs(n=4):
    return [evaluate.draw_case(160, 300) for _ in range(n)]


class TestCalib(unittest.TestCase):
    def test_table_shape(self):
        t = calib.reliability_table(_pairs())
        self.assertEqual(len(t), calib.BINS)
        for b in t:
            self.assertIn("n", b)
            self.assertIn("accuracy", b)
            if b["n"]:
                self.assertIsNotNone(b["mean_conf"])
                self.assertIsNotNone(b["mean_error"])

    def test_bins_nonempty(self):
        t = calib.reliability_table(_pairs())
        total = sum(b["n"] for b in t)
        # 4 fixtures x ~17 truth joints — most land somewhere
        self.assertGreater(total, 40)
        self.assertTrue(any(b["n"] for b in t))

    def test_lookup(self):
        t = calib.reliability_table(_pairs())
        filled = next(b for b in t if b["n"])
        mid = (filled["lo"] + filled["hi"]) / 2
        v = calib.lookup(mid, t)
        self.assertEqual(v, filled["accuracy"])
        self.assertIsNone(calib.lookup(0.0, t)) if \
            t[0]["n"] == 0 else None

    def test_apply_side_record(self):
        pairs = _pairs()
        t = calib.reliability_table(pairs)
        est = pose.HeuristicPoseEstimator()
        sk = est.estimate(pairs[0][0])
        before = {n: j.confidence for n, j in sk.joints.items()}
        rec = calib.apply(sk, t)
        self.assertTrue(rec)
        for n, acc in rec.items():
            self.assertIsNotNone(acc)
            self.assertEqual(sk.joints[n].confidence, before[n])

    def test_report_fields(self):
        r = calib.report(_pairs())
        self.assertEqual(r["state"], "estimated")
        self.assertIn("overconfident_bins", r)
        self.assertIn("bins", r)

    def test_empty_pairs(self):
        t = calib.reliability_table([])
        self.assertEqual(len(t), calib.BINS)
        self.assertTrue(all(b["n"] == 0 for b in t))


if __name__ == "__main__":
    unittest.main()
