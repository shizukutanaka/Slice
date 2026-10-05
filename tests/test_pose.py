import unittest

from tests import synthetic_person

from slice.pose import HeuristicPoseEstimator
from slice.skeleton import OBSERVED


class TestHeuristicPose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_core_joints_observed(self):
        for n in ("head", "neck", "shoulder_l", "shoulder_r",
                  "pelvis", "knee_l", "knee_r", "ankle_l", "ankle_r"):
            self.assertIn(n, self.skel.joints, n)
            self.assertEqual(self.skel.joints[n].state, OBSERVED, n)

    def test_vertical_order(self):
        j = self.skel.joints
        self.assertLess(j["head"].y, j["neck"].y)
        self.assertLess(j["neck"].y, j["pelvis"].y)
        self.assertLess(j["pelvis"].y, j["ankle_l"].y)

    def test_left_right_separation(self):
        j = self.skel.joints
        self.assertLess(j["shoulder_l"].x, j["shoulder_r"].x)
        self.assertLess(j["ankle_l"].x, j["ankle_r"].x)

    def test_dangling_wrist_below_hip(self):
        j = self.skel.joints
        for side in ("l", "r"):
            self.assertEqual(j[f"wrist_{side}"].state, OBSERVED, side)
            self.assertGreater(j[f"wrist_{side}"].y, j[f"hip_{side}"].y,
                               f"wrist_{side} should hang below the hip line")

    def test_confidence_range(self):
        for j in self.skel.joints.values():
            self.assertTrue(0 < j.confidence <= 1)

    def test_orientation_and_model(self):
        self.assertIn(self.skel.orientation["facing"],
                      ("front", "side", "three-quarter"))
        self.assertIn(self.skel.body_model["name"],
                      ("adult", "child", "deformed"))

    def test_blank_image(self):
        from slice.bitmap import Bitmap
        sk = HeuristicPoseEstimator().estimate(Bitmap.new(80, 80,
                                                          (255, 255, 255, 255)))
        self.assertFalse(sk.joints)


if __name__ == "__main__":
    unittest.main()
