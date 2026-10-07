import json
import os
import shutil
import tempfile
import unittest

from slice import bitmap
from slice.__main__ import main
from tests import synthetic_person


class TestTrackCli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.d, True))
        for i in range(3):
            with open(os.path.join(self.d, "f%d.png" % i), "wb") as f:
                f.write(bitmap.encode_png(synthetic_person()))

    def test_track_dir_writes_report(self):
        out = os.path.join(self.d, "track.json")
        rc = main(["track", self.d, "-o", out])
        self.assertEqual(rc, 0)
        rep = json.load(open(out))
        self.assertEqual(rep["summary"]["n_frames"], 3)
        self.assertEqual(rep["summary"]["n_tracks"], 1)
        self.assertEqual(
            [l["state"] for l in rep["links"]],
            ["new_track", "linked", "linked"])

    def test_empty_dir_fails(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(empty, True))
        self.assertEqual(main(["track", empty]), 1)


if __name__ == "__main__":
    unittest.main()
