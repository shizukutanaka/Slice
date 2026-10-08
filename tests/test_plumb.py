import unittest

from tests import synthetic_person

from slice import plumb
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

    def test_inverted_skeleton_no_px_leak(self):
        # head below feet: body_h must not collapse to 1.0 and leak
        # raw px as body-height fractions
        h = self.skel.image_height
        for j in self.skel.joints.values():
            j.y = h - j.y
        r = plumb.line(self.skel)
        for v in r["offsets"].values():
            self.assertLess(abs(v["of_body_h"]), 0.2)
        self.assertIsNotNone(plumb.forward_head(self.skel))

    def test_no_head_none(self):
        for n in ("head", "neck"):
            del self.skel.joints[n]
        self.assertIsNone(plumb.line(self.skel))

    def test_degenerate_span_of_body_h_none(self):
        # head/neck exist but no measurable scale (flat chain, no
        # pelvis/ankle): of_body_h must be disclosed as unmeasurable,
        # not raw px dressed as a fraction via `or 1.0`
        from slice.skeleton import Joint, Skeleton
        skel = Skeleton(image_width=100, image_height=100)
        for i, name in enumerate(("head", "neck", "chest")):
            skel.joints[name] = Joint(name, 50 + i * 4, 50, 0.9)
        r = plumb.line(skel)
        self.assertIsNotNone(r)
        for v in r["offsets"].values():
            self.assertIsNone(v["of_body_h"])
        out = plumb.assess(skel)
        self.assertIsNone(out["stack_score"])


if __name__ == "__main__":
    unittest.main()
