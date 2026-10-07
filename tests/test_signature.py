import unittest

from tests import synthetic_person

from slice import signature as sig
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Joint, Skeleton


class TestSignature(unittest.TestCase):
    def setUp(self):
        self.est = HeuristicPoseEstimator()
        self.skel = self.est.estimate(synthetic_person())
        self.s = sig.signature(self.skel)

    def test_fixed_length(self):
        self.assertEqual(len(self.s), 17 * 2 + 4)

    def test_same_pose_zero_distance(self):
        self.assertEqual(sig.distance(self.s, self.s), 0.0)

    def test_scale_invariance(self):
        big = self.est.estimate(synthetic_person(320, 600))
        d = sig.distance(self.s, sig.signature(big))
        self.assertIsNotNone(d)
        self.assertLess(d, 0.15)

    def test_missing_feet_stay_torso_normalised(self):
        # without feet the scalars must not become raw pixels
        other = Skeleton(self.skel.image_width, self.skel.image_height)
        for n, j in self.skel.joints.items():
            if n.startswith("foot"):
                continue
            other.set(Joint(n, j.x, j.y, j.confidence, state=j.state))
        v = sig.signature(other)
        self.assertTrue(all(abs(s) < 2.0 for s in v[-4:]),
                        "scalars leaked raw-pixel magnitudes")
        d = sig.distance(self.s, v)
        self.assertLess(d, 0.5)

    def test_bent_arm_changes_signature(self):
        other = Skeleton(self.skel.image_width, self.skel.image_height)
        for n, j in self.skel.joints.items():
            other.set(Joint(n, j.x, j.y, j.confidence, state=j.state))
        other.joints["wrist_l"].y -= 120  # raise the hand overhead
        d = sig.distance(self.s, sig.signature(other))
        self.assertGreater(d, 0.02)


if __name__ == "__main__":
    unittest.main()
