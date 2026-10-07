import unittest

from tests import synthetic_person

from slice import classify
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Joint, Skeleton


def sk(**joints):
    s = Skeleton(400, 400)
    for n, xy in joints.items():
        s.set(Joint(n, xy[0], xy[1], 0.8))
    return s


class TestClassify(unittest.TestCase):
    def test_synthetic_stands(self):
        s = HeuristicPoseEstimator().estimate(synthetic_person())
        r = classify.analyze(s)
        self.assertEqual(r["pose"], "stand")
        self.assertEqual(r["label"], "立つ")
        self.assertGreater(r["confidence"], 0.3)

    def test_predicted_geometry_no_label(self):
        # predicted legs are priors, not evidence — no pose claim
        s = sk(head=(100, 30))
        s.set(Joint("ankle_l", 90, 300, 0.3, state="predicted"))
        s.set(Joint("ankle_r", 110, 300, 0.3, state="predicted"))
        self.assertEqual(classify.analyze(s)["pose"], "unknown")

    def test_lie_horizontal(self):
        s = sk(head=(30, 100), neck=(60, 100), chest=(110, 100),
               pelvis=(170, 100), hip_l=(170, 90), hip_r=(170, 110),
               knee_l=(240, 90), knee_r=(240, 110),
               ankle_l=(310, 90), ankle_r=(310, 110))
        self.assertEqual(classify.analyze(s)["pose"], "lie")

    def test_sit_thighs_horizontal(self):
        s = sk(head=(100, 30), neck=(100, 80), chest=(100, 160),
               pelvis=(100, 240), hip_l=(85, 245), hip_r=(115, 245),
               knee_l=(45, 248), knee_r=(155, 248),
               ankle_l=(45, 330), ankle_r=(155, 330))
        self.assertEqual(classify.analyze(s)["pose"], "sit")

    def test_crouch_folded_legs(self):
        s = sk(head=(100, 60), neck=(100, 110), chest=(100, 180),
               pelvis=(100, 260), hip_l=(85, 265), hip_r=(115, 265),
               knee_l=(35, 245), knee_r=(165, 245),
               ankle_l=(60, 340), ankle_r=(140, 340))
        self.assertEqual(classify.analyze(s)["pose"], "crouch")

    def test_bend_tilted_torso(self):
        # upright legs, torso leaning forward (お辞儀)
        s = sk(head=(205, 30), neck=(165, 60), chest=(130, 120),
               pelvis=(100, 180), hip_l=(85, 185), hip_r=(115, 185),
               knee_l=(85, 270), knee_r=(115, 270),
               ankle_l=(85, 355), ankle_r=(115, 355))
        self.assertEqual(classify.analyze(s)["pose"], "bend")

    def test_walk_ankles_apart(self):
        s = sk(head=(100, 30), neck=(100, 80), chest=(100, 160),
               pelvis=(100, 200), hip_l=(85, 205), hip_r=(115, 205),
               knee_l=(75, 290), knee_r=(125, 295),
               ankle_l=(45, 375), ankle_r=(155, 375))
        self.assertEqual(classify.analyze(s)["pose"], "walk")

    def test_run_knee_lifted(self):
        s = sk(head=(100, 30), neck=(100, 80), chest=(100, 160),
               pelvis=(100, 200), hip_l=(85, 205), hip_r=(115, 205),
               knee_l=(75, 290), knee_r=(140, 140),
               ankle_l=(45, 375), ankle_r=(160, 375))
        self.assertEqual(classify.analyze(s)["pose"], "run")

    def test_unknown_empty(self):
        r = classify.analyze(Skeleton(10, 10))
        self.assertEqual(r["pose"], "unknown")
        self.assertEqual(r["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
