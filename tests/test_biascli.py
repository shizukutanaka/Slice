"""`slice bias` — per-joint systematic-error profile over fixtures."""

import io
import json
import unittest
from contextlib import redirect_stdout

from slice.__main__ import main


class BiasCliTest(unittest.TestCase):
    def test_report(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["bias"])
        rep = json.loads(buf.getvalue())
        self.assertEqual(rep["n_cases"], 2)
        self.assertTrue(rep["joints"])
        for r in rep["joints"].values():
            self.assertIn(r["verdict"],
                          ("systematic", "unbiased", "insufficient"))
        worst = rep["worst_joint"]
        self.assertIsNotNone(worst)
        # neck bias is fixed: worst joint stays under the bench gate
        self.assertLessEqual(worst["mean_error_px"], 10.0)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
