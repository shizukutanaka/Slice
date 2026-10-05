import unittest

from tests import synthetic_person

from slice import project
from slice.bitmap import Bitmap


class TestProject(unittest.TestCase):
    def test_person_profiles(self):
        d = project.analyze(synthetic_person())
        self.assertIsNotNone(d)
        self.assertGreater(len(d["v_peaks"]), 0)
        self.assertGreater(len(d["rows"]), 0)
        self.assertGreater(len(d["cols"]), 0)
        self.assertGreater(d["bands"]["middle"], 0)

    def test_single_bar_profile(self):
        b = Bitmap.new(60, 60, (0, 0, 0, 255))
        for y in range(10, 50):
            for x in range(20, 40):
                b.set(x, y, (200, 200, 200, 255))
        d = project.analyze(b)
        self.assertEqual(max(d["rows"]), 20)
        self.assertEqual(max(d["cols"]), 40)
        self.assertEqual(d["bbox_rows"], [10, 49])

    def test_empty_none(self):
        b = Bitmap.new(50, 50, (255, 255, 255, 255))
        self.assertIsNone(project.analyze(b))


if __name__ == "__main__":
    unittest.main()
