import unittest

from tests import synthetic_person

from slice import agecue
from slice.pose import HeuristicPoseEstimator


class TestAgecue(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_adult_band_default(self):
        e = agecue.estimate(self.skel)
        self.assertEqual(e["state"], "estimated")
        self.assertIn(e["band"], ("adult", "juvenile", "child"))
        self.assertGreater(e["ratio"], 0.05)
        self.assertLess(e["ratio"], 0.30)

    def test_heads_tall_consistent(self):
        r = agecue.ratio(self.skel)
        h = agecue.heads_tall(self.skel)
        self.assertAlmostEqual(1.0 / r, h, places=2)

    def test_big_head_reads_child(self):
        neck = self.skel.joints["neck"]
        head = self.skel.joints["head"]
        head.y = neck.y - 100  # inflate head length
        e = agecue.estimate(self.skel)
        self.assertIn(e["band"], ("infant", "child"))

    def test_no_head_none(self):
        del self.skel.joints["head"]
        self.assertIsNone(agecue.estimate(self.skel))


if __name__ == "__main__":
    unittest.main()
