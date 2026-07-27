"""Immutable, versioned study-definition models for CLM-08."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mindtune_clm.validation.endpoints import Endpoint
from mindtune_clm.validation.estimands import Estimand
from mindtune_clm.validation.hypotheses import Hypothesis


class StudyStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PREREGISTERED = "preregistered"
    ACTIVE = "active"
    CLOSED = "closed"
    ANALYZED = "analyzed"
    REPORTED = "reported"
    SUPERSEDED = "superseded"
    INVALID = "invalid"


class ConditionType(str, Enum):
    ADAPTIVE = "adaptive"
    FIXED = "fixed"
    SHAM = "sham"
    CALIBRATED = "calibrated"
    UNCALIBRATED = "uncalibrated"


@dataclass(frozen=True)
class Condition:
    """Experimental condition with a deterministic configuration."""

    condition_id: str
    name: str
    description: str
    condition_type: str
    components: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "description": self.description,
            "condition_type": self.condition_type,
            "components": dict(self.components),
        }


@dataclass(frozen=True)
class StudyDefinition:
    """Immutable, versioned study definition."""

    study_id: str
    study_version: int
    title: str
    research_question: str
    confirmatory: bool
    status: str
    hypotheses: list[Hypothesis]
    conditions: list[Condition]
    target_population: str
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    randomization_method: str
    blinding_level: str
    allocation_ratio: dict[str, float]
    unit_of_randomization: str
    primary_endpoint_id: str
    secondary_endpoint_ids: list[str]
    exploratory_endpoint_ids: list[str]
    analysis_population: str
    sample_size_rationale: dict[str, Any]
    stopping_rules: list[str]
    missing_data_policy: str
    protocol_deviation_policy: str
    analysis_plan_version: str
    curriculum_version: str
    protocol_version: str
    calibration_requirement: str
    clm_component_versions: dict[str, str]
    safety_policy_version: str
    registration_status: str
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def primary_endpoint(self) -> Endpoint | None:
        for h in self.hypotheses:
            if h.endpoint.endpoint_id == self.primary_endpoint_id:
                return h.endpoint
        return None

    def endpoints(self) -> list[Endpoint]:
        return [h.endpoint for h in self.hypotheses]

    def estimands(self) -> list[Estimand]:
        return [h.estimand for h in self.hypotheses]

    def is_locked(self) -> bool:
        return self.status in {StudyStatus.PREREGISTERED.value, StudyStatus.ACTIVE.value, StudyStatus.CLOSED.value}

    def as_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "study_version": self.study_version,
            "title": self.title,
            "research_question": self.research_question,
            "confirmatory": self.confirmatory,
            "status": self.status,
            "hypotheses": [h.as_dict() for h in self.hypotheses],
            "conditions": [c.as_dict() for c in self.conditions],
            "target_population": self.target_population,
            "inclusion_criteria": list(self.inclusion_criteria),
            "exclusion_criteria": list(self.exclusion_criteria),
            "randomization_method": self.randomization_method,
            "blinding_level": self.blinding_level,
            "allocation_ratio": dict(self.allocation_ratio),
            "unit_of_randomization": self.unit_of_randomization,
            "primary_endpoint_id": self.primary_endpoint_id,
            "secondary_endpoint_ids": list(self.secondary_endpoint_ids),
            "exploratory_endpoint_ids": list(self.exploratory_endpoint_ids),
            "analysis_population": self.analysis_population,
            "sample_size_rationale": dict(self.sample_size_rationale),
            "stopping_rules": list(self.stopping_rules),
            "missing_data_policy": self.missing_data_policy,
            "protocol_deviation_policy": self.protocol_deviation_policy,
            "analysis_plan_version": self.analysis_plan_version,
            "curriculum_version": self.curriculum_version,
            "protocol_version": self.protocol_version,
            "calibration_requirement": self.calibration_requirement,
            "clm_component_versions": dict(self.clm_component_versions),
            "safety_policy_version": self.safety_policy_version,
            "registration_status": self.registration_status,
            "provenance": dict(self.provenance),
            "created_at": self.created_at,
        }
