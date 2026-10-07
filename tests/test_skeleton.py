import unittest

from tests import synthetic_person

from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Joint, OBSERVED, PREDICTED, Skeleton


class TestNormalized(unittest.TestCase):
    def test_pelvis_is_origin(self):
        skel = HeuristicPoseEstimator().estimate(synthetic_person())
        norm = skel.normalized()
        self.assertIsNotNone(norm)
        self.assertEqual(norm["origin"], "pelvis")
        self.assertAlmostEqual(norm["joints"]["pelvis"]["x"], 0.0)
        self.assertAlmostEqual(norm["joints"]["pelvis"]["y"], 0.0)

    def test_neck_is_unit_distance(self):
        skel = HeuristicPoseEstimator().estimate(synthetic_person())
        norm = skel.normalized()
        n = norm["joints"]["neck"]
        self.assertAlmostEqual((n["x"] ** 2 + n["y"] ** 2) ** 0.5, 1.0,
                               places=3)

    def test_resolution_independent(self):
        est = HeuristicPoseEstimator()
        big = est.estimate(synthetic_person(320, 600)).normalized()
        small = est.estimate(synthetic_person(160, 300)).normalized()
        for name in big["joints"]:
            a, b = big["joints"][name], small["joints"][name]
            self.assertAlmostEqual(a["x"], b["x"], delta=0.15, msg=name)
            self.assertAlmostEqual(a["y"], b["y"], delta=0.15, msg=name)

    def test_missing_core_omits_field(self):
        skel = Skeleton(100, 100)
        skel.set(Joint("head", 50, 10, 0.5))
        self.assertIsNone(skel.normalized())
        self.assertNotIn("normalized", skel.to_dict())

    def test_normalized_carries_state(self):
        skel = Skeleton(100, 100)
        skel.set(Joint("pelvis", 50, 90, 0.9, OBSERVED))
        skel.set(Joint("neck", 50, 40, 0.9, OBSERVED))
        skel.set(Joint("wrist_l", 10, 60, 0.3, PREDICTED,
                       "prior off wrist"))
        norm = skel.normalized()
        self.assertEqual(norm["joints"]["wrist_l"]["state"], PREDICTED)
        self.assertEqual(norm["joints"]["pelvis"]["state"], OBSERVED)


if __name__ == "__main__":
    unittest.main()
