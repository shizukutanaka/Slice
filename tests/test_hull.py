import unittest

from tests import synthetic_person

from slice import hull


class TestHull(unittest.TestCase):
    def test_synthetic_person(self):
        d = hull.describe(synthetic_person())
        self.assertIsNotNone(d)
        self.assertGreater(d["vertices"], 3)
        self.assertGreater(d["hull_area_px"], d["area_px"] * 0.9)
        self.assertLessEqual(d["solidity"], 1.0)
        self.assertGreater(d["solidity"], 0.3)

    def test_empty_none(self):
        from slice.bitmap import Bitmap
        b = Bitmap.new(100, 100, (255, 255, 255, 255))
        self.assertIsNone(hull.describe(b))

    def test_state_observed(self):
        d = hull.describe(synthetic_person())
        self.assertEqual(d["state"], "observed")


if __name__ == "__main__":
    unittest.main()
