import copy
import unittest

from tests import synthetic_person

from slice import query
from slice.pose import HeuristicPoseEstimator


def _arm_up(skel):
    s = copy.deepcopy(skel)
    s.joints["wrist_r"].y -= 200
    return s


class TestQuery(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_self_top_match(self):
        r = query.rank(self.skel, [_arm_up(self.skel), self.skel])
        self.assertEqual(r[0]["index"], 1)
        self.assertAlmostEqual(r[0]["score"], 1.0)

    def test_different_lower(self):
        sim = query.similarity(self.skel, _arm_up(self.skel))
        self.assertLess(sim["score"], 1.0)
        self.assertGreater(sim["compared"], 10)

    def test_empty_joints_none(self):
        from slice.skeleton import Skeleton
        self.assertIsNone(query.similarity(Skeleton(100, 100),
                                           self.skel))

    def test_rank_order(self):
        cands = [_arm_up(self.skel), self.skel, _arm_up(self.skel)]
        r = query.rank(self.skel, cands)
        self.assertEqual([x["index"] for x in r], [1, 0, 2])


if __name__ == "__main__":
    unittest.main()
