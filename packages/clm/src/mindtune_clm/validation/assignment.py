"""Condition assignment, concealment, and blinding model for CLM-08."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mindtune_clm.validation.designs import StudyDefinition
from mindtune_clm.validation.events import CLM08EventType, ValidationEvent
from mindtune_clm.validation.randomization import (
    Allocation,
    blocked_randomization,
    crossover_sequence_randomization,
    simple_randomization,
    stratified_randomization,
)


class BlindingLevel(str, Enum):
    UNBLINDED = "unblinded"
    PARTICIPANT_BLINDED = "participant-blinded"
    ASSESSOR_BLINDED = "assessor-blinded"
    ANALYST_BLINDED = "analyst-blinded"
    PARTIALLY_BLINDED = "partially-blinded"


@dataclass(frozen=True)
class Assignment:
    """One participant-condition assignment with concealment metadata."""

    assignment_id: str
    study_id: str
    study_version: int
    participant_id: str
    condition_id: str
    period: int
    sequence_order: int
    concealed: bool
    revealed_to: list[str] = field(default_factory=list)
    revealed_at: float | None = None
    concealment_method: str = ""
    condition_guess: str | None = None
    guess_confidence: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "study_id": self.study_id,
            "study_version": self.study_version,
            "participant_id": self.participant_id,
            "condition_id": self.condition_id,
            "period": self.period,
            "sequence_order": self.sequence_order,
            "concealed": self.concealed,
            "revealed_to": list(self.revealed_to),
            "revealed_at": self.revealed_at,
            "concealment_method": self.concealment_method,
            "condition_guess": self.condition_guess,
            "guess_confidence": self.guess_confidence,
        }

    def public_view(self, viewer_role: str) -> dict[str, Any]:
        if self.concealed and viewer_role not in self.revealed_to:
            return {
                "assignment_id": self.assignment_id,
                "study_id": self.study_id,
                "study_version": self.study_version,
                "participant_id": self.participant_id,
                "period": self.period,
                "condition_id": None,
                "concealed": True,
            }
        return self.as_dict()


def _next_assignment_id(study: StudyDefinition, participant_id: str, period: int) -> str:
    return f"{study.study_id}-{study.study_version}-{participant_id}-{period}"


def assign_conditions(
    study: StudyDefinition,
    participants: list[str],
    seed: int,
    strata: dict[str, str] | None = None,
    concealment_method: str = "study_id_versioned_hash",
) -> list[Assignment]:
    """Return deterministic, concealed assignments for a study."""
    condition_ids = [c.condition_id for c in study.conditions]
    allocations: list[Allocation] = []
    if study.randomization_method == "blocked":
        allocations = blocked_randomization(participants, condition_ids, seed, allocation_ratio=study.allocation_ratio)
    elif study.randomization_method == "stratified":
        allocations = stratified_randomization(
            participants, condition_ids, seed, strata=strata, allocation_ratio=study.allocation_ratio
        )
    elif study.randomization_method == "crossover":
        allocations = crossover_sequence_randomization(participants, condition_ids, seed)
    else:
        allocations = simple_randomization(participants, condition_ids, seed, allocation_ratio=study.allocation_ratio)

    assignments: list[Assignment] = []
    for alloc in allocations:
        assignments.append(
            Assignment(
                assignment_id=_next_assignment_id(study, alloc.unit_id, alloc.period),
                study_id=study.study_id,
                study_version=study.study_version,
                participant_id=alloc.unit_id,
                condition_id=alloc.condition_id,
                period=alloc.period,
                sequence_order=alloc.sequence_order,
                concealed=study.blinding_level in {
                    BlindingLevel.PARTICIPANT_BLINDED.value,
                    BlindingLevel.ASSESSOR_BLINDED.value,
                    BlindingLevel.ANALYST_BLINDED.value,
                    BlindingLevel.PARTIALLY_BLINDED.value,
                },
                concealment_method=concealment_method,
            )
        )
    return assignments


def reveal_assignment(
    assignment: Assignment, viewer_role: str, event_log: Any | None = None
) -> Assignment:
    """Reveal a concealed assignment and optionally log the event."""
    revealed_to = list(assignment.revealed_to)
    if viewer_role not in revealed_to:
        revealed_to.append(viewer_role)
    new = Assignment(
        assignment_id=assignment.assignment_id,
        study_id=assignment.study_id,
        study_version=assignment.study_version,
        participant_id=assignment.participant_id,
        condition_id=assignment.condition_id,
        period=assignment.period,
        sequence_order=assignment.sequence_order,
        concealed=False,
        revealed_to=revealed_to,
        revealed_at=time.time(),
        concealment_method=assignment.concealment_method,
        condition_guess=assignment.condition_guess,
        guess_confidence=assignment.guess_confidence,
    )
    if event_log is not None:
        event = ValidationEvent.create(
            CLM08EventType.CONDITION_ASSIGNMENT_REVEALED,
            component="assignment",
            component_version="1.0",
            study_id=new.study_id,
            study_version=new.study_version,
            payload={"assignment_id": new.assignment_id, "viewer_role": viewer_role},
        )
        event_log.append(event)
    return new
