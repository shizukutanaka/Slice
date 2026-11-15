"""SVG overlay — the vector sibling of `render.overlay`.

`render` rasterizes the skeleton into a Bitmap/PNG; `svg` emits the
same drawing as a scalable SVG document — for docs, slide decks, or
downstream editors where pixels are the wrong currency.

The honesty color code is identical (observed = blue, predicted =
orange), plus what raster can't do cheaply: predicted bones are
*dashed* rather than only recolored, and every joint carries a
`<title>` tooltip with its state/confidence/basis so the provenance
survives inside the image itself.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .landmarks import BONES
from .skeleton import OBSERVED, Skeleton

BLUE = "#1e78ff"
ORANGE = "#ff9600"
WHITE = "#ffffff"


def _tip(j) -> str:
    return escape("%s: %s (conf %.2f)%s" % (
        j.name, j.state, j.confidence,
        (" — " + j.basis) if j.basis else ""))


def render(skel: Skeleton, *, background: str = "none",
           scale: float = 1.0, credit: bool = True) -> str:
    """SVG document string for the skeleton at native frame size.

    `scale` multiplies all coordinates (useful when the skeleton
    describes a larger source image). `background` accepts any SVG
    paint value; "none" keeps the overlay transparent.

    `credit` (default on) embeds one `<desc>` line naming Slice and its
    repository — the SVG-native place for document provenance, invisible
    in the rendered image. Delete the element from the file, or pass
    credit=False, to leave it out.
    """
    sx = sy = scale
    w = round(skel.image_width * scale, 3)
    h = round(skel.image_height * scale, 3)
    sw = max(1.5, skel.image_width / 160.0)
    r = max(1.5, skel.image_width / 106.0)
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 %s %s" width="%s" height="%s">' % (w, h, w, h),
    ]
    if credit:
        out.append("<desc>Generated with Slice — "
                   "https://github.com/shizukutanaka/Slice</desc>")
    out.append(
        '<rect width="%s" height="%s" fill="%s"/>' % (w, h, background))
    for a, b in BONES:
        ja, jb = skel.get(a), skel.get(b)
        if not ja or not jb:
            continue
        observed = ja.state == OBSERVED and jb.state == OBSERVED
        color = BLUE if observed else ORANGE
        dash = '' if observed else ' stroke-dasharray="4 3"'
        tip = escape("%s–%s: %s" % (
            a, b, "observed" if observed else "predicted"))
        out.append(
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
            'stroke="%s" stroke-width="%.1f" '
            'stroke-linecap="round"%s>'
            '<title>%s</title></line>' % (
                ja.x * sx, ja.y * sy, jb.x * sx, jb.y * sy,
                color, sw, dash, tip))
    for j in skel.joints.values():
        color = BLUE if j.state == OBSERVED else ORANGE
        out.append(
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s">'
            '<title>%s</title></circle>' % (
                j.x * sx, j.y * sy, r, color, _tip(j)))
        out.append(
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (
                j.x * sx, j.y * sy, r / 3.0, WHITE))
    out.append('</svg>')
    return "\n".join(out)
