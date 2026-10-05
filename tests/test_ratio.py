import unittest

from tests import synthetic_person

from slice import ratio
from slice.pose import HeuristicPoseEstimator


class TestRatio(unittest.TestCase):
    def test_ratios_present_and_sane(self):
        sk = HeuristicPoseEstimator().estimate(synthetic_person())
        r = ratio.analyze(sk, centroid=sk.centroid)
        self.assertNotIn("error", r)
        self.assertGreater(r["head_to_body"], 2)
        self.assertLess(r["head_to_body"], 20)
        for k in ("shoulder_width", "hip_width", "torso_length"):
            self.assertIsNotNone(r[k], k)
        self.assertIsNotNone(r["center_of_mass"])
        self.assertTrue(0 < r["center_of_mass"]["y_ratio"] < 1)

    def test_empty_skeleton(self):
        from slice.skeleton import Skeleton
        self.assertIn("error", ratio.analyze(Skeleton(10, 10)))

    @staticmethod
    def _skel(sw, hw):
        from slice.skeleton import Joint, OBSERVED, Skeleton
        s = Skeleton(100, 300)
        s.set(Joint("head", 50, 15, .9, OBSERVED, "t"))
        s.set(Joint("neck", 50, 45, .9, OBSERVED, "t"))
        s.set(Joint("pelvis", 50, 160, .9, OBSERVED, "t"))
        s.set(Joint("shoulder_l", 50 - sw / 2, 60, .9, OBSERVED, "t"))
        s.set(Joint("shoulder_r", 50 + sw / 2, 60, .9, OBSERVED, "t"))
        s.set(Joint("hip_l", 50 - hw / 2, 170, .9, OBSERVED, "t"))
        s.set(Joint("hip_r", 50 + hw / 2, 170, .9, OBSERVED, "t"))
        s.set(Joint("ankle_l", 45, 290, .9, OBSERVED, "t"))
        s.set(Joint("ankle_r", 55, 290, .9, OBSERVED, "t"))
        s.set(Joint("foot_l", 42, 298, .9, OBSERVED, "t"))
        s.set(Joint("foot_r", 58, 298, .9, OBSERVED, "t"))
        return s

    def test_gender_cue(self):
        m = ratio.analyze(self._skel(sw=40, hw=30))["gender_cue"]
        self.assertEqual(m["cue"], "masculine")
        f = ratio.analyze(self._skel(sw=28, hw=32))["gender_cue"]
        self.assertEqual(f["cue"], "feminine")
        a = ratio.analyze(self._skel(sw=32, hw=31))["gender_cue"]
        self.assertEqual(a["cue"], "androgynous")
        self.assertLessEqual(a["confidence"], 0.7)
        self.assertEqual(a["state"], "estimated")

    def test_gender_cue_skipped_when_predicted(self):
        s = self._skel(sw=40, hw=30)
        s.joints["hip_l"].state = "predicted"
        self.assertNotIn("gender_cue", ratio.analyze(s))


if __name__ == "__main__":
    unittest.main()
