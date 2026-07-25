"""Shared trial orchestration for protocol runners.

This layer emits the invariant trial event flow (trial creation, instructions,
stimuli, response window, observation, response pipeline, evaluation,
feedback) using the existing Runtime, provider contracts, and event
vocabulary.

It deliberately knows nothing about what a stimulus means, how many choices a
protocol has, how correctness is decided, which feedback category applies, or
which protocol is running.  Those semantics stay in protocol-specific code and
reach the shared layer only through typed specifications and an explicit
payload-extension mapping.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from mpe.enums import (
    DataClassification,
    FeedbackCategory,
    FeedbackType,
    InstructionType,
)
from mpe.errors import ProviderFailureError
from mpe.protocol.bounded_repeat import RepeatMetadata
from mpe.providers import ContentItem, ProviderSet, TrialContext
from mpe.runtime import Runtime
from mpe.types import (
    BlockID,
    CapturedResponseID,
    EventID,
    FeedbackEventID,
    InstructionID,
    ObservationID,
    ResponseWindowID,
    StimulusRequestID,
    TrialID,
    make_id,
)

PayloadValue = str | int | float | bool
PayloadExtension = Mapping[str, PayloadValue]


@dataclass(frozen=True)
class TrialIdentity:
    """Canonical identity of a trial."""

    trial_id: TrialID
    block_id: BlockID
    trial_index: int
    task_definition_id: str
    content_item_ids: tuple[str, ...]


@dataclass(frozen=True)
class InstructionSpec:
    """One instruction start/completion pair."""

    instruction_type: InstructionType
    payload: str
    target_operation: str
    duration: float
    observable_response_expected: bool


@dataclass(frozen=True)
class StimulusSpec:
    """One stimulus request/ready pair."""

    content_item_id: str
    asset_role: str
    renderer_id: str


@dataclass(frozen=True)
class ResponseWindowSpec:
    """A response window opened for a trial."""

    response_modes: tuple[str, ...]
    duration: float = 10.0
    timeout_policy: str = "hard"


@dataclass(frozen=True)
class ObservationSpec:
    """A deterministic observation collected from the observation provider."""

    injection: str
    provider_id: str
    provider_version: str = "1.0.0"
    observation_type: str = "touch_input"


@dataclass(frozen=True)
class ObservationOutcome:
    """Raw observation data returned by the observation provider."""

    observation_id: ObservationID
    raw_payload: str
    latency: float
    quality_dimensions: dict[str, Any] = field(default_factory=dict)
    quality_flags: list[str] = field(default_factory=list)
    quality_model_id: str = ""
    quality_model_version: str = ""


@dataclass(frozen=True)
class FeedbackSpec:
    """Feedback presented at the end of a trial."""

    feedback_category: FeedbackCategory
    feedback_type: FeedbackType
    content_item_id: str
    duration_observed: float = 1.0


_CANONICAL_TRIAL_FIELDS = frozenset(
    {
        "trial_id",
        "session_id",
        "block_id",
        "trial_index",
        "task_definition_id",
        "content_item_ids",
        "response_requirement",
        "accepted_response_modes",
        "repeat_count",
        "adaptation_source",
        "cap",
    }
)


def canonical_trial_fields() -> frozenset[str]:
    """Trial payload fields owned by the shared layer."""
    return _CANONICAL_TRIAL_FIELDS


class TrialPipeline:
    """Emit the invariant trial event flow for one protocol runner."""

    def __init__(self, runtime: Runtime, providers: ProviderSet) -> None:
        self.runtime = runtime
        self.providers = providers
        self._source_event_id: EventID | None = None

    # -- event cursor ---------------------------------------------------

    @property
    def source_event_id(self) -> EventID:
        if self._source_event_id is None:
            return self.runtime.state.events[-1].event_id
        return self._source_event_id

    @source_event_id.setter
    def source_event_id(self, event_id: EventID) -> None:
        self._source_event_id = event_id

    def _advance(self) -> EventID:
        self._source_event_id = self.runtime.state.events[-1].event_id
        return self._source_event_id

    # -- block lifecycle ------------------------------------------------

    def emit_block_started(self, block_id: BlockID, block_type: str) -> EventID:
        self.runtime.emit(
            "block_started",
            {
                "session_id": str(self.runtime.state.session_id),
                "block_id": str(block_id),
                "block_type": block_type,
            },
            block_id=block_id,
        )
        return self._advance()

    def emit_block_completed(self, block_id: BlockID, completed_trial_count: int) -> EventID:
        self.runtime.emit(
            "block_completed",
            {
                "session_id": str(self.runtime.state.session_id),
                "block_id": str(block_id),
                "completed_trial_count": completed_trial_count,
            },
            block_id=block_id,
        )
        return self._advance()

    # -- trial flow -----------------------------------------------------

    def emit_trial_created(
        self,
        identity: TrialIdentity,
        repeat: RepeatMetadata,
        response_requirement: str,
        accepted_response_modes: Sequence[str],
        extensions: PayloadExtension | None = None,
    ) -> EventID:
        """Emit `trial_created` with canonical fields plus protocol extensions."""
        payload: dict[str, Any] = {
            "trial_id": str(identity.trial_id),
            "session_id": str(self.runtime.state.session_id),
            "block_id": str(identity.block_id),
            "trial_index": identity.trial_index,
            "task_definition_id": identity.task_definition_id,
            "content_item_ids": list(identity.content_item_ids),
            "response_requirement": response_requirement,
            "accepted_response_modes": list(accepted_response_modes),
            "repeat_count": repeat.repeat_count,
        }
        for key, value in (extensions or {}).items():
            if key in _CANONICAL_TRIAL_FIELDS:
                raise ValueError(f"Protocol extension may not override canonical field {key!r}")
            payload[key] = value
        if repeat.adaptation_source is not None:
            payload["adaptation_source"] = repeat.adaptation_source
        if repeat.cap:
            payload["cap"] = repeat.cap

        self.runtime.emit(
            "trial_created",
            payload,
            trial_id=identity.trial_id,
            block_id=identity.block_id,
            provenance=[self.source_event_id],
        )
        return self._advance()

    def emit_instruction(self, trial_id: TrialID, spec: InstructionSpec) -> EventID:
        instruction_id = InstructionID(str(make_id(InstructionID)))
        started_at = self.runtime.clock.now()
        event = self.runtime.emit(
            "instruction_started",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "instruction_type": spec.instruction_type.value,
                "instruction_payload": spec.payload,
                "target_operation": spec.target_operation,
                "allotted_duration": spec.duration,
                "observable_response_expected": spec.observable_response_expected,
                "started_at": started_at,
            },
            trial_id=trial_id,
            provenance=[self.source_event_id],
        )
        self.runtime.emit(
            "instruction_completed",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "completed_at": self.runtime.clock.now(),
                "duration": spec.duration,
            },
            trial_id=trial_id,
            provenance=[event.event_id],
        )
        return self._advance()

    def emit_stimulus(self, trial_id: TrialID, spec: StimulusSpec) -> EventID:
        stimulus_request_id = StimulusRequestID(str(make_id(StimulusRequestID)))
        requested_at = self.runtime.clock.now()
        self.runtime.emit(
            "stimulus_requested",
            {
                "stimulus_request_id": str(stimulus_request_id),
                "trial_id": str(trial_id),
                "content_item_id": spec.content_item_id,
                "renderer_id": spec.renderer_id,
                "requested_at": requested_at,
                "scheduled_for": requested_at,
                "asset_role": spec.asset_role,
            },
            trial_id=trial_id,
            provenance=[self.source_event_id],
        )
        provenance_event_id = self.runtime.state.events[-1].event_id

        rendered = self.providers.renderer.render({
            "stimulus_request_id": str(stimulus_request_id),
            "trial_id": str(trial_id),
            "content_item_id": spec.content_item_id,
            "asset_role": spec.asset_role,
        })
        self.runtime.emit(
            "stimulus_ready",
            {
                "stimulus_request_id": rendered["stimulus_request_id"],
                "rendered_stimulus_id": rendered["rendered_stimulus_id"],
                "renderer_id": rendered["renderer_id"],
                "renderer_version": rendered["renderer_version"],
                "duration": rendered["duration"],
                "rendered_at": rendered["rendered_at"],
                "media_handle": rendered["media_handle"],
                "asset_version": rendered["asset_version"],
                "asset_role": rendered["asset_role"],
            },
            trial_id=trial_id,
            component="renderer",
            component_version=rendered["renderer_version"],
            provenance=[provenance_event_id],
        )
        return self._advance()

    def emit_stimuli(self, trial_id: TrialID, specs: Sequence[StimulusSpec]) -> EventID:
        """Emit stimulus pairs in the given order."""
        for spec in specs:
            self.emit_stimulus(trial_id, spec)
        return self.source_event_id

    def open_response_window(
        self,
        trial_id: TrialID,
        spec: ResponseWindowSpec,
    ) -> ResponseWindowID:
        response_window_id = ResponseWindowID(str(make_id(ResponseWindowID)))
        opened_at = self.runtime.clock.now()
        self.runtime.emit(
            "response_window_opened",
            {
                "response_window_id": str(response_window_id),
                "trial_id": str(trial_id),
                "response_modes_accepted": list(spec.response_modes),
                "opened_at": opened_at,
                "deadline_at": opened_at + spec.duration,
                "timeout_policy": spec.timeout_policy,
            },
            trial_id=trial_id,
            provenance=[self.source_event_id],
        )
        self._advance()
        return response_window_id

    def poll_observation(self, spec: ObservationSpec) -> ObservationOutcome:
        """Inject and poll one deterministic observation (no event emitted)."""
        self.providers.observation.inject(spec.injection)
        raw_obs = self.providers.observation.poll()
        if not raw_obs:
            raise ProviderFailureError("Fixture observation provider returned no observation")
        obs = raw_obs[0]
        return ObservationOutcome(
            observation_id=ObservationID(obs["observation_id"]),
            raw_payload=str(obs["payload"]),
            latency=float(obs.get("latency", 0.0)),
            quality_dimensions=obs.get("quality_dimensions", {}),
            quality_flags=obs.get("quality_flags", []),
            quality_model_id=obs["quality_model_id"],
            quality_model_version=obs["quality_model_version"],
        )

    def emit_observation_received(
        self,
        trial_id: TrialID,
        response_window_id: ResponseWindowID,
        spec: ObservationSpec,
        observation: ObservationOutcome,
        payload_value: PayloadValue,
        received_at: float,
    ) -> EventID:
        """Emit `observation_received`; the payload value stays protocol-owned."""
        self.runtime.emit(
            "observation_received",
            {
                "observation_id": str(observation.observation_id),
                "response_window_id": str(response_window_id),
                "provider_id": spec.provider_id,
                "provider_version": spec.provider_version,
                "observation_type": spec.observation_type,
                "received_at": received_at,
                "payload": payload_value,
                "latency": observation.latency,
                "quality_dimensions": observation.quality_dimensions,
                "quality_flags": observation.quality_flags,
                "quality_model_id": observation.quality_model_id,
                "quality_model_version": observation.quality_model_version,
            },
            trial_id=trial_id,
            component="observation_provider",
            component_version=spec.provider_version,
            provenance=[self.source_event_id],
            data_classification=DataClassification.INTERNAL,
        )
        return self._advance()

    def run_response_pipeline(
        self,
        trial_id: TrialID,
        response_window_id: ResponseWindowID,
        observation: ObservationOutcome,
        captured_payload: str,
        response_mode: str,
        captured_at: float,
        device_provenance: Sequence[str],
    ) -> dict[str, Any]:
        """Emit captured response, interpretation, and normalization events.

        Returns the normalized response produced by the existing normalizer
        provider contract.
        """
        captured_response_id = CapturedResponseID(str(make_id(CapturedResponseID)))
        self.runtime.emit(
            "captured_response_created",
            {
                "captured_response_id": str(captured_response_id),
                "response_window_id": str(response_window_id),
                "observation_ids": [str(observation.observation_id)],
                "response_mode": response_mode,
                "captured_payload": captured_payload,
                "captured_at": captured_at,
                "device_provenance": list(device_provenance),
                "quality_flags": [],
            },
            trial_id=trial_id,
            provenance=[self.source_event_id],
        )
        self._advance()

        interpretation = self.providers.interpreter.interpret({
            "captured_response_id": str(captured_response_id),
            "response_window_id": str(response_window_id),
            "response_mode": response_mode,
            "captured_payload": captured_payload,
            "captured_at": captured_at,
        })
        self.runtime.emit(
            "response_interpreted",
            {
                "response_interpretation_id": interpretation["response_interpretation_id"],
                "response_window_id": interpretation["response_window_id"],
                "captured_response_id": interpretation["captured_response_id"],
                "interpreter_id": interpretation["interpreter_id"],
                "interpreter_version": interpretation["interpreter_version"],
                "interpreted_payload": interpretation["interpreted_payload"],
                "interpretation_confidence": interpretation["interpretation_confidence"],
                "interpretation_type": interpretation["interpretation_type"],
                "component_timestamp": interpretation["component_timestamp"],
            },
            trial_id=trial_id,
            component="interpreter",
            component_version=interpretation["interpreter_version"],
            provenance=[self.source_event_id],
        )
        self._advance()

        normalized = self.providers.normalizer.normalize(interpretation)
        normalized["response_mode"] = response_mode
        normalized["normalized_payload"] = captured_payload
        self.runtime.emit(
            "domain_response_normalized",
            {
                "domain_normalized_response_id": normalized["domain_normalized_response_id"],
                "response_window_id": normalized["response_window_id"],
                "response_interpretation_id": normalized["response_interpretation_id"],
                "response_mode": normalized["response_mode"],
                "normalizer_id": normalized["normalizer_id"],
                "normalizer_version": normalized["normalizer_version"],
                "normalized_payload": normalized["normalized_payload"],
                "extracted_at": normalized["extracted_at"],
                "uncertainty": normalized["uncertainty"],
            },
            trial_id=trial_id,
            component="normalizer",
            component_version=normalized["normalizer_version"],
            provenance=[self.source_event_id],
        )
        self._advance()
        return normalized

    def emit_evaluation(
        self,
        trial_id: TrialID,
        normalized: dict[str, Any],
        content_item: ContentItem,
        response_mode: str,
        protocol_version_id: str,
    ) -> dict[str, Any]:
        """Run the evaluator provider and emit `evaluation_completed`."""
        eval_result = self.providers.evaluator.evaluate(
            normalized,
            content_item,
            TrialContext(
                trial_id=str(trial_id),
                session_id=str(self.runtime.state.session_id),
                response_mode=response_mode,
                protocol_version_id=protocol_version_id,
            ),
        )
        self.runtime.emit(
            "evaluation_completed",
            {
                "evaluation_id": eval_result["evaluation_id"],
                "trial_id": str(trial_id),
                "evaluator_id": eval_result["evaluator_id"],
                "evaluator_version": eval_result["evaluator_version"],
                "domain_normalized_response_id": eval_result["domain_normalized_response_id"],
                "expected_content_item_id": eval_result["expected_content_item_id"],
                "answer_status": eval_result["answer_status"],
                "evaluation_status": eval_result["evaluation_status"],
                "correctness_credit": eval_result.get("correctness_credit", 0.0),
                "scope_status": eval_result.get("scope_status"),
            },
            trial_id=trial_id,
            component="evaluator",
            component_version=eval_result["evaluator_version"],
            provenance=[self.source_event_id],
        )
        self._advance()
        return eval_result

    def emit_feedback(self, trial_id: TrialID, spec: FeedbackSpec) -> EventID:
        feedback_event_id = FeedbackEventID(str(make_id(FeedbackEventID)))
        self.runtime.emit(
            "feedback_started",
            {
                "feedback_event_id": str(feedback_event_id),
                "trial_id": str(trial_id),
                "feedback_category": spec.feedback_category.value,
                "feedback_type": spec.feedback_type.value,
                "content_item_id": spec.content_item_id,
                "started_at": self.runtime.clock.now(),
            },
            trial_id=trial_id,
            provenance=[self.source_event_id],
        )
        self._advance()

        self.runtime.emit(
            "feedback_completed",
            {
                "feedback_event_id": str(feedback_event_id),
                "trial_id": str(trial_id),
                "completed_at": self.runtime.clock.now(),
                "duration_observed": spec.duration_observed,
            },
            trial_id=trial_id,
            provenance=[self.source_event_id],
        )
        return self._advance()
