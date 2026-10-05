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

    def to_dict(self) -> dict:
        from .landmarks import BONES
        return {
            "frame": {"width": self.image_width, "height": self.image_height},
            "joints": {n: j.to_dict() for n, j in self.joints.items()},
            "bones": [list(b) for b in BONES if b[0] in self.joints
                      and b[1] in self.joints],
            "orientation": self.orientation,
            "body_model": self.body_model,
        }
