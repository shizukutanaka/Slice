import unittest

from tests import synthetic_person

from slice import dominance
from slice.pose import HeuristicPoseEstimator


class TestDominance(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_centered_even_or_leans(self):
        r = dominance.assess(self.skel)
        self.assertIn(r["dominant"], ("even", "l", "r"))
        self.assertGreater(r["confidence"], 0)
        self.assertTrue(r["cues"])

    def test_pelvis_shift_right_dominant(self):
        pelvis = self.skel.joints["pelvis"]
        ar = self.skel.point("ankle_r")
        pelvis.x = ar[0]  # pelvis fully over right ankle
        r = dominance.assess(self.skel)
        self.assertEqual(r["dominant"], "r")
        self.assertGreater(r["confidence"], 0.5)

    def test_bent_leg_unloads_side(self):
        knee = self.skel.joints["knee_l"]
        ankle = self.skel.joints["ankle_l"]
        hip = self.skel.point("hip_l")
        knee.x = hip[0] - 90
        ankle.x = hip[0] - 95
        r = dominance.assess(self.skel)
        self.assertEqual(r["dominant"], "r")

    def test_empty_skeleton_unknown(self):
        for n in list(self.skel.joints):
            del self.skel.joints[n]
        self.assertEqual(dominance.assess(self.skel)["dominant"],
                         "unknown")


if __name__ == "__main__":
    unittest.main()
