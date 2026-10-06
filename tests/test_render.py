import unittest

from slice import render
from slice.skeleton import Joint, Skeleton


class TestRender(unittest.TestCase):
    def test_overlay_draws_bones(self):
        # observed -> blue, predicted -> orange
        sk = Skeleton(100, 200)
        sk.set(Joint("shoulder_l", 30, 60, 0.8))
        sk.set(Joint("elbow_l", 20, 100, 0.8))
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

    def test_facing_arrow(self):
        sk = Skeleton(100, 200)
        sk.set(Joint("head", 50, 30, 0.8))
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
