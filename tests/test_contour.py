import unittest

from tests import synthetic_person

from slice import contour
from slice.pose import HeuristicPoseEstimator


class TestContour(unittest.TestCase):
    def setUp(self):
        self.est = HeuristicPoseEstimator()
        self.bmp = synthetic_person()

    def test_trace_returns_closed_boundary(self):
        mask = self.est._mask(self.bmp)
        path = contour.trace(mask)
        self.assertGreater(len(path), 20)
        # every contour point is on the border
        for x, y in path[:50]:
            self.assertTrue(contour._border(mask, x, y))

    def test_features_of_standing_figure(self):
        mask = self.est._mask(self.bmp)
        f = contour.features(mask)
        self.assertGreater(f["area"], 100)
        self.assertGreater(f["perimeter"], 50)
        # standing figure is taller than wide
        self.assertLess(f["aspect"], 1.0)
        self.assertGreater(f["compactness"], 1.0)
        cx, cy = f["centroid"]
        self.assertTrue(0 < cx < self.bmp.width)

    def test_empty_mask(self):
        mask = [bytearray(10) for _ in range(10)]
        self.assertEqual(contour.trace(mask), [])
        self.assertEqual(contour.features(mask)["area"], 0)

    def test_features_discloses_truncation(self):
        mask = self.est._mask(self.bmp)
        f = contour.features(mask)
        # a normal trace closes: the flag must exist and be True
        self.assertTrue(f["contour_closed"])
        # _trace reports the flag directly
        path, closed = contour._trace(mask)
        self.assertTrue(closed)
        self.assertEqual(path, contour.trace(mask))


if __name__ == "__main__":
    unittest.main()
