"""Tests for slice.track — temporal ID across frames."""
import unittest

from slice.skeleton import Joint, Skeleton, OBSERVED, PREDICTED
from slice import track


def _skel(px, py, w=200, h=200):
    s = Skeleton(image_width=w, image_height=h)
    s.set(Joint("pelvis", px, py, 0.9, OBSERVED))
    s.set(Joint("neck", px, py - 50, 0.9, OBSERVED))
    s.centroid = (px, py)
    return s


class TestTrack(unittest.TestCase):
    def test_continuous_track(self):
        frames = [_skel(100 + i * 2, 120) for i in range(5)]
        out = track.track(frames)
        ids = {a["track_id"] for a in out}
        self.assertEqual(ids, {0})
        self.assertTrue(all(a["state"] in ("new_track", "linked")
                            for a in out))
        self.assertEqual(out[3]["jump"], round(
            2 / 50, 3))  # 2px move / 50px torso

    def test_teleport_starts_new_track(self):
        frames = [_skel(50, 120), _skel(52, 120), _skel(190, 120)]
        out = track.track(frames)
        self.assertEqual(out[2]["track_id"], 1)
        self.assertEqual(out[2]["state"], "new_track")

    def test_empty_and_reacquire(self):
        frames = [_skel(50, 120), Skeleton(image_width=200,
                                          image_height=200),
                  _skel(54, 120)]
        out = track.track(frames)
        self.assertEqual(out[1]["state"], "empty")
        self.assertIsNone(out[1]["track_id"])
        self.assertEqual(out[2]["track_id"], 0)
        self.assertEqual(out[2]["state"], "reacquired")
        self.assertEqual(out[2]["gap"], 1)

    def test_centroid_fallback_anchor(self):
        s = Skeleton(image_width=200, image_height=200)
        s.set(Joint("head", 100, 30, 0.9, OBSERVED))
        s.set(Joint("ankle_l", 100, 190, 0.9, OBSERVED))
        s.centroid = (100, 100)
        out = track.track([s, s])
        self.assertEqual(out[1]["track_id"], 0)
        self.assertEqual(out[1]["anchor"], (100, 100))

    def test_predicted_pelvis_not_anchor(self):
        # a prior-placed pelvis must not anchor the track —
        # the link distance would be computed on a guess
        s = _skel(100, 120)
        p = s.joints["pelvis"]
        s.set(Joint("pelvis", p.x + 500, p.y, 0.5, PREDICTED))
        s.centroid = (100, 120)
        out = track.track([s])
        self.assertEqual(out[0]["anchor"], (100, 120))

    def test_predicted_torso_not_normaliser(self):
        # predicted neck/pelvis must not scale the jump metric —
        # and the frame's height must not pretend to be a torso
        # either: only a pelvis is observed, so nothing measurable
        # gives a scale and the torso abstains
        s = _skel(100, 120)
        s.joints["neck"].state = PREDICTED
        self.assertIsNone(track._torso(s))

    def test_unmeasurable_scale_does_not_link(self):
        # with no measured scale the jump cannot be expressed in
        # torso units — the link is unverifiable, so each frame
        # starts a new track rather than fabricating continuity
        s = _skel(100, 120)
        s.joints["neck"].state = PREDICTED
        s2 = _skel(103, 120)
        s2.joints["neck"].state = PREDICTED
        out = track.track([s, s2])
        self.assertEqual(out[1]["track_id"], 1)
        self.assertEqual(out[1]["state"], "new_track")

    def test_span_fallback_normaliser(self):
        # torso unmeasured but a body span is: scale the jump by the
        # measured span times the prior torso fraction, not by the
        # frame height
        s = Skeleton(image_width=200, image_height=200)
        s.set(Joint("head", 100, 20, 0.9, OBSERVED))
        s.set(Joint("pelvis", 100, 120, 0.9, OBSERVED))
        s.set(Joint("ankle_l", 100, 220, 0.9, OBSERVED))
        self.assertAlmostEqual(track._torso(s), 200 * 0.30)

    def test_summarize(self):
        frames = ([_skel(50 + i, 120) for i in range(3)]
                  + [Skeleton(image_width=200, image_height=200)]
                  + [_skel(60 + i, 120) for i in range(3)])
        sm = track.summarize(track.track(frames))
        self.assertEqual(sm["tracks"], 1)
        self.assertEqual(sm["empty_frames"], 1)
        self.assertEqual(sm["occupancy"], {"0": 6})
        self.assertEqual(sm["longest_run"], 3)


if __name__ == "__main__":
    unittest.main()
