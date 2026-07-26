"""Event envelope and payload schemas for MPE v1.1."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from mpe.enums import (
    AdaptationDecision,
    AnswerStatus,
    BlockType,
    DataClassification,
    DecisionStatus,
    DecisionType,
    DeploymentStatus,
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
        "adaptation_decision",
        "protocol_terminated",
        # CLM-01 closed-loop mantra control events
        "observation_frame_created",
        "cognitive_state_estimated",
        "control_decision_made",
        "actuation_requested",
        "actuation_applied",
        "adapted_stimulus_rendered",
        "intervention_outcome_evaluated",
        # CLM-02 deterministic sensor replay events
        "sensor_source_registered",
        "replay_manifest_created",
        "sensor_sample_parsed",
        "sensor_sample_normalized",
        "sensor_quality_assessed",
        "replay_window_created",
        "replay_window_rejected",
        "observation_frame_generated_from_replay",
        "sensor_replay_started",
        "sensor_replay_completed",
        "sensor_replay_failed",
        "replay_digest_computed",
        # CLM-02B FC11 recorded data adapter events
        "fc11_source_registered",
        "fc11_metadata_parsed",
        "fc11_record_parsed",
        "fc11_record_rejected",
        "fc11_timestamp_policy_applied",
        "fc11_sample_normalized",
        "fc11_quality_assessed",
        "fc11_window_created",
        "fc11_window_rejected",
        "fc11_observation_frame_generated",
        "fc11_sensor_replay_completed",
        "fc11_sensor_replay_failed",
        "fc11_replay_digest_computed",
        "audio_asset_registered",
        "utterance_plan_created",
        "audio_render_started",
        "audio_segment_transformed",
        "audio_artifact_rendered",
        "audio_artifact_validated",
        "audio_render_failed",
        "playback_command_created",
        "playback_scheduled",
        "playback_started",
        "playback_completed",
        "playback_rejected",
        "audio_fallback_applied",
        "audio_digest_computed",
        # CLM-03B SpeechGen Giuseppe/Aaron voice pipeline events
        "pedagogical_voice_request_created",
        "voice_route_selected",
        "speechgen_request_created",
        "speechgen_cache_hit",
        "speechgen_cache_miss",
        "speechgen_synthesis_started",
        "speechgen_synthesis_completed",
        "speechgen_synthesis_failed",
        "speechgen_audio_validated",
        "voice_asset_canonicalized",
        "voice_asset_registered_with_clm03",
        "voice_cache_corruption_detected",
        "human_pronunciation_review_recorded",
        # CLM-04 live FC11 sensor gateway events
        "live_gateway_started",
        "live_gateway_paused",
        "live_gateway_resumed",
        "live_gateway_stopped",
        "live_gateway_completed",
        "live_gateway_health_changed",
        "live_sensor_source_connected",
        "live_sensor_source_disconnected",
        "live_sensor_source_reconnect_attempt",
        "live_sensor_source_reconnect_exhausted",
        "live_sensor_source_epoch_changed",
        "live_packet_received",
        "live_packet_late",
        "live_packet_duplicate",
        "live_buffer_overflow",
        "live_packet_normalized",
        "live_quality_assessed",
        "live_window_created",
        "live_window_rejected",
        "live_observation_frame_generated",
    }
)


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
    "adaptation_decision": [
        _FieldRule("adaptation_decision_id", True, "id"),
        _FieldRule("session_id", True, "id"),
        _FieldRule("policy_id", True, "str"),
        _FieldRule("policy_version", True, "str"),
        _FieldRule("deployment_status", True, "enum", DeploymentStatus),
        _FieldRule("target_dimension", True, "str"),
        _FieldRule("current_value", True, "number"),
        _FieldRule("proposed_value", True, "number"),
        _FieldRule("source_event_ids", True, "list", item_kind="id"),
        _FieldRule("aggregation_window", True, "int"),
        _FieldRule("minimum_evidence", True, "bool"),
        _FieldRule("uncertainty_threshold", True, "bool"),
        _FieldRule("confidence", True, "number"),
        _FieldRule("cooldown", True, "int"),
        _FieldRule("hysteresis", True, "number"),
        _FieldRule("maximum_step_size", True, "number"),
        _FieldRule("rollback_rule", False, "str"),
        _FieldRule("abstention_rule", False, "str"),
        _FieldRule("decision", True, "enum", AdaptationDecision),
        _FieldRule("reason", True, "str"),
        _FieldRule("prior_state", True, "str"),
        _FieldRule("resulting_state", True, "str"),
        _FieldRule("eeg_ignored", True, "bool"),
        _FieldRule("applied_at", False, "number"),
    ],
    # CLM-04 live FC11 sensor gateway events (minimal schemas; no required fields)
    "live_gateway_started": [],
    "live_gateway_paused": [],
    "live_gateway_resumed": [],
    "live_gateway_stopped": [],
    "live_gateway_completed": [],
    "live_gateway_health_changed": [],
    "live_sensor_source_connected": [],
    "live_sensor_source_disconnected": [],
    "live_sensor_source_reconnect_attempt": [],
    "live_sensor_source_reconnect_exhausted": [],
    "live_sensor_source_epoch_changed": [],
    "live_packet_received": [],
    "live_packet_late": [],
    "live_packet_duplicate": [],
    "live_buffer_overflow": [],
    "live_packet_normalized": [],
    "live_quality_assessed": [],
    "live_window_created": [],
    "live_window_rejected": [],
    "live_observation_frame_generated": [],
}
