import unittest

from tests import synthetic_person

from slice import grid
from slice.bitmap import Bitmap


def _rect(w, h, box, color=(200, 200, 200, 255)):
    b = Bitmap.new(w, h, (0, 0, 0, 255))
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            b.set(x, y, color)
    return b


class TestGrid(unittest.TestCase):
    def test_person_descriptor(self):
        d = grid.descriptor(synthetic_person())
        self.assertIsNotNone(d)
        self.assertEqual(len(d), grid.K * grid.K)
        self.assertGreater(max(d), 0.5)

    def test_full_square_all_ones(self):
        d = grid.descriptor(_rect(80, 80, (16, 16, 64, 64)))
        self.assertTrue(all(v == 1.0 for v in d))

    def test_same_shape_matches(self):
        a = grid.descriptor(_rect(80, 80, (10, 10, 40, 70)))
        b = grid.descriptor(_rect(160, 160, (40, 40, 140, 140)))
        self.assertLess(grid.match(a, b), 0.05)

    def test_different_far(self):
        a = grid.descriptor(synthetic_person())
        b = grid.descriptor(_rect(80, 40, (5, 10, 75, 30)))
        self.assertGreater(grid.match(a, b), 0.05)

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(grid.descriptor(b))


if __name__ == "__main__":
    unittest.main()
