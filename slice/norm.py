"""Coordinate transforms — keep skeletons aligned with their image.

Cropping, resizing or padding a bitmap changes every joint's
coordinates. `norm` applies the same transform to the skeleton so
an estimate stays glued to its pixels: `crop`, `resize` (uniform
scale), `flip` handled by mirror, and `to_unit` / `from_unit` for
0-1 normalized storage. Joints leaving the frame are demoted to
`state: "predicted"` with their origin disclosed in `basis`, not
deleted — knowledge must record that a previously observed joint
became unmeasurable, and only observed|predicted states are legal
in a Knowledge document.
"""

from __future__ import annotations

from typing import Optional

from .skeleton import Joint, PREDICTED, Skeleton


def _copy(skel: Skeleton) -> Skeleton:
    out = Skeleton(skel.image_width, skel.image_height,
                   joints={n: Joint(j.name, j.x, j.y, j.confidence,
                                    j.state, j.basis)
                           for n, j in skel.joints.items()},
                   orientation=dict(skel.orientation),
                   body_model=dict(skel.body_model),
                   centroid=skel.centroid)
    return out


def _map(skel: Skeleton, fx, fy, frame_w: int, frame_h: int) -> Skeleton:
    out = _copy(skel)
    for j in out.joints.values():
        j.x, j.y = fx(j.x), fy(j.y)
        if j.state == "observed" and not (
                0 <= j.x < frame_w and 0 <= j.y < frame_h):
            j.state = PREDICTED
            j.basis = (j.basis or "observed") \
                + "; lost to transform (was observed)"
    return out


def crop(skel: Skeleton, x0: float, y0: float, w: int,
         h: int) -> Skeleton:
    """Translate joints into the crop's local frame."""
    return _map(skel, lambda x: x - x0, lambda y: y - y0, w, h)


def resize(skel: Skeleton, w: int, h: int,
           new_w: int, new_h: int) -> Skeleton:
    """Scale joints with the frame."""
    sx, sy = new_w / w, new_h / h
    return _map(skel, lambda x: x * sx, lambda y: y * sy,
                new_w, new_h)


def to_unit(skel: Skeleton, w: int, h: int) -> Skeleton:
    """x/w, y/h normalized coordinates (0-1)."""
    out = _copy(skel)
    for j in out.joints.values():
        j.x, j.y = j.x / w, j.y / h
    return out


def from_unit(skel: Skeleton, w: int, h: int) -> Skeleton:
    """Back to pixels."""
    out = _copy(skel)
    for j in out.joints.values():
        j.x, j.y = j.x * w, j.y * h
    return out
