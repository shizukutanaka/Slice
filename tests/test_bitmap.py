import struct
import unittest
import zlib

from tests import synthetic_person

from slice import bitmap

_ADAM7 = (
    (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
    (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2),
)


def encode_png_adam7(bmp):
    """Minimal Adam7 (color type 6, filter 0) encoder for tests."""
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload)))

    data = bytearray()
    for x0, y0, dx, dy in _ADAM7:
        pw = (bmp.width - x0 + dx - 1) // dx if bmp.width > x0 else 0
        ph = (bmp.height - y0 + dy - 1) // dy if bmp.height > y0 else 0
        for i in range(ph):
            data.append(0)
            y = y0 + i * dy
            for j in range(pw):
                data += bytes(bmp.get(x0 + j * dx, y))
    ihdr = struct.pack(">IIBBBBB", bmp.width, bmp.height, 8, 6, 0, 0, 1)
    return (bitmap.PNG_MAGIC + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(data)))
            + chunk(b"IEND", b""))


class TestBitmap(unittest.TestCase):
    def test_png_roundtrip(self):
        bmp = synthetic_person(60, 90)
        raw = bitmap.encode_png(bmp)
        self.assertTrue(raw.startswith(bitmap.PNG_MAGIC))
        back = bitmap.decode(raw)
        self.assertEqual((back.width, back.height), (60, 90))
        self.assertEqual(back.get(30, 45), bmp.get(30, 45))

    def test_png_filters_and_palette_absent(self):
        # grayscale write path through encode uses RGBA; decode handles ct6
        bmp = bitmap.Bitmap.new(4, 4, (10, 20, 30, 255))
        back = bitmap.decode(bitmap.encode_png(bmp))
        self.assertEqual(back.get(0, 0), (10, 20, 30, 255))

    def test_png_adam7_roundtrip(self):
        bmp = synthetic_person(37, 53)  # non-multiple dims exercise pass edges
        back = bitmap.decode(encode_png_adam7(bmp))
        self.assertEqual((back.width, back.height), (37, 53))
        for y in range(0, 53, 7):
            for x in range(0, 37, 5):
                self.assertEqual(back.get(x, y), bmp.get(x, y),
                                 f"pixel {x},{y}")

    def test_bmp_decode(self):
        w, h = 2, 2
        stride = ((w * 24 + 31) // 32) * 4
        px = bytearray(stride * h)
        # bottom-up: image top-left lives in file row h-1
        i = (h - 1) * stride
        px[i:i + 3] = bytes((0, 0, 255))
        info = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0,
                           len(px), 2835, 2835, 0, 0)
        head = b"BM" + struct.pack("<IHHI", 14 + 40 + len(px), 0, 0, 54)
        img = bitmap.decode(head + info + px)
        self.assertEqual(img.get(0, 0)[:3], (255, 0, 0))

    def test_unsupported(self):
        with self.assertRaises(bitmap.UnsupportedFormat):
            bitmap.decode(b"\x00\x01\x02\x03")

    def test_downscale(self):
        bmp = synthetic_person(200, 400)
        small = bmp.downscale(100)
        self.assertLessEqual(max(small.width, small.height), 100)


if __name__ == "__main__":
    unittest.main()
