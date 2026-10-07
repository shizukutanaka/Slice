import unittest

from tests import synthetic_person

from slice import dynamics, predict
from slice.pose import HeuristicPoseEstimator


class TestDynamics(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_standing_static(self):
        r = dynamics.score(self.skel)
        self.assertLess(r["score"], 0.6)
        self.assertEqual(r["state"], "implied")

    def test_wide_step_dynamic(self):
        ankle = self.skel.joints["ankle_r"]
        ankle.x += 150
        r = dynamics.score(self.skel)
        self.assertGreaterEqual(r["score"], 0.3)
        cues = [c["cue"] for c in r["cues"]]
        self.assertIn("wide_step", cues)

    def test_com_outside_dynamic(self):
        pelvis = self.skel.joints["pelvis"]
        ar = self.skel.point("ankle_r")
        pelvis.x = ar[0] + 100
        r = dynamics.score(self.skel)
        self.assertIn("com_outside_feet",
                      [c["cue"] for c in r["cues"]])

    def test_predicted_joint_fires_no_cue(self):
        # a predicted wrist dragged far out must not fire arm_out —
        # the cue would measure the prior's position, not the pose
        del self.skel.joints["wrist_r"]
        predict.complete(self.skel)
        self.skel.joints["wrist_r"].x = 5
        cues = [c["cue"] for c in dynamics.cues(self.skel)]
        self.assertNotIn("arm_out_r", cues)

    def test_empty_skeleton_zero(self):
        for n in list(self.skel.joints):
            del self.skel.joints[n]
        r = dynamics.score(self.skel)
        self.assertEqual(r["score"], 0.0)
        self.assertEqual(r["verdict"], "static")


if __name__ == "__main__":
    unittest.main()
