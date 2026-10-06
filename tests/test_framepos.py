import unittest

from tests import synthetic_person

from slice import framepos
from slice.pose import HeuristicPoseEstimator


class TestFramepos(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())
        self.W, self.H = 300, 400

    def test_shape(self):
        r = framepos.analyze(self.skel, self.W, self.H)
        for k in ("headroom", "footroom", "side_gap",
                  "center_offset", "body_fraction", "thirds_zone"):
            self.assertIn(k, r)
        self.assertGreaterEqual(r["headroom"], 0)
        self.assertLessEqual(r["body_fraction"], 1)

    def test_centered_offset_small(self):
        r = framepos.analyze(self.skel, self.W, self.H)
        self.assertLess(abs(r["center_offset"]), 0.3)

    def test_tight_when_head_at_top(self):
        for j in self.skel.joints.values():
            j.y -= 200  # shove figure up
        self.assertEqual(framepos.framing(self.skel, self.W, self.H),
                         "tight")

    def test_wide_when_small_figure(self):
        for j in self.skel.joints.values():
            j.x = self.W / 2 + (j.x - self.W / 2) * 0.3
            j.y = self.H / 2 + (j.y - self.H / 2) * 0.3
        r = framepos.analyze(self.skel, self.W, self.H)
        self.assertLess(r["body_fraction"], 0.2)

    def test_empty_none(self):
        for n in list(self.skel.joints):
            del self.skel.joints[n]
        self.assertIsNone(framepos.analyze(self.skel, self.W, self.H))


if __name__ == "__main__":
    unittest.main()
