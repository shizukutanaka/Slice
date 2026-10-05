import unittest

from tests import synthetic_person

from slice import hu
from slice.bitmap import Bitmap


def _shape(w, h, box, color=(200, 200, 200, 255)):
    b = Bitmap.new(w, h, (0, 0, 0, 255))
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            b.set(x, y, color)
    return b


class TestHu(unittest.TestCase):
    def test_scale_invariant(self):
        a = hu.moments(_shape(100, 100, (20, 20, 60, 60)))
        b = hu.moments(_shape(200, 200, (40, 40, 120, 120)))
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertLess(hu.match(a, b), 0.1)

    def test_translation_invariant(self):
        a = hu.moments(_shape(100, 100, (10, 10, 30, 50)))
        b = hu.moments(_shape(100, 100, (60, 40, 80, 80)))
        self.assertLess(hu.match(a, b), 0.1)

    def test_different_shape_far(self):
        a = hu.moments(synthetic_person())
        b = hu.moments(_shape(100, 60, (10, 20, 90, 40)))
        self.assertGreater(hu.match(a, b), 0.05)

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(hu.moments(b))

    def test_seven_values(self):
        self.assertEqual(len(hu.moments(synthetic_person())), 7)


if __name__ == "__main__":
    unittest.main()
