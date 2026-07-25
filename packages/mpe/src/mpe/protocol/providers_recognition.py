"""Provider implementations for the Recognition comparative probe.

These providers are deterministic, do not access any external service, and exist
only to satisfy the Runtime's provider contract with opaque fixture data.
"""

from __future__ import annotations

from typing import Any

from mpe.enums import (
    AnswerStatus,
    EvaluationStatus,
    InterpretationType,
    ObservationType,
    ResponseMode,
    ScopeStatus,
)
from mpe.errors import ProviderFailureError, ProviderTimeoutError
from mpe.protocol.fixture_recognition import RecognitionFixture
from mpe.protocol.providers import NoOpScheduler
from mpe.providers import (
    ContentItem,
    DomainNormalizer,
    Evaluator,
    ObservationProvider,
    ProviderSet,
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


class RecognitionRenderer(Renderer):
    """Deterministic fixture renderer for Recognition choice assets."""

    def __init__(self, fixture: RecognitionFixture, version: str = "1.0.0") -> None:
        self.fixture = fixture
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "renderer_id": "fixture_recognition_renderer",
            "renderer_version": self.version,
            "formats_supported": ["fixture_media"],
            "voices_supported": [],
            "rate_range": {"min": 1.0, "max": 1.0, "default": 1.0},
            "latency_estimate_ms": 0,
            "streaming_support": False,
        }

    def render(self, request: dict[str, Any]) -> dict[str, Any]:
        content_item_id = request.get("content_item_id")
        role = request.get("asset_role", "choice_0")
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
            "renderer_id": "fixture_recognition_renderer",
            "renderer_version": self.version,
            "media_handle": asset.media_handle,
            "duration": 1.0,
            "rendered_at": request.get("requested_at", 0.0),
            "asset_version": asset.version,
            "asset_role": asset.role,
        }


class RecognitionObservationProvider(ObservationProvider):
    """Deterministic discrete-choice observation provider for Recognition."""

    def __init__(self, fixture: RecognitionFixture, version: str = "1.0.0") -> None:
        self.fixture = fixture
        self.version = version
        self._pending: list[dict[str, Any]] = []
        self._failing = False
        self._timeout = False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": "fixture_recognition_choice",
            "provider_version": self.version,
            "observation_types_supported": [ObservationType.TOUCH_INPUT.value],
            "device_id": "fixture_button_0",
            "quality_dimensions_supported": {},
            "quality_flags_supported": [],
            "quality_model_id": "fixture_qm",
            "quality_model_version": "1.0.0",
            "latency_estimate_ms": 0,
        }

    def inject(self, text: str) -> None:
        """Stage a discrete-choice observation.

        `text` is expected as '<latency>:<selected_choice_index>'.
        """
        if ":" in text:
            latency_str, value = text.split(":", 1)
            latency = float(latency_str)
        else:
            latency = 0.0
            value = text
        self._pending.append({
            "observation_id": str(make_id(ObservationID)),
            "observation_type": ObservationType.TOUCH_INPUT.value,
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
            raise ProviderTimeoutError("fixture recognition observation timed out")
        if self._failing:
            raise ProviderFailureError("fixture recognition observation forced failure")
        observations = self._pending
        self._pending = []
        return observations


class RecognitionResponseInterpreter(ResponseInterpreter):
    """Passthrough interpreter mapping selected choice index to SELECTED_OPTION."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "interpreter_id": "fixture_recognition_interpreter",
            "interpreter_version": self.version,
            "response_modes_supported": [ResponseMode.TOUCH.value],
            "output_schema": "selected_option",
        }

    def interpret(self, captured_response: dict[str, Any]) -> dict[str, Any]:
        payload = captured_response.get("captured_payload", "")
        return {
            "response_interpretation_id": str(make_id(ResponseInterpretationID)),
            "response_window_id": captured_response.get("response_window_id", ""),
            "captured_response_id": captured_response.get("captured_response_id", ""),
            "interpreter_id": "fixture_recognition_interpreter",
            "interpreter_version": self.version,
            "interpreted_payload": payload,
            "interpretation_confidence": 1.0,
            "interpretation_type": InterpretationType.SELECTED_OPTION.value,
            "component_timestamp": captured_response.get("captured_at", 0.0),
        }


class RecognitionNormalizer(DomainNormalizer):
    """Passthrough normalizer for Recognition selected choices."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "normalizer_id": "fixture_recognition_normalizer",
            "normalizer_version": self.version,
            "normalization_rules_version": "1.0.0",
            "content_types_supported": ["fixture_recognition_choice"],
        }

    def normalize(self, response_interpretation: dict[str, Any]) -> dict[str, Any]:
        return {
            "domain_normalized_response_id": str(make_id(DomainNormalizedResponseID)),
            "response_window_id": response_interpretation.get("response_window_id", ""),
            "response_interpretation_id": response_interpretation.get(
                "response_interpretation_id", ""
            ),
            "response_mode": ResponseMode.TOUCH.value,
            "normalizer_id": "fixture_recognition_normalizer",
            "normalizer_version": self.version,
            "normalized_payload": response_interpretation.get("interpreted_payload", ""),
            "extracted_at": response_interpretation.get("component_timestamp", 0.0),
            "uncertainty": 0.0,
        }


class RecognitionEvaluator(Evaluator):
    """Evaluates Recognition discrete-choice selections."""

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "evaluator_id": "fixture_recognition_evaluator",
            "evaluator_version": self.version,
            "response_modes_supported": [ResponseMode.TOUCH.value],
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
        selected = domain_normalized_response.get("normalized_payload", "")
        try:
            selected_index = int(selected)
        except (TypeError, ValueError):
            selected_index = -1

        correct_index = expected_answer.metadata.get("correct_choice_index")
        if correct_index is None:
            raise ProviderFailureError(
                "RecognitionEvaluator expected correct_choice_index in ContentItem metadata"
            )

        if selected_index == correct_index:
            answer_status = AnswerStatus.CORRECT.value
            credit = 1.0
        else:
            answer_status = AnswerStatus.INCORRECT.value
            credit = 0.0

        return {
            "evaluation_id": str(make_id(EvaluationID)),
            "trial_id": context.trial_id,
            "evaluator_id": "fixture_recognition_evaluator",
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


class RecognitionProviderSet:
    """Convenience builder for the Recognition provider set."""

    def __init__(self, fixture: RecognitionFixture) -> None:
        self.renderer = RecognitionRenderer(fixture)
        self.observation = RecognitionObservationProvider(fixture)
        self.interpreter = RecognitionResponseInterpreter()
        self.normalizer = RecognitionNormalizer()
        self.evaluator = RecognitionEvaluator()
        self.scheduler: Scheduler = NoOpScheduler()
        self.set = ProviderSet(
            renderer=self.renderer,
            observation=self.observation,
            interpreter=self.interpreter,
            normalizer=self.normalizer,
            evaluator=self.evaluator,
            scheduler=self.scheduler,
        )
