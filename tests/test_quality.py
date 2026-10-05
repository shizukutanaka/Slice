import unittest

from tests import synthetic_person

from slice import quality
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Skeleton


class TestQuality(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_full_observation_high(self):
        g = quality.grade(self.skel)
        self.assertIn(g["grade"], ("A", "B"))
        self.assertGreater(g["score"], 0.7)
        self.assertTrue(all(g["regions"].values()))

    def test_predicted_joints_lower(self):
        for j in self.skel.joints.values():
            if j.name.split("_")[-1] in ("l", "r"):
                j.state = "predicted"
        g = quality.grade(self.skel)
        self.assertFalse(g["regions"]["arms"])
        self.assertFalse(g["regions"]["legs"])
        full = quality.grade(
            HeuristicPoseEstimator().estimate(synthetic_person()))
        self.assertLess(g["score"], full["score"])

    def test_empty_e(self):
        g = quality.grade(Skeleton(100, 100))
        self.assertEqual(g["grade"], "E")
        self.assertEqual(g["score"], 0.0)

    def test_state_estimated(self):
        self.assertEqual(quality.grade(self.skel)["state"],
                         "estimated")


if __name__ == "__main__":
    unittest.main()
