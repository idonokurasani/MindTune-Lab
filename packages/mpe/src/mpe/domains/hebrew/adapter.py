"""Hebrew immediate-recall domain adapter.

The adapter lives entirely outside the generic MPE runtime.  It resolves
Hebrew content, builds deterministic prompts, normalises and evaluates typed
Hebrew responses, and returns only domain-neutral behavioral evidence.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from mpe.domain.base import BehavioralEvidence, DomainEvaluationResult
from mpe.domains.hebrew.models import HebrewContentItem, HebrewPromptInstance
from mpe.domains.hebrew.normalization import is_empty_response, normalize_hebrew_response
from mpe.enums import AnswerStatus, EvaluationStatus


class HebrewDomainAdapter:
    """Typed adapter for Hebrew immediate-recall content.

    Implements the conceptual ``DomainAdapter[HebrewContentItem,
    HebrewPromptInstance, str]`` contract.
    """

    def __init__(self, items: list[HebrewContentItem]) -> None:
        self._items: dict[str, HebrewContentItem] = {
            item.content_item_id: item for item in items
        }

    def get_content_item(self, content_item_id: str) -> HebrewContentItem | None:
        """Resolve a Hebrew content item by its stable identifier."""
        return self._items.get(content_item_id)

    def normalize(self, raw_response: str | None) -> str:
        """Apply Hebrew-specific response normalization rules."""
        return normalize_hebrew_response(raw_response)

    def build_prompt(
        self,
        content_item: HebrewContentItem,
        context: dict[str, Any] | None = None,
    ) -> HebrewPromptInstance:
        """Build a deterministic Italian-cue -> Hebrew-target prompt.

        The prompt identifier is derived from stable content fields, so the
        same content item and direction always yield the same ``prompt_id``.
        """
        _ = context  # reserved for future runtime context; not used for identity
        return HebrewPromptInstance(
            prompt_id=self._derive_prompt_id(content_item),
            content_item_id=content_item.content_item_id,
            content_version=content_item.content_version,
            italian_cue=content_item.italian_cue,
            accepted_answers=content_item.accepted_answers,
        )

    def evaluate_response(
        self,
        prompt: HebrewPromptInstance,
        raw_response: str,
        timing: dict[str, Any] | None = None,
    ) -> DomainEvaluationResult:
        """Evaluate a raw response against a Hebrew prompt.

        The result is typed and domain-specific, but it is only exposed to the
        generic runtime through ``behavioral_evidence``.
        """
        latency = float(timing.get("latency", 0.0) if timing else 0.0)
        normalized = normalize_hebrew_response(raw_response)
        omitted = is_empty_response(raw_response)

        if omitted:
            is_correct = False
            answer_status = AnswerStatus.UNEVALUABLE
            evaluation_status = EvaluationStatus.COMPLETED
            error_category = "omitted"
        else:
            accepted = {normalize_hebrew_response(a) for a in prompt.accepted_answers}
            is_correct = normalized in accepted
            answer_status = AnswerStatus.CORRECT if is_correct else AnswerStatus.INCORRECT
            evaluation_status = EvaluationStatus.COMPLETED
            error_category = None if is_correct else "incorrect"

        return DomainEvaluationResult(
            evaluation_id=f"he-eval-{uuid.uuid4()}",
            prompt_id=prompt.prompt_id,
            content_item_id=prompt.content_item_id,
            raw_response=raw_response,
            normalized_response=normalized,
            answer_status=answer_status,
            evaluation_status=evaluation_status,
            is_omitted=omitted,
            is_correct=is_correct,
            normalized_error_category=error_category,
            latency=latency,
        )

    def behavioral_evidence(
        self,
        evaluation: DomainEvaluationResult,
    ) -> BehavioralEvidence:
        """Translate a Hebrew evaluation into domain-neutral behavioral evidence."""
        return BehavioralEvidence(
            correctness_status=evaluation.answer_status.value,
            response_latency=evaluation.latency,
            omission=evaluation.is_omitted,
            hesitation=evaluation.latency > 2.0,
            evaluation_status=evaluation.evaluation_status.value,
            normalized_error_category=evaluation.normalized_error_category,
            content_item_id=evaluation.content_item_id,
            prompt_id=evaluation.prompt_id,
        )

    def _derive_prompt_id(self, content_item: HebrewContentItem) -> str:
        """Return a deterministic prompt id for ``content_item``.

        The id is a short SHA-256 prefix over a canonical JSON of stable
        content fields, which makes it independent of runtime-generated ids.
        """
        canonical = {
            "content_item_id": content_item.content_item_id,
            "content_version": content_item.content_version,
            "italian_cue": content_item.italian_cue,
            "prompt_direction": "italian_cue_to_hebrew_target",
            "target_language": "he",
        }
        encoded = json.dumps(canonical, sort_keys=True, ensure_ascii=True).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()[:32]
        return f"he-prompt-{content_item.content_item_id}-{digest}"
