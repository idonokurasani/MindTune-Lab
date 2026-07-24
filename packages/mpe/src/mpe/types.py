"""Canonical identifier types for MPE v1.1.

Every identifier is a distinct frozen type so that ProgramID cannot be
accidentally used where SessionID is required.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T", bound="Identifier")


@dataclass(frozen=True, slots=True)
class Identifier:
    """Base class for all canonical MPE identifiers."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError(f"{self.__class__.__name__} requires a non-empty string value")

    def __str__(self) -> str:
        return self.value

    def as_dict(self) -> dict[str, str]:
        return {"value": self.value}


class ProgramID(Identifier):
    """Logical program identity."""


class ProgramVersionID(Identifier):
    """Immutable executable program version."""


class ProtocolID(Identifier):
    """Logical protocol identity."""


class ProtocolVersionID(Identifier):
    """Immutable executable protocol version."""


class SessionID(Identifier):
    """One execution of a ProgramVersion/ProtocolVersion."""


class BlockID(Identifier):
    """Block definition/execution identity."""


class TaskDefinitionID(Identifier):
    """Reusable task template identity."""


class TrialID(Identifier):
    """Atomic trial execution identity."""


class ContentItemID(Identifier):
    """Domain-neutral content item identity."""


class StimulusRequestID(Identifier):
    """Stimulus request identity."""


class RenderedStimulusID(Identifier):
    """Rendered stimulus identity."""


class InstructionID(Identifier):
    """Instruction execution identity."""


class ResponseWindowID(Identifier):
    """Response window identity."""


class ObservationID(Identifier):
    """Raw observation identity."""


class CapturedResponseID(Identifier):
    """Technical captured response identity."""


class ResponseInterpretationID(Identifier):
    """Domain-agnostic response interpretation identity."""


class DomainNormalizedResponseID(Identifier):
    """Domain-specific normalized response identity."""


class EvaluationID(Identifier):
    """Evaluation result identity."""


class FeedbackEventID(Identifier):
    """Feedback delivery identity."""


class ScheduleDecisionID(Identifier):
    """Scheduler decision identity."""


class ItemHistorySnapshotID(Identifier):
    """Snapshot of item history used by scheduler."""


class SafetyEventID(Identifier):
    """Safety event identity."""


class SafetyInstructionID(Identifier):
    """Safety instruction identity."""


class EvidenceRecordID(Identifier):
    """Evidence record identity."""


class EventID(Identifier):
    """Immutable event identity."""


class CorrelationID(Identifier):
    """Correlation identity linking request to result."""


def make_id(cls: type[T]) -> T:
    """Create a new random identifier of the requested type."""
    return cls(str(uuid.uuid4()))
