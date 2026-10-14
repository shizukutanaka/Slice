import io
import json
import unittest
from contextlib import redirect_stdout

from slice.__main__ import main


class TestIkCli(unittest.TestCase):
    def test_reachable(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(
                main(["ik", "--root", "0,0",
                      "--target", "30,10",
                      "--lengths", "25,20"]), 0)
        res = json.loads(buf.getvalue())
        self.assertTrue(res["reached"])
        self.assertEqual(res["end"], [30.0, 10.0])
        self.assertGreater(res["angle_deg"], 80)

    def test_unreachable_clamps(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["ik", "--root", "0,0",
                  "--target", "100,0",
                  "--lengths", "25,20"])
        res = json.loads(buf.getvalue())
        self.assertFalse(res["reached"])
        self.assertAlmostEqual(res["end"][0], 45.0)

    def test_bad_input(self):
        self.assertEqual(
            main(["ik", "--root", "a", "--target", "0,0",
                  "--lengths", "1,1"]), 2)


if __name__ == "__main__":
    unittest.main()
