import unittest

from tests import synthetic_person

from slice import medial
from slice.bitmap import Bitmap


class TestMedial(unittest.TestCase):
    def test_person_has_extremities(self):
        d = medial.analyze(synthetic_person())
        self.assertIsNotNone(d)
        # head top + at least feet/hands → several endpoints
        self.assertGreaterEqual(d["endpoints"], 3)
        # junctions like neck/crotch
        self.assertGreaterEqual(d["branchpoints"], 1)
        self.assertGreater(d["pixels"], 0)

    def test_line_two_endpoints(self):
        b = Bitmap.new(60, 60, (0, 0, 0, 255))
        for y in range(10, 50):
            for x in range(28, 32):
                b.set(x, y, (200, 200, 200, 255))
        d = medial.analyze(b)
        self.assertIsNotNone(d)
        self.assertLessEqual(d["endpoints"], 4)
        self.assertEqual(d["branchpoints"], 0)

    def test_cross_has_branch(self):
        b = Bitmap.new(60, 60, (0, 0, 0, 255))
        for y in range(10, 50):
            for x in range(28, 32):
                b.set(x, y, (200, 200, 200, 255))
        for y in range(28, 32):
            for x in range(10, 50):
                b.set(x, y, (200, 200, 200, 255))
        d = medial.analyze(b)
        self.assertGreaterEqual(d["branchpoints"], 1)

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(medial.analyze(b))


if __name__ == "__main__":
    unittest.main()
