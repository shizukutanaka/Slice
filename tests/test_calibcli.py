"""`slice calib` — confidence calibration over ground-truth fixtures."""

import io
import json
import unittest
from contextlib import redirect_stdout

from slice.__main__ import main


class CalibCliTest(unittest.TestCase):
    def test_report(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["calib"])
        rep = json.loads(buf.getvalue())
        self.assertEqual(rep["state"], "estimated")
        self.assertIn("hit_radius_px", rep)
        self.assertEqual(len(rep["bins"]), 10)
        filled = [b for b in rep["bins"] if b["n"]]
        self.assertTrue(filled)
        for b in filled:
            self.assertGreaterEqual(b["accuracy"], 0.0)
            self.assertLessEqual(b["accuracy"], 1.0)
            self.assertGreater(b["mean_conf"], 0.0)
        self.assertEqual(
            rep["overconfident_bins"],
            sum(1 for b in filled if b["mean_conf"] - b["accuracy"] > 0.10))
        # exit code is 1 only when overconfident bins exist
        self.assertEqual(rc, 1 if rep["overconfident_bins"] else 0)


if __name__ == "__main__":
    unittest.main()
