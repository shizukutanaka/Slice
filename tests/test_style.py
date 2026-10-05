import random
import unittest

from tests import synthetic_person

from slice import bitmap, style


def noise_image(w=128, h=128, seed=1):
    bmp = bitmap.Bitmap.new(w, h, (0, 0, 0, 255))
    rng = random.Random(seed)
    for y in range(h):
        for x in range(w):
            bmp.set(x, y, (rng.randrange(256), rng.randrange(256),
                           rng.randrange(256), 255))
    return bmp


def gradient_image(w=128, h=128):
    bmp = bitmap.Bitmap.new(w, h, (0, 0, 0, 255))
    for y in range(h):
        for x in range(w):
            bmp.set(x, y, (int(255 * x / w), int(200 * y / h), 120, 255))
    return bmp


def sketch_image(w=128, h=128):
    """White paper, thin black stick-figure strokes."""
    bmp = bitmap.Bitmap.new(w, h, (255, 255, 255, 255))
    for y in range(20, 100):                       # body stroke
        bmp.set(64, y, (0, 0, 0, 255))
        bmp.set(65, y, (0, 0, 0, 255))
    for x in range(30, 98):                        # arms stroke
        bmp.set(x, 40, (0, 0, 0, 255))
    for y in range(60, 108):                       # legs
        bmp.set(50 + (y - 60) // 3, y, (0, 0, 0, 255))
        bmp.set(78 - (y - 60) // 3, y, (0, 0, 0, 255))
    for i in range(6):                             # head ring
        for x in range(54 + i, 74 - i):
            bmp.set(x, 8 + i, (0, 0, 0, 255))
            bmp.set(x, 20 - i, (0, 0, 0, 255))
    return bmp


class TestStyle(unittest.TestCase):
    def test_flat_figure_is_anime(self):
        r = style.analyze(synthetic_person(240, 420))
        self.assertEqual(r["style"], "anime")
        self.assertGreater(r["confidence"], 0.5)
        self.assertGreater(r["signals"]["top_color_coverage"], 0.35)

    def test_noise_is_real(self):
        r = style.analyze(noise_image())
        self.assertEqual(r["style"], "real")

    def test_gradient_is_illustration(self):
        r = style.analyze(gradient_image())
        self.assertEqual(r["style"], "illustration")

    def test_line_art_is_sketch(self):
        r = style.analyze(sketch_image())
        self.assertEqual(r["style"], "sketch")
        self.assertLess(r["signals"]["saturation_ratio"], 0.02)

    def test_pipeline_includes_style(self):
        from slice import pipeline
        doc = pipeline.strip_runtime(pipeline.analyze(
            bitmap.encode_png(synthetic_person(240, 420))))
        self.assertEqual(doc["style"]["style"], "anime")


if __name__ == "__main__":
    unittest.main()
