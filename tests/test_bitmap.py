import struct
import unittest
import zlib

from tests import synthetic_person

from slice import bitmap


def _png(w, h, color_type, rows, filters, palette=None, trns=None):
    """Build a minimal 8-bit PNG from raw scanlines + per-row filters."""
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]

    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)

    out = bitmap.PNG_MAGIC
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8,
                                      color_type, 0, 0, 0))
    if palette is not None:
        out += chunk(b"PLTE", palette)
    if trns is not None:
        out += chunk(b"tRNS", trns)
    prev = bytes(w * channels)
    idat = bytearray()
    for row, f in zip(rows, filters):
        idat.append(f)
        enc = bytearray(len(row))
        for i in range(len(row)):
            a = row[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if f == 0:
                enc[i] = row[i]
            elif f == 1:
                enc[i] = (row[i] - a) & 0xFF
            elif f == 2:
                enc[i] = (row[i] - b) & 0xFF
            elif f == 3:
                enc[i] = (row[i] - ((a + b) >> 1)) & 0xFF
            else:
                enc[i] = (row[i] - paeth(a, b, c)) & 0xFF
        idat += enc
        prev = row
    out += chunk(b"IDAT", zlib.compress(bytes(idat)))
    out += chunk(b"IEND", b"")
    return out


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

    def test_bmp_decode(self):
        import struct
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

    def test_downscale_exact_pixels(self):
        # non-integer ratio: nearest-neighbour picks must follow the
        # int(v/s) mapping exactly (byte-identity regression guard)
        bmp = bitmap.Bitmap.new(5, 3, (0, 0, 0, 255))
        for y in range(3):
            for x in range(5):
                bmp.set(x, y, (x * 40 + 1, y * 80 + 2, x + y, 255))
        small = bmp.downscale(3)
        self.assertEqual((small.width, small.height), (3, 2))
        # s = 3/5 = 0.6 -> x picks 0,1,3 ; y picks 0,1
        for y in range(2):
            for x in range(3):
                self.assertEqual(small.get(x, y),
                                 bmp.get((0, 1, 3)[x], (0, 1)[y]))

    def test_get_out_of_frame_raises(self):
        # negative coords used to wrap to the image tail — silent
        # fabrication; now every out-of-frame read fails loudly
        bmp = bitmap.Bitmap.new(8, 8, (1, 2, 3, 255))
        for x, y in ((-1, 0), (0, -1), (8, 0), (0, 8)):
            with self.assertRaises(IndexError):
                bmp.get(x, y)


class TestDecodeFastPaths(unittest.TestCase):
    """The decode rewrite (slice-assignment expansion + SWAR Up
    filter) must stay byte-identical to the per-pixel original."""

    def test_up_filter_adds_prior_row(self):
        # Up filter on rows 1-2; high-bit bytes stress carry lanes.
        w, h = 4, 3
        rows = [
            bytes([200, 100, 250, 77] * w),
            bytes([30, 220, 90, 140] * w),
            bytes([0, 255, 128, 64] * w),
        ]
        img = bitmap.decode(_png(w, h, 6, rows, [0, 2, 2]))
        for y, row in enumerate(rows):
            for x in range(w):
                s = x * 4
                self.assertEqual(img.get(x, y),
                                 tuple(row[s:s + 4]))

    def test_all_filters_mixed_cycle(self):
        w, h = 6, 5
        rows = [bytes(((x * 37 + y * 91 + 17) % 256)
                      for x in range(w * 4)) for y in range(h)]
        img = bitmap.decode(_png(w, h, 6, rows, [0, 1, 2, 3, 4]))
        for y, row in enumerate(rows):
            for x in range(w):
                s = x * 4
                self.assertEqual(img.get(x, y), tuple(row[s:s + 4]))

    def test_gray_rgb_grayalpha_expansion(self):
        g = bitmap.decode(_png(3, 2, 0,
                               [bytes([10, 200, 77]),
                                bytes([0, 128, 255])], [0, 0]))
        self.assertEqual(g.get(1, 0), (200, 200, 200, 255))
        self.assertEqual(g.get(2, 1), (255, 255, 255, 255))

        rgb = bitmap.decode(_png(2, 1, 2,
                                 [bytes([255, 0, 0, 0, 255, 0])], [0]))
        self.assertEqual(rgb.get(0, 0), (255, 0, 0, 255))
        self.assertEqual(rgb.get(1, 0), (0, 255, 0, 255))

        ga = bitmap.decode(_png(2, 1, 4,
                                [bytes([9, 255, 100, 0])], [0]))
        self.assertEqual(ga.get(0, 0), (9, 9, 9, 255))
        self.assertEqual(ga.get(1, 0), (100, 100, 100, 0))

    def test_palette_lookup_unchanged(self):
        palette = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255]
                        + [0] * (256 * 3 - 9))
        trns = bytes([255, 128, 0])
        img = bitmap.decode(_png(4, 1, 3, [bytes([0, 1, 2, 5])], [0],
                                  palette=palette, trns=trns))
        self.assertEqual(img.get(0, 0), (255, 0, 0, 255))
        self.assertEqual(img.get(1, 0), (0, 255, 0, 128))
        self.assertEqual(img.get(2, 0), (0, 0, 255, 0))
        # index beyond tRNS length falls back to opaque
        self.assertEqual(img.get(3, 0), (0, 0, 0, 255))

    def _bmp(self, w, h, bpp, top_down, rgb_rows):
        # rgb_rows: h rows of w*3 bytes (R,G,B per pixel)
        height = -h if top_down else h
        stride = ((w * bpp + 31) // 32) * 4
        rows = {}
        for fy in range(h):
            sy = fy if top_down else h - 1 - fy
            row = bytearray(stride)
            for x in range(w):
                r, g, b = rgb_rows[fy][x * 3:x * 3 + 3]
                o = x * (bpp // 8)
                row[o:o + 3] = bytes((b, g, r))  # BMP stores BGR
                if bpp == 32:
                    row[o + 3] = (x + fy) % 256
            rows[sy] = bytes(row)
        data = b"".join(rows[sy] for sy in range(h))
        info = struct.pack("<IiiHHIIiiII", 40, w, height, 1, bpp, 0,
                           len(data), 2835, 2835, 0, 0)
        head = b"BM" + struct.pack("<IHHI", 54 + len(data), 0, 0, 54)
        return head + info + data

    def test_bmp_32_topdown_and_padding(self):
        # odd width -> 24-bit rows are stride-padded; 32-bit top-down
        # exercises both expansion orders
        w, h = 5, 3
        rgb_rows = [bytes(((x * 53 + y * 29 + 7) % 256)
                          for x in range(w * 3)) for y in range(h)]
        img = bitmap.decode(self._bmp(w, h, 32, True, rgb_rows))
        img24 = bitmap.decode(self._bmp(w, h, 24, False, rgb_rows))
        self.assertEqual((img.width, img.height), (w, h))
        for y in range(h):
            for x in range(w):
                r, g, b = rgb_rows[y][x * 3:x * 3 + 3]
                self.assertEqual(img.get(x, y), (r, g, b, (x + y) % 256))
                self.assertEqual(img24.get(x, y), (r, g, b, 255))


if __name__ == "__main__":
    unittest.main()
