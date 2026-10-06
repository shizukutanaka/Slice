import unittest

from tests import synthetic_person

from slice import consistency
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Joint


class TestAudit(unittest.TestCase):
    def test_clean_figure_has_no_issues(self):
        skel = HeuristicPoseEstimator().estimate(synthetic_person())
        self.assertEqual(consistency.audit(skel), [])

    def test_out_of_frame_joint_flagged(self):
        skel = HeuristicPoseEstimator().estimate(synthetic_person())
        skel.set(Joint("wrist_l", skel.image_width + 5, 100, 0.5))
        self.assertIn("wrist_l_out_of_frame", consistency.audit(skel))

    def test_impossible_leg_length_flagged(self):
        skel = HeuristicPoseEstimator().estimate(synthetic_person())
        knee = skel.get("knee_l")
        skel.set(Joint("knee_l", knee.x, knee.y - 300, knee.confidence))
        issues = consistency.audit(skel)
        self.assertIn("hip_l_knee_l_too_long", issues)


if __name__ == "__main__":
    unittest.main()
