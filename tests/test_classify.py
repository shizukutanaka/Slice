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

    def test_arms_up(self):
        s = sk(head=(100, 30), neck=(100, 80), chest=(100, 160),
               pelvis=(100, 200), hip_l=(85, 205), hip_r=(115, 205),
               knee_l=(80, 290), knee_r=(120, 290),
               ankle_l=(80, 380), ankle_r=(120, 380),
               shoulder_l=(70, 90), shoulder_r=(130, 90),
               wrist_l=(70, 20), wrist_r=(130, 20))
        self.assertEqual(classify.analyze(s)["pose"], "arms_up")

    def test_t_pose(self):
        s = sk(head=(100, 30), neck=(100, 80), chest=(100, 160),
               pelvis=(100, 200), hip_l=(85, 205), hip_r=(115, 205),
               knee_l=(80, 290), knee_r=(120, 290),
               ankle_l=(80, 380), ankle_r=(120, 380),
               shoulder_l=(70, 90), shoulder_r=(130, 90),
               wrist_l=(10, 92), wrist_r=(190, 88))
        self.assertEqual(classify.analyze(s)["pose"], "t_pose")

    def test_arm_pose_needs_observed_wrists(self):
        s = sk(head=(100, 30), neck=(100, 80), chest=(100, 160),
               pelvis=(100, 200), hip_l=(85, 205), hip_r=(115, 205),
               knee_l=(80, 290), knee_r=(120, 290),
               ankle_l=(80, 380), ankle_r=(120, 380))
        self.assertEqual(classify.analyze(s)["pose"], "stand")

    def test_unknown_empty(self):
        r = classify.analyze(Skeleton(10, 10))
        self.assertEqual(r["pose"], "unknown")
        self.assertEqual(r["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
