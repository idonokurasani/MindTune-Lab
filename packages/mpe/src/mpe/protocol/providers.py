"""Provider implementations for the Immediate Recall fixture slice.

These providers are deterministic, do not access any external service, and exist
only to satisfy the Runtime's provider contract with opaque fixture data.
"""

from __future__ import annotations

from typing import Any

from mpe.enums import AnswerStatus, EvaluationStatus, InterpretationType, ResponseMode, ScopeStatus
from mpe.errors import ProviderFailureError, ProviderTimeoutError
from mpe.protocol.eeg_provider import MockEEGProvider
from mpe.protocol.fixture_minimal import ImmediateRecallFixture
from mpe.providers import (
    ContentItem,
    DomainNormalizer,
    Evaluator,
    ObservationProvider,
    Renderer,
    ResponseInterpreter,
    Scheduler,
)
from mpe.types import (
    DomainNormalizedResponseID,
    EvaluationID,
    ObservationID,
    RenderedStimulusID,
    ResponseInterpretationID,
    make_id,
)


class FixtureRenderer(Renderer):
    """Deterministic fixture renderer that returns version-pinned media handles."""

    def __init__(self, fixture: ImmediateRecallFixture, version: str = "1.0.0") -> None:
        self.fixture = fixture
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "renderer_id": "fixture_renderer",
            "renderer_version": self.version,
            "formats_supported": ["fixture_media"],
            "voices_supported": [],
            "rate_range": {"min": 1.0, "max": 1.0, "default": 1.0},
            "latency_estimate_ms": 0,
            "streaming_support": False,
        }

    def render(self, request: dict[str, Any]) -> dict[str, Any]:
        content_item_id = request.get("content_item_id")
        role = request.get("asset_role", "prompt")
        if not isinstance(content_item_id, str) or not isinstance(role, str):
            raise ProviderFailureError("Invalid stimulus request: missing content_item_id or asset_role")
        item = self.fixture.item_by_id(content_item_id)
        if item is None or role not in item.assets:
            raise ProviderFailureError(
                f"No fixture asset for item {content_item_id!r} role {role!r}"
            )
        asset = item.assets[role]
        return {
            "rendered_stimulus_id": str(make_id(RenderedStimulusID)),
            "stimulus_request_id": request.get("stimulus_request_id", ""),
            "renderer_id": "fixture_renderer",
            "renderer_version": self.version,
            "media_handle": asset.media_handle,
            "duration": 1.0,
            "rendered_at": request.get("requested_at", 0.0),
            "asset_version": asset.version,
            "asset_role": asset.role,
        }


class FixtureObservationProvider(ObservationProvider):
    """Deterministic self-confirmation observation provider."""

    def __init__(self, fixture: ImmediateRecallFixture, version: str = "1.0.0") -> None:
        self.fixture = fixture
        self.version = version
        self._pending: list[dict[str, Any]] = []
        self._failing = False
        self._timeout = False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": "fixture_self_confirmation",
            "provider_version": self.version,
            "observation_types_supported": ["touch_input"],
            "device_id": "fixture_button_0",
            "quality_dimensions_supported": {},
            "quality_flags_supported": [],
            "quality_model_id": "fixture_qm",
            "quality_model_version": "1.0.0",
            "latency_estimate_ms": 0,
        }

    def inject(self, text: str) -> None:
        """Stage a self-confirmation observation.

        `text` is expected to be the literal self-confirmation value, optionally
        prefixed with a latency override in the form '<latency>:<value>'.
        """
        if ":" in text:
            latency_str, value = text.split(":", 1)
            latency = float(latency_str)
        else:
            latency = 0.0
            value = text
        self._pending.append({
            "observation_id": str(make_id(ObservationID)),
            "observation_type": "touch_input",
            "payload": value,
            "latency": latency,
            "quality_dimensions": {},
            "quality_flags": [],
            "quality_model_id": "fixture_qm",
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
            raise ProviderTimeoutError("fixture observation timed out")
        if self._failing:
            raise ProviderFailureError("fixture observation forced failure")
        observations = self._pending
        self._pending = []
        return observations


class FixtureResponseInterpreter(ResponseInterpreter):
    """Passthrough interpreter for self-confirmation values."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "interpreter_id": "fixture_interpreter",
            "interpreter_version": self.version,
            "response_modes_supported": ["touch", "typed"],
            "output_schema": "selected_option",
        }

    def interpret(self, captured_response: dict[str, Any]) -> dict[str, Any]:
        payload = captured_response.get("captured_payload", "")
        mode = captured_response.get("response_mode", "touch")
        if mode == "typed":
            interpretation_type = InterpretationType.TYPED_TEXT.value
        elif mode == "button":
            interpretation_type = InterpretationType.BUTTON_LABEL.value
        else:
            interpretation_type = InterpretationType.SELECTED_OPTION.value
        return {
            "response_interpretation_id": str(make_id(ResponseInterpretationID)),
            "response_window_id": captured_response.get("response_window_id", ""),
            "captured_response_id": captured_response.get("captured_response_id", ""),
            "interpreter_id": "fixture_interpreter",
            "interpreter_version": self.version,
            "interpreted_payload": payload,
            "interpretation_confidence": 1.0,
            "interpretation_type": interpretation_type,
            "component_timestamp": captured_response.get("captured_at", 0.0),
        }


class FixtureResponseNormalizer(DomainNormalizer):
    """Passthrough normalizer for self-confirmation values."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "normalizer_id": "fixture_normalizer",
            "normalizer_version": self.version,
            "normalization_rules_version": "1.0.0",
            "content_types_supported": ["fixture_self_confirmation", "typed_text"],
        }

    def normalize(self, response_interpretation: dict[str, Any]) -> dict[str, Any]:
        mode = response_interpretation.get("interpretation_type", ResponseMode.TOUCH.value)
        if mode == InterpretationType.TYPED_TEXT.value:
            response_mode = ResponseMode.TYPED.value
        else:
            response_mode = ResponseMode.TOUCH.value
        return {
            "domain_normalized_response_id": str(make_id(DomainNormalizedResponseID)),
            "response_window_id": response_interpretation.get("response_window_id", ""),
            "response_interpretation_id": response_interpretation.get(
                "response_interpretation_id", ""
            ),
            "response_mode": response_mode,
            "normalizer_id": "fixture_normalizer",
            "normalizer_version": self.version,
            "normalized_payload": response_interpretation.get("interpreted_payload", ""),
            "extracted_at": response_interpretation.get("component_timestamp", 0.0),
            "uncertainty": 0.0,
        }


class SelfConfirmationEvaluator(Evaluator):
    """Evaluates self-confirmation responses for Immediate Recall."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "evaluator_id": "fixture_self_confirm_evaluator",
            "evaluator_version": self.version,
            "response_modes_supported": ["touch"],
            "answer_status_values": [AnswerStatus.CORRECT.value, AnswerStatus.INCORRECT.value],
            "evaluation_status_values": [EvaluationStatus.COMPLETED.value],
            "error_categories_supported": [],
            "abstention_reasons_supported": [],
        }

    def evaluate(
        self,
        domain_normalized_response: dict[str, Any],
        expected_answer: ContentItem,
        context: Any,
    ) -> dict[str, Any]:
        payload = domain_normalized_response.get("normalized_payload", "")
        if payload == "positive":
            answer_status = AnswerStatus.CORRECT.value
            credit = 1.0
        elif payload == "negative":
            answer_status = AnswerStatus.INCORRECT.value
            credit = 0.0
        else:
            answer_status = AnswerStatus.UNEVALUABLE.value
            credit = 0.0
        return {
            "evaluation_id": str(make_id(EvaluationID)),
            "trial_id": context.trial_id,
            "evaluator_id": "fixture_self_confirm_evaluator",
            "evaluator_version": self.version,
            "domain_normalized_response_id": domain_normalized_response.get(
                "domain_normalized_response_id", ""
            ),
            "expected_content_item_id": expected_answer.content_item_id,
            "answer_status": answer_status,
            "evaluation_status": EvaluationStatus.COMPLETED.value,
            "correctness_credit": credit,
            "scope_status": ScopeStatus.IN_SCOPE.value,
        }


class NoOpScheduler(Scheduler):
    """Provider-set placeholder required by the Runtime interface.

    This object satisfies the `Scheduler` protocol expected by `ProviderSet`.
    It is deterministic, performs no scheduling, and raises if ever invoked.
    The Immediate Recall runner makes all item-selection decisions directly and
    does not call a scheduler.
    """

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "scheduler_id": "no_op_scheduler",
            "scheduler_version": self.version,
            "scheduling_strategies_supported": [],
            "difficulty_dimensions_supported": [],
        }

    def select_next(self, scheduling_context: Any) -> dict[str, Any]:
        raise ProviderFailureError(
            "NoOpScheduler was called unexpectedly; the Immediate Recall runner "
            "does not use a scheduler."
        )


class FixtureProviderSet:
    """Convenience builder for the Immediate Recall provider set."""

    def __init__(self, fixture: ImmediateRecallFixture) -> None:
        from mpe.providers import ProviderSet

        self.renderer = FixtureRenderer(fixture)
        self.observation = FixtureObservationProvider(fixture)
        self.interpreter = FixtureResponseInterpreter()
        self.normalizer = FixtureResponseNormalizer()
        self.evaluator = SelfConfirmationEvaluator()
        self.scheduler = NoOpScheduler()
        self.eeg = MockEEGProvider(fixture)
        self.set = ProviderSet(
            renderer=self.renderer,
            observation=self.observation,
            interpreter=self.interpreter,
            normalizer=self.normalizer,
            evaluator=self.evaluator,
            scheduler=self.scheduler,
            eeg=self.eeg,
        )
