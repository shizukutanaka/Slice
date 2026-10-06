import unittest

from tests import synthetic_person

from slice import mass
from slice.pose import HeuristicPoseEstimator


class TestMass(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_adult_mass_plausible(self):
        m = mass.estimate(self.skel, area_px=9000)
        self.assertEqual(m["state"], "estimated")
        self.assertGreater(m["kg"], 5)
        self.assertLess(m["kg"], 200)
        self.assertGreater(m["depth_cm"], 0)

    def test_zero_area_none(self):
        self.assertIsNone(mass.estimate(self.skel, 0))

    def test_no_body_none(self):
        for n in list(self.skel.joints):
            del self.skel.joints[n]
        self.assertIsNone(mass.estimate(self.skel, 9000))

    def test_bmi_shape(self):
        b = mass.bmi(self.skel, 9000)
        self.assertIsNotNone(b)
        self.assertGreater(b, 5)


if __name__ == "__main__":
    unittest.main()
