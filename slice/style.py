"""Style Detection: is the input a photo, a cel-style anime image, or a
painterly illustration?

Pure image statistics — no model. Flat-color coverage, palette size,
edge density, and saturation are the discriminators used across the
photo-vs-illustration literature; each gets reported in `signals` so the
decision stays auditable. Ambiguous statistics return `unknown` rather
than a forced label.
"""

from __future__ import annotations

from .bitmap import Bitmap

LABELS = {
    "real": "リアル（写真・写実）",
    "anime": "アニメ・セル塗り",
    "illustration": "イラスト・絵画的",
    "unknown": "不明",
}


def analyze(bmp: Bitmap) -> dict:
    small = bmp.downscale(256)
    w, h = small.width, small.height
    n = w * h
    if n == 0:
        return {"style": "unknown", "label": LABELS["unknown"],
                "confidence": 0.0, "signals": {}}

    colors: dict = {}
    sat_hi = 0          # vivid pixels
    grad_sum = 0
    grad_hi = 0         # strong-edge pixels
    d = small.data
    luma = bytearray(n)
    for y in range(h):
        base = y * w
        for x in range(w):
            i = (base + x) * 4
            r, g, b = d[i], d[i + 1], d[i + 2]
            luma[base + x] = (r * 3 + g * 6 + b) // 10
            key = (r >> 3, g >> 3, b >> 3)
            colors[key] = colors.get(key, 0) + 1
            if max(r, g, b) - min(r, g, b) > 100 and max(r, g, b) > 120:
                sat_hi += 1
    for y in range(1, h - 1):
        base = y * w
        for x in range(1, w - 1):
            gx = abs(luma[base + x + 1] - luma[base + x - 1])
            gy = abs(luma[base + w + x] - luma[base - w + x])
            g = gx + gy
            grad_sum += g
            if g > 60:
                grad_hi += 1

    inner = max(1, (w - 2) * (h - 2))
    uniq_ratio = len(colors) / n
    top_cov = max(colors.values()) / n
    grad_mean = grad_sum / inner
    edge_density = grad_hi / inner
    sat_ratio = sat_hi / n

    signals = {
        "unique_color_ratio": round(uniq_ratio, 4),
        "top_color_coverage": round(top_cov, 3),
        "edge_density": round(edge_density, 4),
        "grad_mean": round(grad_mean, 2),
        "saturation_ratio": round(sat_ratio, 3),
    }

    def result(style: str, conf: float) -> dict:
        return {"style": style, "label": LABELS[style],
                "confidence": round(min(conf, 0.9), 3), "signals": signals}

    # セル塗り: few flat colors dominate, edges are sparse and sharp.
    if uniq_ratio < 0.02 and top_cov > 0.35 and edge_density < 0.08:
        return result("anime", 0.55 + top_cov * 0.4)
    # 写真: dense micro-texture, no dominant flat color.
    if uniq_ratio > 0.2 and top_cov < 0.25 and edge_density > 0.12:
        return result("real", 0.5 + min(uniq_ratio, 0.4))
    # 絵画的: mid palette with blended gradients — edges exist but soft.
    if uniq_ratio >= 0.02 and edge_density < 0.12 and grad_mean > 3:
        return result("illustration", 0.45 + sat_ratio * 0.3)
    return result("unknown", 0.25)
