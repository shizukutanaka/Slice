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
