import unittest

from tests import synthetic_person

from slice import lift
from slice.pose import HeuristicPoseEstimator


class TestLift(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_front_view_is_flat(self):
        self.skel.orientation = {"facing": "front"}
        d = lift.lift(self.skel)
        for v in d.values():
            self.assertEqual(v["z"], 0.0)
            self.assertEqual(v["basis"], "no_depth_cue")
        self.assertEqual(lift.depth_spread(d), 0.0)

    def test_side_view_pushes_far_limb_back(self):
        self.skel.orientation = {"facing": "side", "side": "left"}
        d = lift.lift(self.skel)
        # far side gets +z, near side stays 0 (convention aside)
        zs = {d["wrist_l"]["z"], d["wrist_r"]["z"]}
        self.assertEqual(min(zs), 0.0)
        self.assertGreater(max(zs), 0.0)
        self.assertGreater(lift.depth_spread(d), 0.0)

    def test_unknown_facing_flat(self):
        self.skel.orientation = {}
        d = lift.lift(self.skel)
        self.assertEqual(lift.depth_spread(d), 0.0)


if __name__ == "__main__":
    unittest.main()
