"""Typed Hebrew content model for immediate recall."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HebrewContentItem:
    """A single Hebrew vocabulary item usable for immediate recall.

    Keeps source preservation (``source_reference``) separate from optional
    reconstructed linguistic metadata.  All items carry a stable
    deterministic identifier and an explicit content version.
    """

    content_item_id: str
    hebrew_target: str
    accepted_answers: tuple[str, ...]
    italian_cue: str
    transliteration: str | None = None
    linguistic_metadata: dict[str, Any] = field(default_factory=dict)
    source_reference: str = ""
    content_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.content_item_id:
            raise ValueError("content_item_id is required")
        if not self.hebrew_target:
            raise ValueError("hebrew_target is required")
        if not self.accepted_answers:
            raise ValueError("accepted_answers must contain at least one answer")
        if not self.italian_cue:
            raise ValueError("italian_cue is required")


@dataclass(frozen=True)
class HebrewPromptInstance:
    """Deterministic immediate-recall prompt: Italian cue -> Hebrew answer."""

    prompt_id: str
    content_item_id: str
    content_version: str
    italian_cue: str
    prompt_direction: str = "italian_cue_to_hebrew_target"
    target_language: str = "he"
    accepted_answers: tuple[str, ...] = field(default_factory=tuple)

    def cue_text(self) -> str:
        """Return the prompt text shown to the learner."""
        return self.italian_cue
