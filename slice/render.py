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
GREEN = (80, 220, 120, 255)  # facing indicator — not a state color


def _line(bmp: Bitmap, x0, y0, x1, y1, rgba):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
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
        color = (BLUE if skel.get(a).state == OBSERVED
                 and skel.get(b).state == OBSERVED else ORANGE)
        _line(out, pa[0], pa[1], pb[0], pb[1], color)
    for j in skel.joints.values():
        color = BLUE if j.state == OBSERVED else ORANGE
        _disc(out, j.x * sx, j.y * sy, max(2, bmp.width // 160), color)
        _disc(out, j.x * sx, j.y * sy, 1, WHITE)

    # Facing arrow above the head when the estimator saw a side profile.
    facing = skel.orientation.get("facing")
    head = pt("head")
    if facing in ("left", "right") and head:
        sgn = -1 if facing == "left" else 1
        ay = max(2, head[1] - bmp.height * 0.06)
        ln = max(6, bmp.width * 0.08)
        tail_x, tip_x = head[0] - sgn * ln, head[0] + sgn * ln * 0.4
        _line(out, tail_x, ay, tip_x, ay, GREEN)
        head_sz = ln * 0.25
        _line(out, tip_x, ay, tip_x - sgn * head_sz, ay - head_sz * 0.6,
              GREEN)
        _line(out, tip_x, ay, tip_x - sgn * head_sz, ay + head_sz * 0.6,
              GREEN)
    return out


def overlay_png(bmp: Bitmap, skel: Skeleton) -> bytes:
    return encode_png(overlay(bmp, skel))
