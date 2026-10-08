import unittest

from tests import synthetic_person

from slice import predict
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import OBSERVED, PREDICTED, Skeleton


class TestPredict(unittest.TestCase):
    def test_mirror_completion(self):
        sk = Skeleton(100, 200)
        from slice.skeleton import Joint
        sk.set(Joint("spine", 50, 100, 0.8, OBSERVED))
        sk.set(Joint("hip_l", 40, 120, 0.8, OBSERVED))
        sk.set(Joint("hip_r", 60, 120, 0.8, OBSERVED))
        sk.set(Joint("knee_l", 38, 160, 0.8, OBSERVED))
        sk.set(Joint("ankle_l", 36, 195, 0.8, OBSERVED))
        added = predict.complete(sk)
        names = {j.name for j in added}
        self.assertIn("knee_r", names)
        kr = sk.get("knee_r")
        self.assertEqual(kr.state, PREDICTED)
        self.assertAlmostEqual(kr.x, 62, delta=2)
        self.assertLess(kr.confidence, sk.get("knee_l").confidence)

    def test_prior_completion_when_nothing_visible(self):
        sk = Skeleton(100, 200)
        from slice.skeleton import Joint
        sk.set(Joint("shoulder_l", 30, 50, 0.8, OBSERVED))
        added = predict.complete(sk)
        names = {j.name for j in added}
        self.assertIn("elbow_l", names)
        el = sk.get("elbow_l")
        self.assertEqual(el.state, PREDICTED)
        self.assertGreater(el.y, 50)

    def test_mid_chain_interpolation(self):
        # elbow missing but shoulder and wrist known -> elbow sits on the
        # segment between them, not on a straight prior drop
        sk = Skeleton(100, 200)
        from slice.skeleton import Joint
        sk.set(Joint("shoulder_l", 30, 60, 0.8, OBSERVED))
        sk.set(Joint("wrist_l", 10, 120, 0.8, OBSERVED))
        predict.complete(sk)
        el = sk.get("elbow_l")
        self.assertEqual(el.state, PREDICTED)
        self.assertIn("interpolated", el.basis)
        # adult prior: upper/(upper+fore) ≈ .545 -> el ≈ lerp(sh, wr, .545)
        self.assertAlmostEqual(el.x, 30 + (10 - 30) * 0.545, delta=3)
        self.assertAlmostEqual(el.y, 60 + (120 - 60) * 0.545, delta=3)
        # the straight prior drop would have kept x near shoulder+x
        self.assertLess(el.x, 30)

    def test_wrist_extends_observed_elbow(self):
        # wrist continues from the elbow, not from the shoulder's
        # straight prior drop
        sk = Skeleton(100, 200)
        from slice.skeleton import Joint
        sk.set(Joint("shoulder_l", 30, 60, 0.8))
        sk.set(Joint("elbow_l", 10, 100, 0.8))   # bent arm
        predict.complete(sk)
        wr = sk.get("wrist_l")
        self.assertEqual(wr.state, PREDICTED)
        self.assertIn("elbow_l", wr.basis)
        self.assertGreater(wr.y, 100, "wrist must not land above elbow")
        self.assertLess(wr.x, 10)

    def test_torso_only_grows_limbs(self):
        # missing shoulders/hips are derived from the torso anchors so
        # arm and leg chains can complete
        sk = Skeleton(100, 300)
        from slice.skeleton import Joint
        sk.set(Joint("head", 50, 20, 0.8))
        sk.set(Joint("neck", 50, 45, 0.8))
        sk.set(Joint("chest", 50, 80, 0.8))
        sk.set(Joint("pelvis", 50, 130, 0.8))
        sk.set(Joint("spine", 50, 105, 0.8))
        predict.complete(sk)
        for n in ("shoulder_l", "shoulder_r", "hip_l", "hip_r",
                  "wrist_l", "ankle_r"):
            self.assertIn(n, sk.joints, n)
        self.assertLess(sk.get("shoulder_l").x, sk.get("neck").x)
        self.assertGreater(sk.get("shoulder_r").x, sk.get("neck").x)

    def test_full_pipeline_needs_no_prior_fallback_for_missing(self):
        sk = HeuristicPoseEstimator().estimate(synthetic_person())
        added = predict.complete(sk)
        for j in added:
            self.assertEqual(j.state, PREDICTED)
            self.assertTrue(0 < j.confidence <= 1)
        # a completed skeleton should have most vocabulary filled
        self.assertGreaterEqual(len(sk.joints), 14)


if __name__ == "__main__":
    unittest.main()
