import unittest

from tests import synthetic_person

from slice import bitmap, render
from slice.bitmap import Bitmap, PNG_MAGIC
from slice.pose import HeuristicPoseEstimator
from slice.skeleton import Joint, OBSERVED, Skeleton


class TestRender(unittest.TestCase):
    def test_overlay_png_roundtrip(self):
        bmp = synthetic_person(200, 360)
        skel = HeuristicPoseEstimator().estimate(bmp)
        png = render.overlay_png(bmp, skel)
        self.assertTrue(png.startswith(PNG_MAGIC))
        back = bitmap.decode(png)
        self.assertEqual((back.width, back.height), (200, 360))

    def test_joint_radius_scales_with_confidence(self):
        def blob_at(conf):
            s = Skeleton(100, 100)
            s.set(Joint("head", 50, 20, conf, OBSERVED, "t"))
            return render.overlay(Bitmap.new(100, 100, (0, 0, 0, 255)), s)

        def colored(bmp):
            return sum(1 for y in range(bmp.height)
                       for x in range(bmp.width) if bmp.get(x, y)[:3] != (0, 0, 0))

        self.assertGreater(colored(blob_at(0.9)), colored(blob_at(0.3)))

    def test_low_confidence_bone_is_dashed(self):
        def bone_pixels(conf):
            s = Skeleton(100, 100)
            s.set(Joint("shoulder_l", 10, 50, 0.9, OBSERVED, "t"))
            s.set(Joint("elbow_l", 90, 50, conf, OBSERVED, "t"))
            ov = render.overlay(Bitmap.new(100, 100, (0, 0, 0, 255)), s)
            # count non-black pixels strictly between the joint blobs
            return sum(1 for x in range(15, 85)
                       for y in range(47, 54) if ov.get(x, y)[:3] != (0, 0, 0))

        solid = bone_pixels(0.9)
        dashed = bone_pixels(0.3)
        self.assertLess(dashed, solid)


if __name__ == "__main__":
    unittest.main()
import unittest

from slice import render
from slice.skeleton import Joint, OBSERVED, Skeleton


class TestRender(unittest.TestCase):
    def test_overlay_draws_bones(self):
        # observed -> blue, predicted -> orange
        sk = Skeleton(100, 200)
        sk.set(Joint("shoulder_l", 30, 60, 0.8, OBSERVED))
        sk.set(Joint("elbow_l", 20, 100, 0.8, OBSERVED))
        sk.set(Joint("elbow_r", 80, 100, 0.3, "predicted", "prior"))
        from slice.bitmap import Bitmap
        out = render.overlay(
            Bitmap.new(100, 200, (255, 255, 255, 255)), sk)
        # some pixel somewhere was painted blue or orange
        blue = orange = 0
        for i in range(0, len(out.data), 4):
            r, g, b, a = out.data[i:i + 4]
            if a == 255 and (r, g, b) == (30, 120, 255):
                blue += 1
            elif a == 255 and (r, g, b) == (255, 150, 0):
                orange += 1
        self.assertGreater(blue, 0)
        self.assertGreater(orange, 0)

    def test_state_dual_encoded_in_shape(self):
        # colour-blind check: predicted joints are hollow rings
        # (centre stays background) while observed are filled discs;
        # predicted bones are dashed (gaps along the segment).
        from slice.bitmap import Bitmap
        sk = Skeleton(200, 200)
        sk.set(Joint("chest", 50, 50, 0.9, OBSERVED))                      # observed
        sk.set(Joint("pelvis", 50, 90, 0.9, OBSERVED))                     # observed
        sk.set(Joint("wrist_l", 150, 50, 0.3, "predicted", "prior"))
        out = render.overlay(
            Bitmap.new(200, 200, (255, 255, 255, 255)), sk)

        def px(x, y):
            i = (y * 200 + x) * 4
            return tuple(out.data[i:i + 4])

        # observed disc is filled (centre has the white core dot,
        # but the disc body around it is solid blue)
        self.assertEqual(px(52, 50), (30, 120, 255, 255))
        self.assertEqual(px(150, 50), (255, 255, 255, 255))  # hollow
        # orange ring exists somewhere around the predicted joint
        ring = any(px(x, 50) == (255, 150, 0, 255)
                   for x in range(146, 155))
        self.assertTrue(ring)

        # a predicted bone leaves gaps: count blue/orange pixels on the
        # chest->pelvis line (observed, solid) — every y is painted
        bone_col = [px(50, y) for y in range(52, 89)]
        painted = sum(1 for p in bone_col if p != (255, 255, 255, 255))
        self.assertEqual(painted, len(bone_col))

    def test_dashed_bone_has_gaps(self):
        from slice.bitmap import Bitmap
        sk = Skeleton(200, 200)
        sk.set(Joint("pelvis", 100, 100, 0.9, OBSERVED))
        sk.set(Joint("hip_l", 30, 100, 0.2, "predicted", "prior"))
        out = render.overlay(
            Bitmap.new(200, 200, (255, 255, 255, 255)), sk)

        def px(x, y):
            i = (y * 200 + x) * 4
            return tuple(out.data[i:i + 4])

        row = [px(x, 100) for x in range(35, 95)]
        gaps = sum(1 for p in row if p == (255, 255, 255, 255))
        self.assertGreater(gaps, 3)   # dashes skip segments
        oranges = sum(1 for p in row if p == (255, 150, 0, 255))
        self.assertGreater(oranges, 10)

    def test_facing_arrow(self):
        sk = Skeleton(100, 200)
        sk.set(Joint("head", 50, 30, 0.8, OBSERVED))
        sk.orientation = {"facing": "left", "confidence": 0.5}
        from slice.bitmap import Bitmap
        bmp = render.overlay(
            Bitmap.new(100, 200, (255, 255, 255, 255)), sk)
        green = 0
        for i in range(0, len(bmp.data), 4):
            if tuple(bmp.data[i:i + 4]) == render.GREEN:
                green += 1
        self.assertGreater(green, 10, "facing arrow should be drawn")


if __name__ == "__main__":
    unittest.main()
