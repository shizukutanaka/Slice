import unittest

from tests import synthetic_person

from slice import moments
from slice.bitmap import Bitmap


class TestMoments(unittest.TestCase):
    def test_person_vertical_eccentric(self):
        d = moments.describe(synthetic_person())
        self.assertIsNotNone(d)
        self.assertGreater(d["eccentricity"], 0.7)
        self.assertGreater(d["major_px"], d["minor_px"])
        self.assertGreater(d["area_px"], 0)

    def test_square_low_eccentricity(self):
        b = Bitmap.new(80, 80, (0, 0, 0, 255))
        for y in range(20, 60):
            for x in range(20, 60):
                b.set(x, y, (200, 200, 200, 255))
        d = moments.describe(b)
        self.assertIsNotNone(d)
        self.assertLess(d["eccentricity"], 0.2)
        self.assertEqual(d["centroid"], [39.5, 39.5])

    def test_wide_angle_horizontal(self):
        b = Bitmap.new(100, 60, (0, 0, 0, 255))
        for y in range(20, 40):
            for x in range(10, 90):
                b.set(x, y, (200, 200, 200, 255))
        d = moments.describe(b)
        self.assertLess(abs(d["angle_deg"]), 15)

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(moments.describe(b))


if __name__ == "__main__":
    unittest.main()
