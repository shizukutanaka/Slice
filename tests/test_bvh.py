import unittest

from tests import synthetic_person

from slice import bvh
from slice.pose import HeuristicPoseEstimator


class TestBvh(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())
        self.txt = bvh.export(self.skel)

    def test_structure(self):
        self.assertIn("HIERARCHY", self.txt)
        self.assertIn("ROOT SliceFigure", self.txt)
        self.assertIn("JOINT chest", self.txt)
        self.assertIn("JOINT foot_r", self.txt)
        self.assertIn("End Site", self.txt)
        self.assertIn("MOTION", self.txt)
        self.assertIn("Frames: 1", self.txt)

    def test_channel_count_matches_motion_row(self):
        n_joints = self.txt.count("JOINT ")
        row = self.txt.strip().splitlines()[-1].split()
        self.assertEqual(len(row), 6 + 3 * n_joints)

    def test_offsets_relative(self):
        # pelvis→chest offset equals chest position minus pelvis position
        chest = self.skel.point("chest")
        pelvis = self.skel.point("pelvis")
        expected = f"OFFSET {chest[0]-pelvis[0]:.2f} " \
                   f"{chest[1]-pelvis[1]:.2f} 0.00"
        self.assertIn(expected, self.txt)

    def test_no_root_raises(self):
        self.skel.joints.pop("pelvis")
        with self.assertRaises(ValueError):
            bvh.export(self.skel)


if __name__ == "__main__":
    unittest.main()
