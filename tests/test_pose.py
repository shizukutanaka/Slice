import unittest

from tests import crouch_person, synthetic_person, wide_hand_person

from slice.bitmap import Bitmap
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import OBSERVED


def profile_person(width=100, height=300, side=-1, bg=235, fg=60):
    """Side-view silhouette: narrow fused column, head blob leaning
    toward the faced side (side=-1 left, +1 right)."""
    bmp = Bitmap.new(width, height, (bg, bg, bg, 255))
    cx = width // 2 - side * 8
    for y in range(int(height * 0.32), height - 2):  # torso + fused legs
        for x in range(cx, cx + 12):
            bmp.set(x, y, (fg, fg, fg, 255))
    r = int(height * 0.08)
    hcx = cx + 6 + side * (r + 2)  # head center offset toward `side`
    cy = int(height * 0.12)
    for y in range(cy - r, cy + r):
        for x in range(hcx - r, hcx + r):
            if (x - hcx) ** 2 + (y - cy) ** 2 <= r * r:
                bmp.set(x, y, (fg, fg, fg, 255))
    for y in range(cy, int(height * 0.34)):  # neck bridge keeps one component
        for x in range(min(cx + 6, hcx) - 2, max(cx + 6, hcx) + 2):
            bmp.set(x, y, (fg, fg, fg, 255))
    return bmp


class TestHeuristicPose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skel = HeuristicPoseEstimator().estimate(synthetic_person())

    def test_core_joints_observed(self):
        for n in ("head", "neck", "shoulder_l", "shoulder_r",
                  "pelvis", "knee_l", "knee_r", "ankle_l", "ankle_r"):
            self.assertIn(n, self.skel.joints, n)
            self.assertEqual(self.skel.joints[n].state, OBSERVED, n)

    def test_vertical_order(self):
        j = self.skel.joints
        self.assertLess(j["head"].y, j["neck"].y)
        self.assertLess(j["neck"].y, j["pelvis"].y)
        self.assertLess(j["pelvis"].y, j["ankle_l"].y)

    def test_left_right_separation(self):
        j = self.skel.joints
        self.assertLess(j["shoulder_l"].x, j["shoulder_r"].x)
        self.assertLess(j["ankle_l"].x, j["ankle_r"].x)

    def test_dangling_wrist_below_hip(self):
        j = self.skel.joints
        for side in ("l", "r"):
            self.assertEqual(j[f"wrist_{side}"].state, OBSERVED, side)
            self.assertGreater(j[f"wrist_{side}"].y, j[f"hip_{side}"].y,
                               f"wrist_{side} should hang below the hip line")

    def test_wide_drifting_hand_tracked(self):
        """A hand wider than a leg run and drifting outward must still be
        followed: width-based leg guessing drops it, and a frozen arm
        band truncates it before the fingertips."""
        skel = HeuristicPoseEstimator().estimate(wide_hand_person())
        j = skel.joints
        self.assertEqual(j["wrist_l"].state, OBSERVED)
        self.assertGreater(j["wrist_l"].y, 300 * 0.8)
        self.assertLess(j["wrist_l"].x, 80 - 160 * 0.17 - 15)

    def test_crouch_dangling_wrist_not_amputated(self):
        """Wide flat feet used to swallow the below-crotch arm band
        (x-overlap classified arm pixels as leg), leaving the wrist
        floating at hip height."""
        skel = HeuristicPoseEstimator().estimate(crouch_person())
        j = skel.joints
        for side in ("l", "r"):
            self.assertEqual(j[f"wrist_{side}"].state, OBSERVED, side)
            # wrist reaches the arm bar's bottom (~80% height), not
            # amputated at the hip line
            self.assertGreater(j[f"wrist_{side}"].y, 300 * 0.7, side)

    def test_inverted_person_180_retry(self):
        """An upside-down figure used to yield a consistent-looking
        but fully wrong skeleton (head found where the feet are).
        The 180° orientation retry un-rotates joints into image space
        and records the rotation in the joint basis."""
        src = synthetic_person()
        w, h = src.width, src.height
        inv = Bitmap.new(w, h, src.get(1, 1))
        for y in range(h):
            for x in range(w):
                inv.set(x, y, src.get(x, h - 1 - y))
        j = HeuristicPoseEstimator().estimate(inv).joints
        self.assertEqual(j["head"].state, OBSERVED)
        self.assertGreater(j["head"].y, h * 0.7)    # head at the bottom
        self.assertGreater(j["ankle_l"].y, 0)
        self.assertLess(j["ankle_l"].y, h * 0.3)    # feet at the top
        self.assertTrue(any(jt.basis and "rotated" in jt.basis
                            for jt in j.values()))

    def test_spine_sits_on_torso_axis_not_head(self):
        """The spine joint is the mirroring axis for predictions.
        Placing it on the head centroid pulls the axis toward the
        faced side in profile — where mirrored prediction is needed
        most. It must track the torso column instead."""
        for side in (-1, 1):
            sk = HeuristicPoseEstimator().estimate(
                profile_person(side=side))
            sp = sk.joints["spine"]
            nk, pl = sk.joints["neck"], sk.joints["pelvis"]
            axis = (nk.x + pl.x) / 2
            head_x = sk.joints["head"].x
            self.assertLess(abs(sp.x - axis), abs(head_x - axis))

    def test_confidence_range(self):
        for j in self.skel.joints.values():
            self.assertTrue(0 < j.confidence <= 1)

    def test_orientation_and_model(self):
        self.assertIn(self.skel.orientation["facing"],
                      ("front", "side", "three-quarter", "left", "right"))
        self.assertEqual(self.skel.orientation["facing"], "front")
        self.assertIn(self.skel.body_model["name"],
                      ("adult", "child", "deformed"))

    def test_profile_facing_direction(self):
        est = HeuristicPoseEstimator()
        left = est.estimate(profile_person(side=-1))
        right = est.estimate(profile_person(side=1))
        self.assertEqual(left.orientation["facing"], "left")
        self.assertLess(left.orientation["head_shift"], 0)
        self.assertEqual(right.orientation["facing"], "right")
        self.assertGreater(right.orientation["head_shift"], 0)

    def test_blank_image(self):
        sk = HeuristicPoseEstimator().estimate(Bitmap.new(80, 80,
                                                          (255, 255, 255, 255)))
        self.assertFalse(sk.joints)


if __name__ == "__main__":
    unittest.main()
