from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def synthetic_person(width=160, height=300, *, arms_down=True,
                     skin=(60, 60, 60, 255), bg=(235, 235, 235, 255)):
    """Draw a simple dark figure on a light background.

    Front view: round head, rectangular torso, both arms visible beside
    the torso, two separated legs.
    """
    from slice.bitmap import Bitmap

    bmp = Bitmap.new(width, height, bg)
    cx = width // 2

    def rect(x0, y0, x1, y1):
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                bmp.set(x, y, skin)

    def disc(ccx, ccy, r):
        for y in range(int(ccy - r), int(ccy + r) + 1):
            for x in range(int(ccx - r), int(ccx + r) + 1):
                if (x - ccx) ** 2 + (y - ccy) ** 2 <= r * r:
                    bmp.set(x, y, skin)

    head_r = width * 0.11
    sh_y = height * 0.22
    hip_y = height * 0.55
    torso_w = width * 0.34
    disc(cx, head_r + 8, head_r)                       # head
    rect(cx - 3, head_r + 6, cx + 3, sh_y + 6)         # neck (joins head->torso)
    # shoulder bar connects arms and torso into one silhouette
    rect(cx - torso_w / 2 - 10, sh_y, cx + torso_w / 2 + 10, sh_y + 6)
    rect(cx - torso_w / 2, sh_y, cx + torso_w / 2, hip_y)  # torso
    # arms below the bar: separate runs beside the torso, dangling
    # well below the hip line (hands at ~75% of body height)
    rect(cx - torso_w / 2 - 10, sh_y + 6, cx - torso_w / 2 - 2,
         height * 0.75)                                 # left arm
    rect(cx + torso_w / 2 + 2, sh_y + 6, cx + torso_w / 2 + 10,
         height * 0.75)                                 # right arm
    # legs separated by a gap
    gap = 8
    rect(cx - torso_w / 2, hip_y, cx - gap / 2, height - 10)
    rect(cx + gap / 2, hip_y, cx + torso_w / 2, height - 10)
    return bmp
