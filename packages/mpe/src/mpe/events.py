"""Event envelope and payload schemas for MPE v1.1."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from mpe.enums import (
    AnswerStatus,
    BlockType,
    DataClassification,
    DecisionStatus,
    DecisionType,
    ErrorCategory,
    EvaluationStatus,
    FeedbackCategory,
    FeedbackType,
    InstructionType,
    InterpretationType,
    ObservationType,
    ResponseMode,
    ResponseRequirement,
    ScopeStatus,
)
from mpe.types import BlockID, CorrelationID, EventID, ProtocolVersionID, SessionID, TrialID

SUPPORTED_EVENT_TYPES = frozenset(
    {
        "session_created",
        "session_provenance_recorded",
        "session_started",
        "session_completed",
        "session_cancelled",
        "block_started",
        "block_completed",
        "trial_created",
        "instruction_started",
        "instruction_completed",
        "stimulus_requested",
        "stimulus_ready",
        "response_window_opened",
        "response_timeout",
        "observation_received",
        "captured_response_created",
        "response_interpreted",
        "domain_response_normalized",
        "evaluation_completed",
        "evaluation_abstained",
        "evaluation_failed",
        "feedback_started",
        "feedback_completed",
        "schedule_decision",
        "protocol_terminated",
    }
)


CURRENT_EVENT_SCHEMA_VERSION = "1.2"
"""Event contract emitted by this build.

Schema 1.2 adds the integrity fields (`content_digest`, `previous_digest`) and
the provenance field (`writer_revision`) to the envelope. Schema 1.1 streams
remain readable but carry no chain (ADR-0001 sec. 2.4).
"""


@dataclass(frozen=True, slots=True)
class Event:
    """Canonical MPE event envelope with payload."""

    event_id: EventID
    event_type: str
    schema_version: str
    session_id: SessionID
    session_sequence_number: int
    protocol_version_id: ProtocolVersionID
    timestamp: float
    component: str
    component_version: str
    provenance: list[EventID] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    sensitive: bool = False
    data_classification: DataClassification | None = None
    wallclock_at: float | None = None
    trial_id: TrialID | None = None
    block_id: BlockID | None = None
    correlation_id: CorrelationID | None = None
    quality_flags: list[str] = field(default_factory=list)
    content_digest: str | None = None
    previous_digest: str | None = None
    writer_revision: str | None = None

    def __post_init__(self) -> None:
        payload_copy = copy.deepcopy(dict(self.payload))
        object.__setattr__(self, "payload", MappingProxyType(payload_copy))
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "quality_flags", tuple(self.quality_flags))

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "session_id": str(self.session_id),
            "session_sequence_number": self.session_sequence_number,
            "protocol_version_id": str(self.protocol_version_id),
            "timestamp": self.timestamp,
            "wallclock_at": self.wallclock_at,
            "component": self.component,
            "component_version": self.component_version,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "provenance": [str(e) for e in self.provenance],
            "payload": dict(self.payload),
            "sensitive": self.sensitive,
            "data_classification": self.data_classification.value if self.data_classification else None,
            "trial_id": str(self.trial_id) if self.trial_id else None,
            "block_id": str(self.block_id) if self.block_id else None,
            "quality_flags": list(self.quality_flags),
            "content_digest": self.content_digest,
            "previous_digest": self.previous_digest,
            "writer_revision": self.writer_revision,
        }


class _FieldRule:
    def __init__(
        self,
        name: str,
        required: bool,
        kind: str = "any",
        enum: type | None = None,
        item_kind: str = "any",
    ) -> None:
        self.name = name
        self.required = required
        self.kind = kind
        self.enum = enum
        self.item_kind = item_kind


PAYLOAD_SCHEMAS: dict[str, list[_FieldRule]] = {
    "session_created": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("program_version_id", True, "id"),
        _FieldRule("protocol_version_id", True, "id"),
        _FieldRule("learner_id", True, "str"),
    ],
    "session_provenance_recorded": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("protocol_id", True, "id"),
        _FieldRule("protocol_version_id", True, "id"),
        _FieldRule("curriculum_id", False, "id"),
        _FieldRule("curriculum_version", False, "str"),
        _FieldRule("experimental_condition", False, "str"),
        _FieldRule("randomization_seed", True, "str"),
        _FieldRule("stimulus_set_id", False, "id"),
        _FieldRule("stimulus_set_version", False, "str"),
        _FieldRule("scoring_policy_version", False, "str"),
        _FieldRule("rt_policy_version", False, "str"),
        _FieldRule("signal_processing_policy_version", False, "str"),
        _FieldRule("software_revision", True, "dict"),
        _FieldRule("provider_versions", True, "dict"),
        _FieldRule("writer_component", True, "str"),
        _FieldRule("writer_version", True, "str"),
    ],
    "session_started": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("program_version_id", True, "id"),
        _FieldRule("protocol_version_id", True, "id"),
        _FieldRule("learner_id", True, "str"),
        _FieldRule("random_seed", True, "str"),
        _FieldRule("start_parameters", False, "dict"),
    ],
    "session_completed": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("completed_at", True, "number"),
        _FieldRule("final_trial_index", False, "int"),
    ],
    "session_cancelled": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("reason", True, "str"),
        _FieldRule("cancelled_at", True, "number"),
    ],
    "block_started": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("block_id", True, "id"),
        _FieldRule("block_type", True, "enum", BlockType),
    ],
    "block_completed": [
        _FieldRule("session_id", True, "id"),
        _FieldRule("block_id", True, "id"),
        _FieldRule("completed_trial_count", False, "int"),
    ],
    "trial_created": [
        _FieldRule("trial_id", True, "id"),
        _FieldRule("session_id", True, "id"),
        _FieldRule("block_id", False, "id"),
        _FieldRule("trial_index", True, "int"),
        _FieldRule("task_definition_id", True, "id"),
        _FieldRule("content_item_ids", True, "list", item_kind="id"),
        _FieldRule("response_requirement", True, "enum", ResponseRequirement),
        _FieldRule("accepted_response_modes", False, "list", ResponseMode, "enum"),
    ],
    "instruction_started": [
        _FieldRule("trial_id", True, "id"),
        _FieldRule("instruction_id", True, "id"),
        _FieldRule("instruction_type", True, "enum", InstructionType),
        _FieldRule("instruction_payload", True, "str"),
        _FieldRule("target_operation", True, "str"),
        _FieldRule("allotted_duration", True, "number"),
        _FieldRule("observable_response_expected", False, "bool"),
        _FieldRule("started_at", True, "number"),
    ],
    "instruction_completed": [
        _FieldRule("trial_id", True, "id"),
        _FieldRule("instruction_id", True, "id"),
        _FieldRule("completed_at", True, "number"),
        _FieldRule("duration", False, "number"),
    ],
    "stimulus_requested": [
        _FieldRule("stimulus_request_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("content_item_id", True, "id"),
        _FieldRule("renderer_id", True, "str"),
        _FieldRule("requested_at", True, "number"),
        _FieldRule("scheduled_for", True, "number"),
    ],
    "stimulus_ready": [
        _FieldRule("stimulus_request_id", True, "id"),
        _FieldRule("rendered_stimulus_id", True, "id"),
        _FieldRule("renderer_version", True, "str"),
        _FieldRule("duration", True, "number"),
        _FieldRule("rendered_at", True, "number"),
    ],
    "response_window_opened": [
        _FieldRule("response_window_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("response_modes_accepted", True, "list", ResponseMode, "enum"),
        _FieldRule("opened_at", True, "number"),
        _FieldRule("deadline_at", False, "number"),
        _FieldRule("timeout_policy", True, "str"),
    ],
    "response_timeout": [
        _FieldRule("response_window_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("timeout_at", True, "number"),
    ],
    "observation_received": [
        _FieldRule("observation_id", True, "id"),
        _FieldRule("response_window_id", False, "id"),
        _FieldRule("provider_id", True, "str"),
        _FieldRule("provider_version", True, "str"),
        _FieldRule("observation_type", True, "enum", ObservationType),
        _FieldRule("received_at", True, "number"),
        _FieldRule("payload", True, "any"),
        _FieldRule("quality_dimensions", False, "dict"),
        _FieldRule("quality_flags", False, "list", item_kind="str"),
        _FieldRule("quality_model_id", True, "str"),
        _FieldRule("quality_model_version", True, "str"),
    ],
    "captured_response_created": [
        _FieldRule("captured_response_id", True, "id"),
        _FieldRule("response_window_id", True, "id"),
        _FieldRule("observation_ids", True, "list", item_kind="id"),
        _FieldRule("response_mode", True, "enum", ResponseMode),
        _FieldRule("captured_payload", True, "any"),
        _FieldRule("captured_at", True, "number"),
        _FieldRule("device_provenance", False, "list", item_kind="str"),
        _FieldRule("quality_flags", False, "list", item_kind="str"),
    ],
    "response_interpreted": [
        _FieldRule("response_interpretation_id", True, "id"),
        _FieldRule("response_window_id", True, "id"),
        _FieldRule("captured_response_id", True, "id"),
        _FieldRule("interpreter_id", True, "str"),
        _FieldRule("interpreter_version", True, "str"),
        _FieldRule("interpreted_payload", True, "any"),
        _FieldRule("interpretation_confidence", True, "number"),
        _FieldRule("interpretation_type", True, "enum", InterpretationType),
        _FieldRule("component_timestamp", False, "number"),
    ],
    "domain_response_normalized": [
        _FieldRule("domain_normalized_response_id", True, "id"),
        _FieldRule("response_window_id", True, "id"),
        _FieldRule("response_interpretation_id", True, "id"),
        _FieldRule("response_mode", True, "enum", ResponseMode),
        _FieldRule("normalizer_id", True, "str"),
        _FieldRule("normalizer_version", True, "str"),
        _FieldRule("normalized_payload", True, "any"),
        _FieldRule("extracted_at", True, "number"),
        _FieldRule("uncertainty", False, "number"),
    ],
    "evaluation_completed": [
        _FieldRule("evaluation_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("evaluator_id", True, "str"),
        _FieldRule("evaluator_version", True, "str"),
        _FieldRule("domain_normalized_response_id", True, "id"),
        _FieldRule("expected_content_item_id", True, "id"),
        _FieldRule("answer_status", True, "enum", AnswerStatus),
        _FieldRule("evaluation_status", True, "enum", EvaluationStatus),
        _FieldRule("correctness_credit", False, "number"),
        _FieldRule("scope_status", False, "enum", ScopeStatus),
    ],
    "evaluation_abstained": [
        _FieldRule("evaluation_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("evaluator_id", True, "str"),
        _FieldRule("evaluator_version", True, "str"),
        _FieldRule("answer_status", True, "enum", AnswerStatus),
        _FieldRule("evaluation_status", True, "enum", EvaluationStatus),
        _FieldRule("abstention_reason", False, "str"),
        _FieldRule("scope_status", False, "enum", ScopeStatus),
    ],
    "evaluation_failed": [
        _FieldRule("evaluation_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("evaluator_id", True, "str"),
        _FieldRule("evaluator_version", True, "str"),
        _FieldRule("failure_reason", True, "str"),
        _FieldRule("error_category", True, "enum", ErrorCategory),
    ],
    "feedback_started": [
        _FieldRule("feedback_event_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("evaluation_id", False, "id"),
        _FieldRule("feedback_category", True, "enum", FeedbackCategory),
        _FieldRule("feedback_type", True, "enum", FeedbackType),
        _FieldRule("content_item_id", False, "id"),
        _FieldRule("started_at", True, "number"),
    ],
    "feedback_completed": [
        _FieldRule("feedback_event_id", True, "id"),
        _FieldRule("trial_id", True, "id"),
        _FieldRule("completed_at", True, "number"),
        _FieldRule("duration_observed", False, "number"),
    ],
    "schedule_decision": [
        _FieldRule("schedule_decision_id", True, "id"),
        _FieldRule("session_id", True, "id"),
        _FieldRule("scheduler_id", True, "str"),
        _FieldRule("scheduler_version", True, "str"),
        _FieldRule("policy_id", True, "str"),
        _FieldRule("policy_version", True, "str"),
        _FieldRule("source_event_ids", True, "list", item_kind="id"),
        _FieldRule("candidate_item_ids", True, "list", item_kind="id"),
        _FieldRule("excluded_candidates", False, "list", item_kind="any"),
        _FieldRule("selection_rule", True, "str"),
        _FieldRule("tie_break_rule", True, "str"),
        _FieldRule("random_seed", False, "str"),
        _FieldRule("selected_item_ids", True, "list", item_kind="id"),
        _FieldRule("decision_type", True, "enum", DecisionType),
        _FieldRule("decision_status", True, "enum", DecisionStatus),
    ],
    "protocol_terminated": [
        _FieldRule("safety_event_id", True, "id"),
        _FieldRule("session_id", True, "id"),
        _FieldRule("reason", True, "str"),
        _FieldRule("terminated_at", True, "number"),
        _FieldRule("final_event_id", False, "id"),
    ],
}
