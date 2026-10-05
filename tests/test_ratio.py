import unittest

from tests import synthetic_person

from slice import ratio
from slice.pose import HeuristicPoseEstimator


class TestRatio(unittest.TestCase):
    def test_ratios_present_and_sane(self):
        sk = HeuristicPoseEstimator().estimate(synthetic_person())
        r = ratio.analyze(sk, centroid=sk.centroid)
        self.assertNotIn("error", r)
        self.assertGreater(r["head_to_body"], 2)
        self.assertLess(r["head_to_body"], 20)
        for k in ("shoulder_width", "hip_width", "torso_length"):
            self.assertIsNotNone(r[k], k)
        self.assertIsNotNone(r["center_of_mass"])
        self.assertTrue(0 < r["center_of_mass"]["y_ratio"] < 1)

    def test_empty_skeleton(self):
        from slice.skeleton import Skeleton
        self.assertIn("error", ratio.analyze(Skeleton(10, 10)))


if __name__ == "__main__":
    unittest.main()
