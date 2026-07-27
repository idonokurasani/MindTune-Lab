"""Typed, prespecified endpoint definitions for CLM-08."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EndpointType(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    EXPLORATORY = "exploratory"


class EndpointDirection(str, Enum):
    HIGHER = "higher"
    LOWER = "lower"
    TWO_SIDED = "two-sided"


@dataclass(frozen=True)
class Endpoint:
    """A concrete, prespecified endpoint."""

    endpoint_id: str
    name: str
    endpoint_type: EndpointType
    metric: str
    timepoint: str
    condition: str | None = None
    expected_direction: EndpointDirection = EndpointDirection.HIGHER
    units: str = ""
    composite: bool = False
    definition: dict[str, Any] = field(default_factory=dict)

    def is_primary(self) -> bool:
        return self.endpoint_type == EndpointType.PRIMARY

    def as_dict(self) -> dict[str, Any]:
        return {
            "endpoint_id": self.endpoint_id,
            "name": self.name,
            "endpoint_type": self.endpoint_type.value,
            "metric": self.metric,
            "timepoint": self.timepoint,
            "condition": self.condition,
            "expected_direction": self.expected_direction.value,
            "units": self.units,
            "composite": self.composite,
            "definition": dict(self.definition),
        }
