import unittest

from tests import synthetic_person

from slice import topology
from slice.bitmap import Bitmap


class TestTopology(unittest.TestCase):
    def test_person_one_component_no_holes(self):
        d = topology.analyze(synthetic_person())
        self.assertIsNotNone(d)
        self.assertEqual(d["components"], 1)
        self.assertEqual(d["holes"], 0)
        self.assertEqual(d["euler"], 1)

    def test_ring_has_hole(self):
        b = Bitmap.new(80, 80, (0, 0, 0, 255))
        for y in range(20, 60):
            for x in range(20, 60):
                if not (30 <= x < 50 and 30 <= y < 50):
                    b.set(x, y, (200, 200, 200, 255))
        d = topology.analyze(b)
        self.assertEqual(d["components"], 1)
        self.assertEqual(d["holes"], 1)
        self.assertEqual(d["hole_areas"], [400])
        self.assertEqual(d["euler"], 0)

    def test_two_blobs(self):
        b = Bitmap.new(80, 80, (0, 0, 0, 255))
        for y in range(10, 30):
            for x in range(10, 30):
                b.set(x, y, (200, 200, 200, 255))
        for y in range(40, 60):
            for x in range(50, 70):
                b.set(x, y, (200, 200, 200, 255))
        d = topology.analyze(b)
        self.assertEqual(d["components"], 2)
        self.assertEqual(d["euler"], 2)

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(topology.analyze(b))


if __name__ == "__main__":
    unittest.main()
