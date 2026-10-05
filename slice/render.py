"""2D skeleton overlay rendering on a Bitmap (no dependencies).

Observed joints/bones render blue, predicted render orange — the same
honesty color code the web viewer uses.
"""

from __future__ import annotations

from .bitmap import Bitmap, encode_png
from .landmarks import BONES
from .skeleton import OBSERVED, Skeleton

BLUE = (30, 120, 255, 255)
ORANGE = (255, 150, 0, 255)
WHITE = (255, 255, 255, 255)


def _line(bmp: Bitmap, x0, y0, x1, y1, rgba, dash=False):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    step = 0
    while True:
        step += 1
        # 2-on/2-off: the 2px brush covers each skipped column's
        # neighbor, so skipping single steps would stay solid.
        if not dash or step % 4 < 2:
            for ox in (-1, 0):
                for oy in (-1, 0):
                    bmp.set(x0 + ox, y0 + oy, rgba)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _disc(bmp: Bitmap, cx, cy, r, rgba):
    for y in range(int(cy) - r, int(cy) + r + 1):
        for x in range(int(cx) - r, int(cx) + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                bmp.set(x, y, rgba)


def overlay(bmp: Bitmap, skel: Skeleton) -> Bitmap:
    """Return a copy of bmp with the skeleton drawn on it."""
    out = Bitmap(bmp.width, bmp.height, bytearray(bmp.data))
    sx = bmp.width / skel.image_width
    sy = bmp.height / skel.image_height

    def pt(name):
        j = skel.get(name)
        return (j.x * sx, j.y * sy) if j else None

    for a, b in BONES:
        pa, pb = pt(a), pt(b)
        if not pa or not pb:
            continue
        ja, jb = skel.get(a), skel.get(b)
        color = (BLUE if ja.state == OBSERVED
                 and jb.state == OBSERVED else ORANGE)
        # Low-confidence links get dashed — the picture carries the
        # same uncertainty the JSON records.
        _line(out, pa[0], pa[1], pb[0], pb[1], color,
              dash=min(ja.confidence, jb.confidence) < 0.55)
    base = max(2, bmp.width // 160)
    for j in skel.joints.values():
        color = BLUE if j.state == OBSERVED else ORANGE
        r = max(2, round(base * (0.5 + j.confidence)))
        _disc(out, j.x * sx, j.y * sy, r, color)
        _disc(out, j.x * sx, j.y * sy, 1, WHITE)
    return out


def overlay_png(bmp: Bitmap, skel: Skeleton) -> bytes:
    return encode_png(overlay(bmp, skel))
