import unittest

from tests import synthetic_person

from slice import scale
from slice.pose import HeuristicPoseEstimator


class TestScale(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_calibration_from_head(self):
        cal = scale.calibrate(self.skel)
        self.assertIsNotNone(cal["px_per_cm"])
        self.assertEqual(cal["state"], "estimated")

    def test_height_in_plausible_range(self):
        m = scale.measure_cm(self.skel)
        # head..foot ≈ body height; expect human-plausible 100–210cm
        h = m["lengths"].get("height")
        self.assertIsNotNone(h)
        self.assertTrue(80 <= h <= 220)

    def test_no_head_no_scale(self):
        self.skel.joints.pop("head")
        cal = scale.calibrate(self.skel)
        self.assertIsNone(cal["px_per_cm"])
        self.assertEqual(scale.measure_cm(self.skel)["lengths"], {})


if __name__ == "__main__":
    unittest.main()
