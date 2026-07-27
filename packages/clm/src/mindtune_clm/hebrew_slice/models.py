"""Canonical dataclasses for the CLM-06 Hebrew adaptive vertical slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HebrewAdaptiveItem:
    """A single validated Hebrew curriculum item ready for adaptive presentation."""

    item_id: str
    curriculum_version: str
    source_id: str
    lemma: str
    lemma_pointed: str
    lemma_unpointed: str
    root: str
    binyan: str
    tense: str
    mood: str
    person: str
    gender: str
    number: str
    subject: str
    register: str
    canonical_pointed: str
    canonical_unpointed: str
    transliteration: str
    pointed_context_sentence: str
    unpointed_context_sentence: str
    italian_gloss: str
    natural_italian: str
    morphology_provenance: str
    pointing_provenance: str
    help_references: list[str]
    linguistic_validation_status: str
    pronunciation_review_status: str
    required_audio_asset_ids: list[str]
    accepted_alternates: list[str]
    error_confusion_set: list[str]
    usage_classification: str = "unknown"
    paradigm_form_key: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "curriculum_version": self.curriculum_version,
            "source_id": self.source_id,
            "lemma": self.lemma,
            "lemma_pointed": self.lemma_pointed,
            "lemma_unpointed": self.lemma_unpointed,
            "root": self.root,
            "binyan": self.binyan,
            "tense": self.tense,
            "mood": self.mood,
            "person": self.person,
            "gender": self.gender,
            "number": self.number,
            "subject": self.subject,
            "register": self.register,
            "canonical_pointed": self.canonical_pointed,
            "canonical_unpointed": self.canonical_unpointed,
            "transliteration": self.transliteration,
            "pointed_context_sentence": self.pointed_context_sentence,
            "unpointed_context_sentence": self.unpointed_context_sentence,
            "italian_gloss": self.italian_gloss,
            "natural_italian": self.natural_italian,
            "morphology_provenance": self.morphology_provenance,
            "pointing_provenance": self.pointing_provenance,
            "help_references": list(self.help_references),
            "linguistic_validation_status": self.linguistic_validation_status,
            "pronunciation_review_status": self.pronunciation_review_status,
            "required_audio_asset_ids": list(self.required_audio_asset_ids),
            "accepted_alternates": list(self.accepted_alternates),
            "error_confusion_set": list(self.error_confusion_set),
            "usage_classification": self.usage_classification,
            "paradigm_form_key": self.paradigm_form_key,
        }


@dataclass(frozen=True)
class HebrewTrial:
    """A prepared Hebrew adaptive trial."""

    trial_id: str
    presentation_id: str
    prompt_id: str
    item: HebrewAdaptiveItem
    trial_type: str
    direction: str
    prompt_text: str
    choices: tuple[str, ...] | None
    expected: str
    control_state_id: str
    control_state_snapshot: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "presentation_id": self.presentation_id,
            "prompt_id": self.prompt_id,
            "item_id": self.item.item_id,
            "trial_type": self.trial_type,
            "direction": self.direction,
            "prompt_text": self.prompt_text,
            "choices": list(self.choices) if self.choices is not None else None,
            "expected": self.expected,
            "pointed_hebrew": self.item.canonical_pointed,
            "unpointed_hebrew": self.item.canonical_unpointed,
            "italian_meaning": self.item.natural_italian,
            "control_state_id": self.control_state_id,
            "control_state_snapshot": dict(self.control_state_snapshot),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class HebrewResponse:
    """A learner's submitted response to a Hebrew trial."""

    response_id: str
    trial_id: str
    item_id: str
    prompt_id: str
    presentation_id: str
    raw_response: str
    normalized_response: str
    response_semantic_timestamp: float
    response_time_ms: float
    confidence: int
    hint_used: bool
    replay_count: int
    audio_assistance_level: float
    response_mode: str = "typed"

    def as_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "trial_id": self.trial_id,
            "item_id": self.item_id,
            "prompt_id": self.prompt_id,
            "presentation_id": self.presentation_id,
            "raw_response": self.raw_response,
            "normalized_response": self.normalized_response,
            "response_semantic_timestamp": self.response_semantic_timestamp,
            "response_time_ms": self.response_time_ms,
            "confidence": self.confidence,
            "hint_used": self.hint_used,
            "replay_count": self.replay_count,
            "audio_assistance_level": self.audio_assistance_level,
            "response_mode": self.response_mode,
        }


@dataclass(frozen=True)
class HebrewScore:
    """Deterministic per-dimension Hebrew response score."""

    overall: str
    lemma: str
    root: str
    binyan: str
    tense_mood: str
    person: str
    gender: str
    number: str
    pointed_orthography: str
    unpointed_orthography: str
    meaning: str
    contextual_agreement: str
    accepted_alternate_used: bool
    error_codes: list[str]
    version: str = "1.0.0"

    def as_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "lemma": self.lemma,
            "root": self.root,
            "binyan": self.binyan,
            "tense_mood": self.tense_mood,
            "person": self.person,
            "gender": self.gender,
            "number": self.number,
            "pointed_orthography": self.pointed_orthography,
            "unpointed_orthography": self.unpointed_orthography,
            "meaning": self.meaning,
            "contextual_agreement": self.contextual_agreement,
            "accepted_alternate_used": self.accepted_alternate_used,
            "error_codes": list(self.error_codes),
            "version": self.version,
        }


@dataclass(frozen=True)
class HebrewPedagogicalDecision:
    """A bounded, evented pedagogical action chosen for the next cycle."""

    action: str
    next_item_id: str | None
    next_trial_type: str | None
    assistance_delta: float
    reason_codes: list[str]
    repeat_same_item: bool = False
    interleave_item_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "next_item_id": self.next_item_id,
            "next_trial_type": self.next_trial_type,
            "assistance_delta": self.assistance_delta,
            "reason_codes": list(self.reason_codes),
            "repeat_same_item": self.repeat_same_item,
            "interleave_item_id": self.interleave_item_id,
        }


@dataclass
class HebrewItemLearningState:
    """Item-level learning state used by the adaptive selector."""

    item_id: str
    presentations: int = 0
    attempts: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    last_result: str = ""
    last_seen_semantic_time: float | None = None
    response_times_ms: list[float] = field(default_factory=list)
    confidence_values: list[int] = field(default_factory=list)
    morphology_errors: dict[str, int] = field(default_factory=dict)
    pointing_errors: dict[str, int] = field(default_factory=dict)
    current_difficulty_estimate: float = 0.5
    current_mastery_estimate: float = 0.0
    scheduled_review_position: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    assistance_history: list[float] = field(default_factory=list)
    active_learning_eligible: bool = True
    reference_only: bool = False
    linguistic_validation_status: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "presentations": self.presentations,
            "attempts": self.attempts,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "last_result": self.last_result,
            "last_seen_semantic_time": self.last_seen_semantic_time,
            "response_times_ms": list(self.response_times_ms),
            "confidence_values": list(self.confidence_values),
            "morphology_errors": dict(self.morphology_errors),
            "pointing_errors": dict(self.pointing_errors),
            "current_difficulty_estimate": self.current_difficulty_estimate,
            "current_mastery_estimate": self.current_mastery_estimate,
            "scheduled_review_position": self.scheduled_review_position,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "assistance_history": list(self.assistance_history),
            "active_learning_eligible": self.active_learning_eligible,
            "reference_only": self.reference_only,
            "linguistic_validation_status": self.linguistic_validation_status,
        }


@dataclass(frozen=True)
class HebrewAdaptiveEvent:
    """A typed CLM-06 slice event with explicit causal links."""

    event_id: str
    event_type: str
    session_id: str
    timestamp: float
    component: str
    payload: dict[str, Any]
    provenance: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "component": self.component,
            "payload": dict(self.payload),
            "provenance": list(self.provenance),
        }
