import unittest

from tests import synthetic_person

from slice import rig
from slice.pose import HeuristicPoseEstimator


class TestRig(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())
        self.rig = rig.build(self.skel)

    def test_all_bones_present(self):
        names = {b["name"] for b in self.rig}
        self.assertIn("thigh_l", names)
        self.assertIn("forearm_r", names)
        self.assertIn("spine", names)
        self.assertEqual(len(self.rig), 17)

    def test_child_head_equals_parent_tail(self):
        by_parent = {b["parent"]: b for b in self.rig}
        knee = by_parent["knee_l"]          # shin_l bone
        thigh = next(b for b in self.rig if b["name"] == "thigh_l")
        self.assertEqual(knee["head"], thigh["tail"])

    def test_missing_joint_omits_bones(self):
        self.skel.joints.pop("wrist_l")
        r = rig.build(self.skel)
        self.assertNotIn("forearm_l", {b["name"] for b in r})
        self.assertEqual(len(r), len(self.rig) - 1)

    def test_lengths_positive(self):
        self.assertGreater(rig.total_bone_length(self.rig), 50)


if __name__ == "__main__":
    unittest.main()
