"""Skeleton data model: joints with position, confidence and provenance.

Every joint is either OBSERVED (a silhouette feature supports it) or
PREDICTED (filled in from symmetry / anatomy priors). The distinction is
the core honesty contract of Slice and is preserved in the Knowledge JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

OBSERVED = "observed"
PREDICTED = "predicted"

Point = Tuple[float, float]


@dataclass
class Joint:
    name: str
    x: float
    y: float
    confidence: float
    state: str = OBSERVED  # OBSERVED | PREDICTED
    basis: str = ""        # what evidence produced this joint

    def to_dict(self) -> dict:
        return {
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "confidence": round(self.confidence, 3),
            "state": self.state,
            "basis": self.basis,
        }


@dataclass
class Skeleton:
    image_width: int
    image_height: int
    joints: Dict[str, Joint] = field(default_factory=dict)
    orientation: dict = field(default_factory=dict)
    body_model: dict = field(default_factory=dict)
    centroid: Optional[Point] = None
    # runtime only (not serialized): how many foreground components
    # were offered for skeletonization when estimate_multi/split ran
    # — 0 means the skeleton came from the single-person path
    component_count: int = 0

    def set(self, joint: Joint) -> None:
        self.joints[joint.name] = joint

    def get(self, name: str) -> Optional[Joint]:
        return self.joints.get(name)

    def point(self, name: str) -> Optional[Point]:
        j = self.joints.get(name)
        return (j.x, j.y) if j else None

    def missing(self) -> List[str]:
        from .landmarks import JOINTS
        return [n for n in JOINTS if n not in self.joints]

    def normalized(self) -> Optional[dict]:
        """Root-relative pose in torso units: pelvis at the origin,
        one unit = neck–pelvis distance, +y downward. Resolution- and
        framing-independent, so poses compare across images."""
        pelvis = self.point("pelvis")
        neck = self.point("neck")
        if not pelvis or not neck:
            return None
        unit = ((pelvis[0] - neck[0]) ** 2 + (pelvis[1] - neck[1]) ** 2) ** 0.5
        if unit < 1e-6:
            return None
        return {
            "origin": "pelvis",
            "unit": "neck_pelvis_length",
            "joints": {
                n: {"x": round((j.x - pelvis[0]) / unit, 4),
                    "y": round((j.y - pelvis[1]) / unit, 4)}
                for n, j in self.joints.items()
            },
        }

    def to_dict(self) -> dict:
        from .landmarks import BONES
        d = {
            "frame": {"width": self.image_width, "height": self.image_height},
            "joints": {n: j.to_dict() for n, j in self.joints.items()},
            "bones": [list(b) for b in BONES if b[0] in self.joints
                      and b[1] in self.joints],
            "orientation": self.orientation,
            "body_model": self.body_model,
        }
        norm = self.normalized()
        if norm is not None:
            d["normalized"] = norm
        return d
