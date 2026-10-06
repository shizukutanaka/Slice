import unittest

from tests import synthetic_person

from slice import contact
from slice.pose import HeuristicPoseEstimator


class TestContact(unittest.TestCase):
    def setUp(self):
        self.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_standing_hands_apart_no_contact(self):
        names = [c["contact"] for c in contact.detect(self.skel)]
        self.assertNotIn("hands_together", names)
        self.assertNotIn("hand_at_head", names)

    def test_hands_together(self):
        wl, wr = self.skel.joints["wrist_l"], self.skel.joints["wrist_r"]
        mx = (wl.x + wr.x) / 2
        my = (wl.y + wr.y) / 2
        wl.x, wl.y, wr.x, wr.y = mx - 5, my, mx + 5, my
        names = [c["contact"] for c in contact.detect(self.skel)]
        self.assertIn("hands_together", names)

    def test_arms_crossed(self):
        wr = self.skel.joints["wrist_r"]
        el = self.skel.joints["elbow_l"]
        wr.x, wr.y = el.x, el.y  # right hand on left elbow
        names = [c["contact"] for c in contact.detect(self.skel)]
        self.assertIn("arms_crossed", names)

    def test_predicted_joint_never_contacts(self):
        wr = self.skel.joints["wrist_r"]
        el = self.skel.joints["elbow_l"]
        wr.x, wr.y = el.x, el.y
        wr.state = "predicted"
        self.assertNotIn("arms_crossed",
                         [c["contact"] for c in contact.detect(self.skel)])

    def test_summary_shape(self):
        s = contact.summary(self.skel)
        self.assertIsInstance(s["count"], int)


if __name__ == "__main__":
    unittest.main()
