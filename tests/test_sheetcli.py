import os
import shutil
import tempfile
import unittest

from slice import bitmap
from slice.__main__ import main
from tests import synthetic_person


class TestSheetCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        for name in ("a.png", "b.png", "c.png"):
            with open(os.path.join(self.d, name), "wb") as f:
                f.write(bitmap.encode_png(synthetic_person()))
        with open(os.path.join(self.d, "note.txt"), "w") as f:
            f.write("not an image")

    def test_writes_grid(self):
        out = os.path.join(self.d, "out.png")
        self.assertEqual(
            main(["sheet", self.d, "-o", out]), 0)
        bmp = bitmap.decode(open(out, "rb").read())
        # 3 tiles -> 2 cols x 2 rows of 128px cells
        self.assertEqual((bmp.width, bmp.height), (256, 256))

    def test_empty_dir_fails(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(empty, True))
        self.assertEqual(main(["sheet", empty]), 1)


if __name__ == "__main__":
    unittest.main()
