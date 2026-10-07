import unittest

from tests import synthetic_person

from slice import predict, scale
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

    def test_predicted_joints_no_scale(self):
        # a predicted neck makes head_px a prior measurement — the
        # scale factor would be fabricated, so it must be withheld
        del self.skel.joints["neck"]
        predict.complete(self.skel)
        cal = scale.calibrate(self.skel)
        self.assertIsNone(cal["px_per_cm"])

    def test_predicted_endpoint_no_length(self):
        del self.skel.joints["foot_l"]
        predict.complete(self.skel)
        m = scale.measure_cm(self.skel)
        self.assertNotIn("height", m["lengths"])

    def test_no_head_no_scale(self):
        self.skel.joints.pop("head")
        cal = scale.calibrate(self.skel)
        self.assertIsNone(cal["px_per_cm"])
        self.assertEqual(scale.measure_cm(self.skel)["lengths"], {})


if __name__ == "__main__":
    unittest.main()
