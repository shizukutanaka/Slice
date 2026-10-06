import unittest

from tests import synthetic_person

from slice import distfield
from slice.pose import HeuristicPoseEstimator


class TestDistField(unittest.TestCase):
    def setUp(self):
        self.est = HeuristicPoseEstimator()
        self.bmp = synthetic_person()
        self.skel = self.est.estimate(self.bmp)
        self.mask = self.est._mask(self.bmp)
        self.dist = distfield.distance_transform(self.mask)

    def test_torso_thicker_than_arm(self):
        pelvis = self.skel.point("pelvis")
        wrist = self.skel.point("wrist_l")
        t_torso = distfield.thickness_at(self.dist, self.bmp.width,
                                       *pelvis)
        t_arm = distfield.thickness_at(self.dist, self.bmp.width,
                                       wrist[0], wrist[1] - 8)
        self.assertGreater(t_torso, t_arm)

    def test_profile(self):
        p = distfield.thickness_profile(self.dist, self.bmp.width,
                                        self.bmp.height, self.mask)
        self.assertGreater(p["max"], 5)
        self.assertGreaterEqual(p["max"], p["median"])

    def test_background_is_zero(self):
        w = self.bmp.width
        self.assertEqual(self.dist[0], 0.0)


if __name__ == "__main__":
    unittest.main()
