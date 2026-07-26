"""Provider set for the Hebrew immediate-recall vertical slice.

This module wires the domain-specific ``HebrewDomainAdapter`` into the
generic MPE provider contracts.  Hebrew logic lives here, inside the adapter
boundary, and never leaks into the generic runtime.
"""

from __future__ import annotations

from typing import Any

from mpe.domain.base import BehavioralEvidence
from mpe.domains.hebrew.adapter import HebrewDomainAdapter
from mpe.enums import AnswerStatus, EvaluationStatus, ResponseMode, ScopeStatus
from mpe.protocol.eeg_provider import MockEEGProvider
from mpe.protocol.fixture_minimal import ImmediateRecallFixture
from mpe.protocol.providers import (
    FixtureObservationProvider,
    FixtureResponseInterpreter,
    NoOpScheduler,
)
from mpe.providers import ContentItem, DomainNormalizer, Evaluator, ProviderSet, Renderer, TrialContext
from mpe.types import DomainNormalizedResponseID, EvaluationID, RenderedStimulusID, make_id


class HebrewRenderer(Renderer):
    """Deterministic renderer producing stable media handles for Hebrew items."""

    def __init__(self, adapter: HebrewDomainAdapter, version: str = "1.0.0") -> None:
        self.adapter = adapter
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "renderer_id": "hebrew_renderer",
            "renderer_version": self.version,
            "formats_supported": ["hebrew_text"],
            "voices_supported": [],
            "rate_range": {"min": 1.0, "max": 1.0, "default": 1.0},
            "latency_estimate_ms": 0,
            "streaming_support": False,
        }

    def render(self, request: dict[str, Any]) -> dict[str, Any]:
        content_item_id = request.get("content_item_id")
        if not isinstance(content_item_id, str):
            raise ValueError("HebrewRenderer requires a string content_item_id")
        item = self.adapter.get_content_item(content_item_id)
        if item is None:
            raise ValueError(f"No Hebrew content item for {content_item_id!r}")
        prompt = self.adapter.build_prompt(item)
        return {
            "rendered_stimulus_id": str(make_id(RenderedStimulusID)),
            "stimulus_request_id": request.get("stimulus_request_id", ""),
            "renderer_id": "hebrew_renderer",
            "renderer_version": self.version,
            "media_handle": f"hebrew://prompt/{prompt.prompt_id}",
            "duration": 1.0,
            "rendered_at": request.get("requested_at", 0.0),
            "asset_version": item.content_version,
            "asset_role": request.get("asset_role", "prompt"),
        }


class HebrewNormalizer(DomainNormalizer):
    """Domain-specific normalizer delegating to the Hebrew adapter.

    The adapter's normalization rules (whitespace, Unicode, Hebrew punctuation)
    are applied here.  The generic runtime sees only the resulting typed-text
    payload and a stable normalizer identity.
    """

    def __init__(self, adapter: HebrewDomainAdapter, version: str = "1.0.0") -> None:
        self.adapter = adapter
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "normalizer_id": "hebrew_normalizer",
            "normalizer_version": self.version,
            "normalization_rules_version": "1.0.0",
            "content_types_supported": ["hebrew_immediate_recall"],
        }

    def normalize(self, response_interpretation: dict[str, Any]) -> dict[str, Any]:
        raw = str(response_interpretation.get("interpreted_payload", ""))
        normalized = self.adapter.normalize(raw)
        return {
            "domain_normalized_response_id": str(make_id(DomainNormalizedResponseID)),
            "response_window_id": response_interpretation.get("response_window_id", ""),
            "response_interpretation_id": response_interpretation.get(
                "response_interpretation_id", ""
            ),
            "response_mode": ResponseMode.TYPED.value,
            "normalizer_id": "hebrew_normalizer",
            "normalizer_version": self.version,
            "normalized_payload": normalized,
            "extracted_at": response_interpretation.get("component_timestamp", 0.0),
            "uncertainty": 0.0,
        }


class HebrewEvaluator(Evaluator):
    """Domain-specific evaluator delegating to the Hebrew adapter.

    The expected ``ContentItem`` carries the stable content_item_id; the
    adapter resolves the Hebrew item, re-derives the deterministic prompt, and
    evaluates the normalized payload.  The returned dictionary is fully
    compatible with the generic ``evaluation_completed`` event contract.
    """

    def __init__(self, adapter: HebrewDomainAdapter, version: str = "1.0.0") -> None:
        self.adapter = adapter
        self.version = version

    def capabilities(self) -> dict[str, Any]:
        return {
            "evaluator_id": "hebrew_evaluator",
            "evaluator_version": self.version,
            "response_modes_supported": ["typed"],
            "answer_status_values": list(AnswerStatus.values()),
            "evaluation_status_values": list(EvaluationStatus.values()),
            "error_categories_supported": [],
            "abstention_reasons_supported": [],
        }

    def evaluate(
        self,
        domain_normalized_response: dict[str, Any],
        expected_answer: ContentItem,
        context: TrialContext,
    ) -> dict[str, Any]:
        item = self.adapter.get_content_item(expected_answer.content_item_id)
        if item is None:
            return {
                "evaluation_id": str(make_id(EvaluationID)),
                "trial_id": context.trial_id,
                "evaluator_id": "hebrew_evaluator",
                "evaluator_version": self.version,
                "domain_normalized_response_id": domain_normalized_response.get(
                    "domain_normalized_response_id", ""
                ),
                "expected_content_item_id": expected_answer.content_item_id,
                "answer_status": AnswerStatus.UNEVALUABLE.value,
                "evaluation_status": EvaluationStatus.FAILED.value,
                "failure_reason": "hebrew_content_item_not_found",
                "error_category": "unknown",
                "correctness_credit": 0.0,
                "scope_status": ScopeStatus.OUT_OF_SCOPE.value,
            }

        prompt = self.adapter.build_prompt(item)
        normalized = str(domain_normalized_response.get("normalized_payload", ""))
        evaluation = self.adapter.evaluate_response(
            prompt,
            normalized,
            timing={"latency": 0.0},
        )
        evidence = self.adapter.behavioral_evidence(evaluation)
        return self._to_evaluation_dict(context.trial_id, evaluation, evidence, domain_normalized_response)

    def _to_evaluation_dict(
        self,
        trial_id: str,
        evaluation: Any,
        evidence: BehavioralEvidence,
        normalized: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "evaluation_id": str(make_id(EvaluationID)),
            "trial_id": trial_id,
            "evaluator_id": "hebrew_evaluator",
            "evaluator_version": self.version,
            "domain_normalized_response_id": normalized.get("domain_normalized_response_id", ""),
            "expected_content_item_id": evidence.content_item_id,
            "answer_status": evidence.correctness_status,
            "evaluation_status": evidence.evaluation_status,
            "correctness_credit": 1.0 if evaluation.is_correct else 0.0,
            "scope_status": ScopeStatus.IN_SCOPE.value,
        }


class HebrewFixtureProviderSet:
    """Convenience builder for the Hebrew immediate-recall provider set."""

    def __init__(self, fixture: ImmediateRecallFixture, hebrew_fixture_items: list[HebrewContentItem]) -> None:
        adapter = HebrewDomainAdapter(hebrew_fixture_items)
        self.renderer = HebrewRenderer(adapter)
        self.observation = FixtureObservationProvider(fixture)
        self.interpreter = FixtureResponseInterpreter()
        self.normalizer = HebrewNormalizer(adapter)
        self.evaluator = HebrewEvaluator(adapter)
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
