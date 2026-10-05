import unittest

from tests import synthetic_person

from slice import dtw
from slice.pose import HeuristicPoseEstimator


def _shifted(skel, dx):
    import copy
    s = copy.deepcopy(skel)
    for j in s.joints.values():
        j.x += dx
    return s


class TestDtw(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_identical_zero_cost(self):
        r = dtw.align([self.skel, self.skel], [self.skel, self.skel])
        self.assertEqual(r["cost"], 0.0)
        self.assertEqual(r["path_len"], 2)

    def test_shift_uniform(self):
        a = [self.skel, _shifted(self.skel, 10), _shifted(self.skel, 20)]
        b = [_shifted(self.skel, 10)]  # slower same move
        r = dtw.align(a, b)
        self.assertLess(r["per_frame"], 15)

    def test_tempo_warped_alignment(self):
        # sequence A moves right steadily; B is the same at half speed
        a = [_shifted(self.skel, i * 10) for i in range(4)]
        b = [_shifted(self.skel, i * 5) for i in range(8)]
        r = dtw.align(a, b)
        self.assertLess(r["per_frame"], 10)

    def test_empty_none(self):
        self.assertIsNone(dtw.align([], [self.skel]))

    def test_frame_dist_shared(self):
        d = dtw.frame_dist(self.skel, _shifted(self.skel, 5))
        self.assertAlmostEqual(d, 5.0)


if __name__ == "__main__":
    unittest.main()
