import unittest

from tests import synthetic_person

from slice import ground, predict
from slice.pose import HeuristicPoseEstimator


class TestGround(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_standing_is_grounded(self):
        r = ground.estimate(self.skel)
        self.assertEqual(r["contact"], "grounded")
        self.assertIn("support_is_lowest", r["reasons"])
        self.assertIsNotNone(r["ground_y"])

    def test_no_support_unknown(self):
        for n in ("foot_l", "foot_r", "ankle_l", "ankle_r"):
            del self.skel.joints[n]
        self.assertEqual(ground.estimate(self.skel)["contact"], "unknown")

    def test_frame_edge_is_cropped(self):
        gy = ground.estimate(self.skel)["ground_y"]
        r = ground.estimate(self.skel, frame_h=int(gy))
        self.assertEqual(r["contact"], "cropped")

    def test_predicted_feet_no_clearance(self):
        # "foot below ankle" priors sit ~3% below the observed ankle —
        # they must not fabricate a floating gap (clearance 7.8px
        # on a grounded figure before the fix)
        for n in ("foot_l", "foot_r"):
            del self.skel.joints[n]
        predict.complete(self.skel)
        self.assertEqual(self.skel.joints["foot_l"].state, "predicted")
        r = ground.estimate(self.skel)
        self.assertEqual(r["contact"], "grounded")
        self.assertEqual(ground.clearance(self.skel), 0)

    def test_floating_figure_airborne(self):
        # a hand below the feet reads as airborne
        j = self.skel.joints["wrist_l"]
        lo = max(x.y for x in self.skel.joints.values())
        j.y = lo + 50
        r = ground.estimate(self.skel)
        self.assertEqual(r["contact"], "airborne")
        self.assertGreater(ground.clearance(self.skel), 0)


if __name__ == "__main__":
    unittest.main()
