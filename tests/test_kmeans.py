import copy
import unittest

from tests import synthetic_person

from slice import kmeans
from slice.pose import HeuristicPoseEstimator


def _arm_up(skel):
    s = copy.deepcopy(skel)
    s.joints["wrist_r"].y -= 200
    s.joints["wrist_l"].y -= 200
    return s


class TestKmeans(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_two_groups_separate(self):
        skels = ([self.skel] * 3 + [_arm_up(self.skel)] * 3)
        r = kmeans.cluster(skels, k=2)
        self.assertEqual(len(r), 2)
        sizes = sorted(o["size"] for o in r)
        self.assertEqual(sizes, [3, 3])
        # indices 0-2 together, 3-5 together
        groups = sorted(sorted(o["members"]) for o in r)
        self.assertEqual(groups, [[0, 1, 2], [3, 4, 5]])

    def test_deterministic_seed(self):
        skels = [self.skel, _arm_up(self.skel), self.skel]
        a = kmeans.cluster(skels, k=2, seed=7)
        b = kmeans.cluster(skels, k=2, seed=7)
        self.assertEqual([o["members"] for o in a],
                         [o["members"] for o in b])

    def test_features_length(self):
        self.assertEqual(len(kmeans.features(self.skel)), 34)

    def test_empty_none(self):
        self.assertIsNone(kmeans.cluster([], k=2))


if __name__ == "__main__":
    unittest.main()
