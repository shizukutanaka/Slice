import unittest

from tests import synthetic_person

from slice import radial
from slice.bitmap import Bitmap


def _rect(w, h, box, color=(200, 200, 200, 255)):
    b = Bitmap.new(w, h, (0, 0, 0, 255))
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            b.set(x, y, color)
    return b


class TestRadial(unittest.TestCase):
    def test_person_signature(self):
        s = radial.signature(synthetic_person())
        self.assertIsNotNone(s)
        self.assertEqual(len(s), radial.N)
        self.assertAlmostEqual(max(s), 1.0)
        self.assertGreater(min(s), 0.0)

    def test_same_shape_matches(self):
        a = radial.signature(_rect(80, 80, (20, 10, 60, 70)))
        b = radial.signature(_rect(160, 160, (40, 20, 120, 140)))
        self.assertLess(radial.match(a, b), 0.15)

    def test_different_shape_far(self):
        a = radial.signature(synthetic_person())
        b = radial.signature(_rect(80, 40, (10, 10, 70, 30)))
        self.assertGreater(radial.match(a, b), 0.05)

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(radial.signature(b))


if __name__ == "__main__":
    unittest.main()
