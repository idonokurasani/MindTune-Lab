"""Generic domain-adapter boundary for the MindTune Protocol Engine.

A domain adapter is a typed, domain-specific plug-in that resolves content,
builds deterministic prompts, evaluates raw responses, and translates the
result into domain-neutral behavioral evidence.  The generic MPE runtime
consumes only the neutral evidence; it never sees domain-specific labels,
roots, or grading rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from mpe.enums import AnswerStatus, EvaluationStatus

ContentItemT = TypeVar("ContentItemT")
PromptInstanceT = TypeVar("PromptInstanceT")
RawResponseT = TypeVar("RawResponseT")


@dataclass(frozen=True)
class BehavioralEvidence:
    """Domain-neutral evidence produced from one evaluation.

    This is the only information the generic runtime may consume from a
    domain adapter.  It contains correctness, latency, omission status, and
    stable identifiers, but no domain-specific grading details.
    """

    correctness_status: str
    response_latency: float
    omission: bool
    hesitation: bool
    evaluation_status: str
    normalized_error_category: str | None
    content_item_id: str
    prompt_id: str


@dataclass(frozen=True)
class DomainEvaluationResult:
    """Typed result of evaluating one raw response against a prompt.

    This stays inside the adapter boundary.  The adapter exposes it to the
    runtime only through ``behavioral_evidence``.
    """

    evaluation_id: str
    prompt_id: str
    content_item_id: str
    raw_response: str
    normalized_response: str
    answer_status: AnswerStatus
    evaluation_status: EvaluationStatus
    is_omitted: bool
    is_correct: bool
    normalized_error_category: str | None = None
    latency: float = 0.0


class DomainAdapter(Protocol, Generic[ContentItemT, PromptInstanceT, RawResponseT]):  # type: ignore[misc]
    """Typed boundary between domain-specific content and the generic runtime.

    Implementations are conceptually equivalent to:

        get_content_item(content_item_id)
        build_prompt(content_item, context)
        evaluate_response(prompt, raw_response, timing)
        behavioral_evidence(evaluation)
    """

    def get_content_item(self, content_item_id: str) -> ContentItemT | None:
        """Resolve a content item by its stable identifier."""
        ...

    def build_prompt(
        self,
        content_item: ContentItemT,
        context: dict[str, Any] | None = None,
    ) -> PromptInstanceT:
        """Build a deterministic prompt instance for the given content item."""
        ...

    def evaluate_response(
        self,
        prompt: PromptInstanceT,
        raw_response: RawResponseT,
        timing: dict[str, Any] | None = None,
    ) -> DomainEvaluationResult:
        """Evaluate a raw response against the prompt."""
        ...

    def behavioral_evidence(
        self,
        evaluation: DomainEvaluationResult,
    ) -> BehavioralEvidence:
        """Translate a domain evaluation into domain-neutral evidence."""
        ...
