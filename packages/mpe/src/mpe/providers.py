"""Provider interfaces and deterministic mock implementations for Phase 4B.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from mpe.enums import (
    AnswerStatus,
    DecisionStatus,
    ErrorCategory,
    EvaluationStatus,
    InterpretationType,
    ResponseMode,
    ScopeStatus,
)
from mpe.errors import ProviderFailureError, ProviderTimeoutError, UnsupportedProviderVersionError
from mpe.types import (
    DomainNormalizedResponseID,
    EvaluationID,
    ObservationID,
    RenderedStimulusID,
    ResponseInterpretationID,
    ScheduleDecisionID,
    make_id,
)

# --------------------------------------------------------------------------- #
# Domain object fixtures
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ContentItem:
    content_item_id: str
    provider_id: str
    provider_version: str
    content_type: str
    checksum: str
    surface_form: str
    normalized_form: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "verified_consensus"
    abstention_status: bool = False


@dataclass(frozen=True)
class TrialContext:
    trial_id: str
    session_id: str
    response_mode: str
    protocol_version_id: str


# --------------------------------------------------------------------------- #
# Provider protocols
# --------------------------------------------------------------------------- #


class Renderer(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def render(self, request: dict[str, Any]) -> dict[str, Any]: ...


class ObservationProvider(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def start_listening(self, window: dict[str, Any]) -> None: ...
    def stop_listening(self, window_id: str) -> None: ...
    def inject(self, text: str) -> None: ...
    def poll(self) -> list[dict[str, Any]]: ...


class ResponseInterpreter(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def interpret(self, captured_response: dict[str, Any]) -> dict[str, Any]: ...


class DomainNormalizer(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def normalize(self, response_interpretation: dict[str, Any]) -> dict[str, Any]: ...


class Evaluator(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def evaluate(
        self,
        domain_normalized_response: dict[str, Any],
        expected_answer: ContentItem,
        context: TrialContext,
    ) -> dict[str, Any]: ...


class Scheduler(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def select_next(self, scheduling_context: "SchedulingContext") -> dict[str, Any]: ...


# --------------------------------------------------------------------------- #
# Scheduling context
# --------------------------------------------------------------------------- #


@dataclass
class SchedulingContext:
    protocol_version_id: str
    session_id: str
    trial_index: int
    item_history: list[dict[str, Any]] = field(default_factory=list)
    protocol_policy: dict[str, Any] = field(default_factory=dict)
    random_seed: str | None = None
    current_block_id: str | None = None
    source_event_ids: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Mock implementations
# --------------------------------------------------------------------------- #


class MockRenderer:
    """Deterministic mock renderer."""

    def __init__(self, version: str = "1.0.0", latency: float = 0.0) -> None:
        self.version = version
        self.latency = latency
        self.failing = False

    def capabilities(self) -> dict[str, Any]:
        return {
            "renderer_id": "mock_renderer",
            "renderer_version": self.version,
            "formats_supported": ["mock_audio"],
            "voices_supported": ["mock_voice"],
            "rate_range": {"min": 0.5, "max": 2.0, "default": 1.0},
            "latency_estimate_ms": 5,
            "streaming_support": False,
        }

    def render(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.failing:
            raise ProviderFailureError("mock renderer forced failure")
        content_item_id = request["content_item_id"]
        return {
            "rendered_stimulus_id": str(make_id(RenderedStimulusID)),
            "stimulus_request_id": request["stimulus_request_id"],
            "renderer_id": "mock_renderer",
            "renderer_version": self.version,
            "media_handle": f"media://mock/{content_item_id}",
            "duration": 1.0,
            "rendered_at": request.get("requested_at", 0.0) + self.latency,
        }


class MockKeyboardObservationProvider:
    """Deterministic mock keyboard observation provider."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version
        self._pending: list[dict[str, Any]] = []
        self._failing = False
        self._timeout = False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": "mock_keyboard",
            "provider_version": self.version,
            "observation_types_supported": ["typed_input"],
            "device_id": "mock_keyboard_0",
            "quality_dimensions_supported": {},
            "quality_flags_supported": [],
            "quality_model_id": "mock_qm",
            "quality_model_version": "1.0.0",
            "latency_estimate_ms": 10,
        }

    def inject(self, text: str) -> None:
        self._pending.append({
            "observation_id": str(make_id(ObservationID)),
            "observation_type": "typed_input",
            "payload": text,
            "quality_dimensions": {},
            "quality_flags": [],
            "quality_model_id": "mock_qm",
            "quality_model_version": "1.0.0",
        })

    def set_failing(self, failing: bool) -> None:
        self._failing = failing

    def set_timeout(self, timeout: bool) -> None:
        self._timeout = timeout

    def start_listening(self, window: dict[str, Any]) -> None:
        pass

    def stop_listening(self, window_id: str) -> None:
        pass

    def poll(self) -> list[dict[str, Any]]:
        if self._timeout:
            raise ProviderTimeoutError("mock keyboard timed out")
        if self._failing:
            raise ProviderFailureError("mock keyboard forced failure")
        observations = self._pending
        self._pending = []
        return observations


class MockResponseInterpreter:
    """Deterministic mock response interpreter."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "interpreter_id": "mock_interpreter",
            "interpreter_version": self.version,
            "response_modes_supported": ["typed", "button"],
            "output_schema": "typed_text",
        }

    def interpret(self, captured_response: dict[str, Any]) -> dict[str, Any]:
        mode = captured_response["response_mode"]
        payload = captured_response["captured_payload"]
        if mode == "typed":
            interpretation_type = InterpretationType.TYPED_TEXT.value
        elif mode == "button":
            interpretation_type = InterpretationType.BUTTON_LABEL.value
        else:
            interpretation_type = InterpretationType.SELECTED_OPTION.value
        return {
            "response_interpretation_id": str(make_id(ResponseInterpretationID)),
            "response_window_id": captured_response["response_window_id"],
            "captured_response_id": captured_response["captured_response_id"],
            "interpreter_id": "mock_interpreter",
            "interpreter_version": self.version,
            "interpreted_payload": payload,
            "interpretation_confidence": 1.0,
            "interpretation_type": interpretation_type,
            "component_timestamp": captured_response.get("captured_at", 0.0),
        }


class MockDomainNormalizer:
    """Deterministic mock domain normalizer."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "normalizer_id": "mock_normalizer",
            "normalizer_version": self.version,
            "normalization_rules_version": "1.0.0",
            "content_types_supported": ["mock_word"],
        }

    def normalize(self, response_interpretation: dict[str, Any]) -> dict[str, Any]:
        return {
            "domain_normalized_response_id": str(make_id(DomainNormalizedResponseID)),
            "response_window_id": response_interpretation["response_window_id"],
            "response_interpretation_id": response_interpretation["response_interpretation_id"],
            "response_mode": response_interpretation.get("interpretation_type", ResponseMode.TYPED.value),
            "normalizer_id": "mock_normalizer",
            "normalizer_version": self.version,
            "normalized_payload": response_interpretation["interpreted_payload"],
            "extracted_at": response_interpretation.get("component_timestamp", 0.0),
            "uncertainty": 0.0,
        }


class MockEvaluator:
    """Deterministic mock evaluator (no Hebrew logic)."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version
        self.abstain = False
        self.fail = False

    def capabilities(self) -> dict[str, Any]:
        return {
            "evaluator_id": "mock_evaluator",
            "evaluator_version": self.version,
            "response_modes_supported": ["typed", "button"],
            "answer_status_values": list(AnswerStatus.values()),
            "evaluation_status_values": list(EvaluationStatus.values()),
            "error_categories_supported": ["out_of_scope", "engine_error", "version_mismatch"],
            "abstention_reasons_supported": ["not_in_scope"],
        }

    def evaluate(
        self,
        domain_normalized_response: dict[str, Any],
        expected_answer: ContentItem,
        context: TrialContext,
    ) -> dict[str, Any]:
        if self.fail:
            return {
                "evaluation_id": str(make_id(EvaluationID)),
                "trial_id": context.trial_id,
                "evaluator_id": "mock_evaluator",
                "evaluator_version": self.version,
                "answer_status": AnswerStatus.UNEVALUABLE.value,
                "evaluation_status": EvaluationStatus.FAILED.value,
                "failure_reason": "forced mock failure",
                "error_category": ErrorCategory.EVALUATION_FAILURE.value,
            }
        if self.abstain:
            return {
                "evaluation_id": str(make_id(EvaluationID)),
                "trial_id": context.trial_id,
                "evaluator_id": "mock_evaluator",
                "evaluator_version": self.version,
                "answer_status": AnswerStatus.UNEVALUABLE.value,
                "evaluation_status": EvaluationStatus.ABSTAINED.value,
                "abstention_reason": "not_in_scope",
                "scope_status": ScopeStatus.OUT_OF_SCOPE.value,
            }
        answer = str(domain_normalized_response.get("normalized_payload", ""))
        correct = answer.strip().lower() == expected_answer.surface_form.strip().lower()
        return {
            "evaluation_id": str(make_id(EvaluationID)),
            "trial_id": context.trial_id,
            "evaluator_id": "mock_evaluator",
            "evaluator_version": self.version,
            "domain_normalized_response_id": domain_normalized_response.get(
                "domain_normalized_response_id", str(make_id(DomainNormalizedResponseID))
            ),
            "expected_content_item_id": expected_answer.content_item_id,
            "answer_status": AnswerStatus.CORRECT.value if correct else AnswerStatus.INCORRECT.value,
            "evaluation_status": EvaluationStatus.COMPLETED.value,
            "correctness_credit": 1.0 if correct else 0.0,
            "scope_status": ScopeStatus.IN_SCOPE.value,
        }


class MockScheduler:
    """Deterministic mock scheduler for a single-item protocol."""

    def __init__(self, version: str = "1.0.0", policy_id: str = "mock_single_item") -> None:
        self.version = version
        self.policy_id = policy_id
        self.policy_version = "1.0.0"
        self.fail = False
        self.abstain = False

    def capabilities(self) -> dict[str, Any]:
        return {
            "scheduler_id": "mock_scheduler",
            "scheduler_version": self.version,
            "scheduling_strategies_supported": ["fixed_sequence"],
            "difficulty_dimensions_supported": [],
        }

    def select_next(self, context: SchedulingContext) -> dict[str, Any]:
        if self.fail:
            raise ProviderFailureError("mock scheduler forced failure")
        policy = context.protocol_policy
        item_sequence = policy.get("item_sequence", [])
        current_index = context.trial_index
        if 1 <= current_index <= len(item_sequence):
            selected = [item_sequence[current_index - 1]]
            decision_type = "next_trial"
        else:
            selected = []
            decision_type = "session_end"

        return {
            "schedule_decision_id": str(make_id(ScheduleDecisionID)),
            "session_id": context.session_id,
            "scheduler_id": "mock_scheduler",
            "scheduler_version": self.version,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "source_event_ids": list(context.source_event_ids),
            "item_history_snapshot_id": "snapshot_0",
            "candidate_item_ids": list(item_sequence),
            "excluded_candidates": [],
            "selection_rule": "fixed_sequence",
            "tie_break_rule": "first",
            "random_seed": context.random_seed or "seed_0",
            "selected_item_ids": selected,
            "decision_type": decision_type,
            "decision_status": DecisionStatus.MADE.value if not self.abstain else DecisionStatus.ABSTAINED.value,
        }


# --------------------------------------------------------------------------- #
# Provider set
# --------------------------------------------------------------------------- #


@dataclass
class ProviderSet:
    renderer: Renderer
    observation: ObservationProvider
    interpreter: ResponseInterpreter
    normalizer: DomainNormalizer
    evaluator: Evaluator
    scheduler: Scheduler

    def version_map(self) -> dict[str, str | None]:
        """Return the provider versions, keyed exactly as the dependency map is.

        The provenance record persists this map, so what is recorded is the same
        thing `check_versions` verifies.
        """
        return {
            "mock_renderer": self.renderer.capabilities().get("renderer_version"),
            "mock_keyboard": self.observation.capabilities().get("provider_version"),
            "mock_interpreter": self.interpreter.capabilities().get("interpreter_version"),
            "mock_normalizer": self.normalizer.capabilities().get("normalizer_version"),
            "mock_evaluator": self.evaluator.capabilities().get("evaluator_version"),
            "mock_scheduler": self.scheduler.capabilities().get("scheduler_version"),
        }

    def check_versions(self, dependency_versions: dict[str, str]) -> None:
        """Verify that each provider version matches the protocol dependencies."""
        for key, actual in self.version_map().items():
            expected = dependency_versions.get(key)
            if expected and actual != expected:
                raise UnsupportedProviderVersionError(
                    f"Provider {key} version mismatch: expected {expected}, got {actual}"
                )
