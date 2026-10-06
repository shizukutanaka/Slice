"""Tests for slice.consensus — median-vote estimation."""
import unittest

from slice import consensus, evaluate
from slice.skeleton import OBSERVED, PREDICTED


class TestConsensus(unittest.TestCase):
    def test_fixture_consensus(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = consensus.consensus(bmp)
        self.assertEqual(r["state"], "observed")
        sk = r["skeleton"]
        self.assertTrue(sk.joints)
        self.assertEqual(len(r["runs"]), 5)

    def test_confidence_discounted(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = consensus.consensus(bmp)
        for j in r["skeleton"].joints.values():
            self.assertLessEqual(j.confidence, 1.0)
            self.assertGreater(j.confidence, 0.0)

    def test_basis_records_runs(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = consensus.consensus(bmp)
        for j in r["skeleton"].joints.values():
            self.assertIn(j.state, (OBSERVED, PREDICTED))
            self.assertTrue(j.basis)

    def test_disputed_listed(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = consensus.consensus(bmp)
        for d in r["disputed"]:
            self.assertIn("joint", d)
            self.assertIn("runs", d)
            self.assertIn("spread_px", d)

    def test_empty_image_fails(self):
        from slice.bitmap import Bitmap
        r = consensus.consensus(Bitmap.new(160, 300, (240, 240, 240, 255)))
        self.assertEqual(r["state"], "failed")

    def test_positions_in_base_frame(self):
        bmp, _ = evaluate.draw_case(160, 300)
        r = consensus.consensus(bmp)
        sk = r["skeleton"]
        for j in sk.joints.values():
            self.assertGreaterEqual(j.x, 0)
            self.assertLessEqual(j.x, sk.image_width)
            self.assertGreaterEqual(j.y, 0)
            self.assertLessEqual(j.y, sk.image_height)


if __name__ == "__main__":
    unittest.main()
