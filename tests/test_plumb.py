import unittest

from tests import synthetic_person

from slice import plumb, predict
from slice.pose import HeuristicPoseEstimator


class TestPlumb(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_upright_good_stack(self):
        r = plumb.assess(self.skel)
        self.assertIsNotNone(r["stack_score"])
        self.assertLess(r["stack_score"], 0.15)

    def test_head_forward_detected(self):
        j = self.skel.joints["head"]
        j.x += 60  # push head sideways relative to torso
        fh = plumb.forward_head(self.skel)
        self.assertIsNotNone(fh)
        self.assertEqual(fh["posture"], "forward_head")

    def test_neutral_small_offset(self):
        fh = plumb.forward_head(self.skel)
        self.assertEqual(fh["posture"], "neutral")

    def test_no_head_none(self):
        for n in ("head", "neck"):
            del self.skel.joints[n]
        self.assertIsNone(plumb.line(self.skel))

    def test_predicted_chest_no_forward_head(self):
        # a chord-placed chest can't anchor the torso line —
        # forward_head must abstain, not measure a prior
        del self.skel.joints["chest"]
        predict.complete(self.skel)
        self.assertIsNone(plumb.forward_head(self.skel))
        r = plumb.line(self.skel)
        self.assertNotIn("chest", r["offsets"])

    def test_predicted_ankle_no_base(self):
        for n in ("ankle_l", "ankle_r"):
            del self.skel.joints[n]
        predict.complete(self.skel)
        self.assertNotIn("base", plumb.line(self.skel)["offsets"])


if __name__ == "__main__":
    unittest.main()
