import unittest

from tests import (crouch_person, raised_arms_person,
                   synthetic_person, wide_hand_person)

from slice.anatomy import BODY_MODELS
from slice.bitmap import Bitmap
from slice.pose import (HeuristicPoseEstimator, _arm_candidates,
                        _classify_orientation, _estimate_arm_ends,
                        _estimate_head, _estimate_legs,
                        _estimate_pelvis_column, _estimate_shoulder_line,
                        _estimate_torso_column, _symmetry)
from slice.skeleton import Joint, NECK_CLAVICLE_BASIS, OBSERVED


class TestArmCandidates(unittest.TestCase):
    def test_candidates_stay_on_requested_side(self):
        comp = [bytearray(12) for _ in range(8)]
        for y in range(8):
            for x in range(7, 10):
                comp[y][x] = 1
        for x in range(2, 5):
            comp[2][x] = 1

        left = _arm_candidates(comp, 12, -1, 7, 8, 1, 4, 7)
        right = _arm_candidates(comp, 12, 1, 9, 8, 1, 4, 7)

        self.assertEqual(left, [(2, 2), (3, 2), (4, 2)])
        self.assertEqual(right, [])

    def test_dangling_hand_is_kept_and_grounded_legs_are_excluded(self):
        comp = [bytearray(18) for _ in range(10)]
        for y in range(10):
            comp[y][9] = comp[y][10] = 1
        for y in range(5, 10):
            for x in (6, 7, 12, 13):
                comp[y][x] = 1
        for y in (2, 5, 6, 7):
            for x in range(2, 5):
                comp[y][x] = 1

        cand = _arm_candidates(comp, 18, -1, 9, 10, 1, 4, 9)
        expected = ([(x, 2) for x in range(2, 5)]
                    + [(x, y) for y in range(5, 8)
                       for x in range(2, 5)])

        self.assertEqual(cand, expected)
        self.assertNotIn((6, 5), cand)
        self.assertNotIn((12, 5), cand)

    def test_no_protrusion_returns_empty(self):
        comp = [bytearray(12) for _ in range(8)]
        for row in comp:
            for x in range(5, 8):
                row[x] = 1

        self.assertEqual(_arm_candidates(comp, 12, -1, 5, 6, 1, 4, 7),
                         [])


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


class TestOrientationClassifier(unittest.TestCase):
    def test_profile_head_shift_sets_facing(self):
        comp = [bytearray(20) for _ in range(20)]
        for row in comp[10:]:
            for x in range(9, 11):
                row[x] = 1
        rows = [None] * 20
        rows[0] = (2, 4, 3)
        sym = _symmetry(comp, 20, 10, 19, 10)
        orientation = _classify_orientation(
            comp, 20, rows, 0, 2, 20, 3, 4, False,
            (9, 11), (9, 10), 10, 19, 10, sym)
        self.assertEqual(orientation["facing"], "left")
        self.assertLess(orientation["head_shift"], 0)


class TestEstimateLegs(unittest.TestCase):
    def test_split_legs_anchor_to_foot_runs(self):
        comp = [bytearray(20) for _ in range(20)]
        # two leg columns reaching the bottom row
        for y in range(10, 20):
            for x in (4, 5, 14, 15):
                comp[y][x] = 1
        legs_split, joints = _estimate_legs(comp, 20, 20, 10, 19,
                                            (9, 10))
        names = [j[0] for j in joints]
        self.assertTrue(legs_split)
        self.assertEqual(names, ["knee_l", "ankle_l", "foot_l",
                                 "knee_r", "ankle_r", "foot_r"])
        self.assertEqual(joints[0][3:], (0.7, "leg run at knee height"))

    def test_merged_legs_fall_back_to_hip_run_knees(self):
        comp = [bytearray(20) for _ in range(20)]
        for y in range(10, 20):
            for x in range(8, 12):
                comp[y][x] = 1
        legs_split, joints = _estimate_legs(comp, 20, 20, 10, 19,
                                            (8, 11))
        names = [j[0] for j in joints]
        self.assertFalse(legs_split)
        self.assertEqual(names, ["ankle_l", "foot_l",
                                 "ankle_r", "foot_r",
                                 "knee_l", "knee_r"])
        knee_l = next(j for j in joints if j[0] == "knee_l")
        self.assertEqual(knee_l[3:], (0.3, "legs not separable"))


class TestEstimateArmEnds(unittest.TestCase):
    def _comp(self):
        comp = [bytearray(20) for _ in range(20)]
        for y in range(20):  # torso column
            for x in (9, 10, 11):
                comp[y][x] = 1
        for y in range(4, 9):  # left arm hanging beside torso
            for x in range(4, 7):
                comp[y][x] = 1
        return comp

    def _call(self, **kw):
        args = dict(comp=self._comp(), w=20, top=0, head_h=4, crotch=10,
                    bottom=19, torso_run=(9, 11), cx_spine=10,
                    shoulders={"l": Joint("shoulder_l", 9, 8, 0.8,
                                          OBSERVED, "test")},
                    horizontal_arms=set(), prior=BODY_MODELS["adult"],
                    body_h=20)
        args.update(kw)
        return _estimate_arm_ends(**args)

    def test_arm_candidates_produce_wrist_and_elbow(self):
        joints = self._call()
        self.assertEqual([j[0] for j in joints],
                         ["wrist_l", "elbow_l"])
        self.assertEqual(joints[0][4], "arm blob extremity")
        self.assertEqual(joints[1][4], "arm blob mid-extent")
        self.assertLess(joints[1][3], joints[0][3])

    def test_horizontal_arm_side_is_skipped(self):
        self.assertEqual(self._call(horizontal_arms={"l"}), [])

    def test_missing_shoulder_skips_side(self):
        self.assertEqual(self._call(shoulders={}), [])


class TestEstimateTorsoColumn(unittest.TestCase):
    def _comp_row(self, row=8, spans=((9, 11),)):
        comp = [bytearray(20) for _ in range(20)]
        for a, b in spans:
            for x in range(a, b + 1):
                comp[row][x] = 1
        return comp

    def test_wide_shoulder_row_splits_into_tpose_strips(self):
        torso_run, cx, arms, joints = _estimate_torso_column(
            self._comp_row(), 20, top=0, body_h=20, sh_row=5,
            sr=(2, 17, 15))
        self.assertEqual((torso_run, cx), ((9, 11), 9.5))
        self.assertEqual(arms, {"l", "r"})
        self.assertEqual([j[0] for j in joints],
                         ["shoulder_l", "elbow_l", "wrist_l",
                          "shoulder_r", "elbow_r", "wrist_r"])
        self.assertEqual(joints[2][1:3], (2, 5))  # wrist at strip tip
        self.assertEqual(joints[1][1:3], (5.5, 5))  # elbow midpoint

    def test_narrow_shoulder_row_is_not_tpose(self):
        torso_run, cx, arms, joints = _estimate_torso_column(
            self._comp_row(), 20, top=0, body_h=20, sh_row=5,
            sr=(8, 11, 4))
        self.assertEqual((torso_run, cx), ((9, 11), 9.5))
        self.assertEqual(arms, set())
        self.assertEqual(joints, [])

    def test_torso_run_falls_back_to_shoulder_span(self):
        comp = self._comp_row(spans=((2, 4), (14, 17)))  # no spine run
        torso_run, cx, arms, joints = _estimate_torso_column(
            comp, 20, top=0, body_h=20, sh_row=5, sr=(8, 11, 4))
        self.assertEqual(torso_run, (8, 11))
        self.assertEqual(cx, 9.5)
        self.assertEqual(joints, [])


class TestEstimatePelvisColumn(unittest.TestCase):
    def _comp(self, rowmap):
        comp = [bytearray(20) for _ in range(20)]
        for y, spans in rowmap.items():
            for a, b in spans:
                for x in range(a, b + 1):
                    comp[y][x] = 1
        return comp

    def _rows(self):
        rows = [None] * 20
        for y in range(5, 16):
            rows[y] = (9, 11, 3)
        return rows

    def _call(self, rowmap, crotch_row, widest_row):
        return _estimate_pelvis_column(
            self._comp(rowmap), 20, self._rows(), top=0, body_h=20,
            head_h=4, sh_row=5, neck_y=7, torso_run=(9, 11),
            cx_spine=10, crotch_row=crotch_row, widest_row=widest_row)

    def test_crotch_split_branch(self):
        crotch, hr, joints = self._call(
            {11: [(9, 11)], 9: [(9, 11)]},
            lambda comp, w, y0, y1, torso: 12,
            lambda rows, y0, y1: 13)
        self.assertEqual(crotch, 12)
        self.assertEqual(hr, (9, 11))
        self.assertEqual([j[0] for j in joints],
                         ["pelvis", "hip_l", "hip_r", "chest", "spine"])
        self.assertEqual(joints[0], ("pelvis", 10.0, 11, 0.75,
                                     "crotch split row"))
        self.assertEqual(joints[1][3:], (0.75, "crotch split row"))
        self.assertEqual(joints[2][1:3], (11, 11))
        self.assertEqual(joints[3], ("chest", 10.0, 8.0, 0.65,
                                     "midpoint shoulders-pelvis"))
        self.assertEqual(joints[4], ("spine", 10.0, 9.0, 0.6,
                                     "axis midpoint"))

    def test_crotch_none_falls_back_to_widest_row(self):
        crotch, hr, joints = self._call(
            {13: [(8, 12)], 10: [(9, 11)]},
            lambda *a: None,
            lambda rows, y0, y1: 13)
        self.assertEqual(crotch, 15)  # 13 + max(2, int(4*0.4))
        self.assertEqual(hr, (8, 12))
        self.assertEqual(joints[0], ("pelvis", 10.0, 13, 0.55,
                                     "widest hip-band row"))
        self.assertEqual(joints[3][2], 9.0)   # chest_y
        self.assertEqual(joints[4][2], 10.0)  # spine_y

    def test_measurement_bands_match_caller_math(self):
        seen = []

        def crotch_row(comp, w, y0, y1, torso):
            seen.append(("crotch", y0, y1, torso))
            return 12

        def widest_row(rows, y0, y1):
            seen.append(("widest", y0, y1))
            return 13

        self._call({11: [(9, 11)]}, crotch_row, widest_row)
        self.assertEqual(seen, [("crotch", 9, 14, (9, 11))])

    def test_widest_row_called_only_on_fallback(self):
        seen = []
        self._call({11: [(9, 11)], 9: [(9, 11)]},
                   lambda comp, w, y0, y1, torso: 12,
                   lambda rows, y0, y1: seen.append((y0, y1)) or 13)
        self.assertEqual(seen, [])  # crotch split: no fallback scan


class TestEstimateHead(unittest.TestCase):
    def _rows(self, fill=None):
        rows = [None] * 50
        if fill:
            for y in fill:
                rows[y] = (40, 50, 11)
        return rows

    def test_band_centroid_and_ratio_stats(self):
        cx, hn, hx1, joints = _estimate_head(
            self._rows(range(0, 7)), 0, 49, head_h=6.0, left=30, right=70)
        self.assertEqual(cx, 45.0)
        self.assertEqual((hn, hx1), (77, 6))
        self.assertEqual(joints, [("head", 45.0, 3.0, 0.85,
                                   "top blob centroid")])

    def test_empty_band_falls_back_to_bbox_centre(self):
        cx, hn, hx1, joints = _estimate_head(
            self._rows(), 0, 49, head_h=6.0, left=30, right=70)
        self.assertEqual((cx, hn, hx1), (50.0, 0, 0))
        self.assertEqual(joints[0][1:3], (50.0, 3.0))


class TestEstimateShoulderLine(unittest.TestCase):
    def _rows(self, row=None):
        rows = [None] * 40
        if row is not None:
            rows[8] = row
        return rows

    def _call(self, row_val, recorder=None):
        calls = recorder if recorder is not None else []

        def widest_row(rows, y0, y1):
            calls.append((y0, y1))
            return 8

        return _estimate_shoulder_line(
            self._rows(row_val), 0, body_h=40, body_w=24, head_h=6.0,
            left=30, right=70, widest_row=widest_row), calls

    def test_widest_row_band_and_joint_order(self):
        (sh_row, sr, neck_y, joints), calls = self._call((30, 50, 20))
        self.assertEqual((sh_row, sr, neck_y), (8, (30, 50, 20), 10))
        self.assertEqual(calls, [(6, 14)])  # int(head_h) .. 0.35*body_h
        self.assertEqual([j[0] for j in joints],
                         ["shoulder_l", "shoulder_r", "neck"])
        self.assertEqual(joints[0], ("shoulder_l", 30, 8, 0.8,
                                     "widest upper row"))
        self.assertEqual(joints[1][1:3], (50, 8))
        self.assertEqual(joints[2], ("neck", 40.0, 10, 0.7,
                                     NECK_CLAVICLE_BASIS))

    def test_missing_row_falls_back_to_bbox_span(self):
        (_, sr, _, joints), _ = self._call(None)
        self.assertEqual(sr, (30, 70, 24))  # (left, right, body_w)
        self.assertEqual(joints[1][1], 70)


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

    def test_tpose_horizontal_arms(self):
        """Arms spread horizontally (T-pose): shoulders sit at the torso
        edge (not the arm tips), elbow at strip midpoint, wrist at the
        strip tip."""
        from slice.evaluate import draw_case
        bmp, truth = draw_case(width=320, height=240, pose="t")
        skel = HeuristicPoseEstimator().estimate(bmp)
        j = skel.joints
        for side in ("l", "r"):
            for name in ("shoulder", "elbow", "wrist"):
                self.assertEqual(j[f"{name}_{side}"].state, OBSERVED,
                                 f"{name}_{side}")
            self.assertLess(
                abs(j[f"shoulder_{side}"].x
                    - truth[f"shoulder_{side}"][0]), 8,
                f"shoulder_{side} must sit at the torso edge")
            self.assertLess(
                abs(j[f"wrist_{side}"].x - truth[f"wrist_{side}"][0]), 8,
                f"wrist_{side} must reach the strip tip")

    def test_raised_arms_detected(self):
        """V-pose: arms above the shoulder line must still surface —
        the scan starts below the head band, not at the shoulder row."""
        skel = HeuristicPoseEstimator().estimate(raised_arms_person())
        j = skel.joints
        for side in ("l", "r"):
            self.assertEqual(j[f"wrist_{side}"].state, OBSERVED, side)
            self.assertEqual(j[f"elbow_{side}"].state, OBSERVED, side)
            # raised wrist sits above the shoulder row, not dangling
            self.assertLess(j[f"wrist_{side}"].y,
                            j[f"shoulder_{side}"].y, side)
            if side == "l":
                self.assertLess(j["wrist_l"].x, j["shoulder_l"].x)
            else:
                self.assertGreater(j["wrist_r"].x, j["shoulder_r"].x)

    def test_asymmetric_raised_arm_partial_detection(self):
        """One arm raised, other dangling: raised side detected above
        the shoulder row and the dangling side stays detected."""
        bmp = synthetic_person()
        w, h = bmp.width, bmp.height
        cx = w // 2
        tw = w * 0.34
        sh_y = h * 0.22
        bg = bmp.get(1, 1)
        skin = bmp.get(cx, int(sh_y) + 2)
        for y in range(int(sh_y) + 6, int(h * 0.75)):
            for x in range(int(cx - tw / 2 - 10), int(cx - tw / 2 - 2)):
                bmp.set(x, y, bg)
        tip_y = w * 0.11 + 12
        for i in range(40):
            t = i / 40
            x0 = int(cx - tw / 2 - t * (cx - tw / 2 - 14))
            y0 = int(sh_y + 6 - t * (sh_y - tip_y))
            for dy in range(6):
                for dx in range(6):
                    bmp.set(x0 + dx, y0 + dy, skin)
        j = HeuristicPoseEstimator().estimate(bmp).joints
        self.assertEqual(j["wrist_l"].state, OBSERVED)
        self.assertLess(j["wrist_l"].y, j["shoulder_l"].y)
        self.assertEqual(j["wrist_r"].state, OBSERVED)
        self.assertGreater(j["wrist_r"].y, j["shoulder_r"].y)

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

    def test_flat_lying_figure_retried_when_upright_starves(self):
        """A figure shorter than the upright 24px body-height gate
        used to return an empty skeleton with no retry at all — the
        one case the orientation retry exists for. The rotated scans
        must still run; only a clean rotated skeleton is adopted."""
        bmp = Bitmap.new(200, 60, (240, 240, 240, 255))
        for y in range(20, 40):
            for x in range(30, 170):
                bmp.set(x, y, (60, 60, 60, 255))
        j = HeuristicPoseEstimator().estimate(bmp).joints
        self.assertTrue(j)
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

    def test_rotated_retry_discloses_and_mirrors_orientation(self):
        """180°-flipped profile faces right in the image — but the
        rotated scan reads its facing in the mirrored frame ("left").
        The doc must report the image frame's facing ("right") and
        disclose the rotation itself."""
        src = profile_person(side=-1)   # faces left, upright
        w, h = src.width, src.height
        inv = Bitmap.new(w, h, src.get(1, 1))
        for y in range(h):
            for x in range(w):
                inv.set(x, y, src.get(w - 1 - x, h - 1 - y))  # true 180°
        sk = HeuristicPoseEstimator().estimate(inv)
        ori = sk.orientation
        self.assertEqual(ori.get("estimated_on_rotated_deg"), 180)
        self.assertEqual(ori.get("facing"), "right")

    def test_raised_arm_upright_not_flipped(self):
        """A raised arm made the upright scan look inconsistent
        (arms outside prior bounds), and the 180° retry used to win
        on its cleaner audit — flipping a real upright figure so its
        fabricated head landed at the bottom. Rotation now requires
        decisively stronger head-band evidence."""
        bmp = synthetic_person()
        w, h = bmp.width, bmp.height
        cx = w // 2
        tw = w * 0.34
        sh_y = h * 0.22
        bg = bmp.get(1, 1)
        skin = bmp.get(cx, int(sh_y) + 2)
        # delete the left dangling arm, paint a raised one instead
        for y in range(int(sh_y) + 6, int(h * 0.75)):
            for x in range(int(cx - tw / 2 - 10), int(cx - tw / 2 - 2)):
                bmp.set(x, y, bg)
        tip_y = w * 0.11 + 12
        for i in range(40):
            t = i / 40
            x0 = int(cx - tw / 2 - t * (cx - tw / 2 - 14))
            y0 = int(sh_y + 6 - t * (sh_y - tip_y))
            for dy in range(6):
                for dx in range(6):
                    bmp.set(x0 + dx, y0 + dy, skin)
        j = HeuristicPoseEstimator().estimate(bmp).joints
        self.assertLess(j["head"].y, h * 0.3)       # head stays up
        self.assertFalse(any(jt.basis and "rotated" in jt.basis
                             for jt in j.values()))

    def test_confidence_range(self):
        for j in self.skel.joints.values():
            self.assertTrue(0 < j.confidence <= 1)

    def test_orientation_and_model(self):
        self.assertIn(self.skel.orientation["facing"],
                      ("front", "side", "three-quarter", "left", "right"))
        self.assertEqual(self.skel.orientation["facing"], "front")
        self.assertIn(self.skel.body_model["name"],
                      ("adult", "child", "deformed"))
        # the prior actually applied to observed placement is disclosed
        self.assertIn(self.skel.body_model["prior"],
                      ("adult", "child", "deformed"))

    def test_prior_discloses_applied_model(self):
        est = HeuristicPoseEstimator()
        forced = est.estimate(synthetic_person(), model="child")
        self.assertEqual(forced.body_model["prior"], "child")
        # a bogus name falls back to the default table — and says so
        bogus = est.estimate(synthetic_person(), model="nope")
        self.assertEqual(bogus.body_model["prior"], "adult")

    def test_profile_facing_direction(self):
        est = HeuristicPoseEstimator()
        left = est.estimate(profile_person(side=-1))
        right = est.estimate(profile_person(side=1))
        self.assertEqual(left.orientation["facing"], "left")
        self.assertLess(left.orientation["head_shift"], 0)
        self.assertEqual(right.orientation["facing"], "right")
        self.assertGreater(right.orientation["head_shift"], 0)

    def test_offcenter_figure_keeps_front_facing(self):
        """Symmetry is measured around the body axis, not the image
        centre — a front-facing person framed off-centre must not
        degrade to three-quarter purely by composition."""
        src = synthetic_person(width=160, height=300)
        w, h = src.width, src.height
        bg = src.get(0, 0)
        wide = Bitmap.new(w + 120, h, bg)
        for y in range(h):
            for x in range(w):
                if src.get(x, y) != bg:
                    wide.set(x + 110, y, src.get(x, y))
        ori = HeuristicPoseEstimator().estimate(wide).orientation
        self.assertEqual(ori["facing"], "front")
        self.assertGreater(ori["symmetry"], 0.75)

    def test_symmetry_override_still_steers_facing(self):
        """A subclass overriding _symmetry must keep steering the
        facing verdict — the classifier no longer calls the module
        function directly."""
        class FlatSym(HeuristicPoseEstimator):
            def _symmetry(self, mask, w, y0, y1, cx):
                return 0.0

        sk = FlatSym().estimate(synthetic_person())
        self.assertEqual(sk.orientation["symmetry"], 0.0)
        self.assertEqual(sk.orientation["facing"], "three-quarter")

    def test_crotch_row_override_still_steers_column(self):
        """The pelvis stage receives _crotch_row bound, so a subclass
        override must still be invoked after the extraction."""
        calls = []

        class TrackCrotch(HeuristicPoseEstimator):
            def _crotch_row(self, mask, w, y0, y1, torso_runs):
                calls.append(1)
                return super()._crotch_row(mask, w, y0, y1, torso_runs)

        TrackCrotch().estimate(synthetic_person())
        self.assertTrue(calls)

    def test_widest_row_override_still_steers_line(self):
        """_widest_row is injected bound into the shoulder-line and
        pelvis stages, so a subclass override must keep firing."""
        calls = []

        class TrackWide(HeuristicPoseEstimator):
            def _widest_row(self, rows, y0, y1):
                calls.append(1)
                return super()._widest_row(rows, y0, y1)

        TrackWide().estimate(synthetic_person())
        self.assertTrue(calls)

    def test_blank_image(self):
        sk = HeuristicPoseEstimator().estimate(Bitmap.new(80, 80,
                                                          (255, 255, 255, 255)))
        self.assertFalse(sk.joints)


if __name__ == "__main__":
    unittest.main()
