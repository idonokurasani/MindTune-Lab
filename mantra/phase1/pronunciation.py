"""Provider pronunciation lexicon for reviewed TTS entries.

Each entry records the canonical learner-facing text, the provider-specific
synthesis text, expected pronunciation, explicit sheva decisions, the selected
audio checksum, and the reviewer decision.  The primary key is the tuple
(lexical_item, conjugated_form, provider, voice, provider_model).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .utils import normalize_unicode


@dataclass
class PronunciationEntry:
    """One reviewed pronunciation decision for a single lexical form."""

    lexical_item: str
    conjugated_form: str
    provider: str
    voice: str
    provider_model: str = ""
    display_text: str = ""
    normalized_text: str = ""
    tts_text: str = ""
    expected_pronunciation: str = ""
    sheva_decisions: list[dict[str, Any]] = field(default_factory=list)
    selected_audio_checksum: str = ""
    human_review_status: str = "pending"
    reviewer_decision: str = "pending"
    diagnostic_source_variant: str = ""
    review_notes: str = ""

    def key(self) -> str:
        """Return a stable string key for this entry."""
        return f"{self.lexical_item}|{self.conjugated_form}|{self.provider}|{self.voice}|{self.provider_model}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PronunciationEntry":
        return cls(
            lexical_item=data["lexical_item"],
            conjugated_form=data["conjugated_form"],
            provider=data["provider"],
            voice=data["voice"],
            provider_model=data.get("provider_model", ""),
            display_text=data.get("display_text", ""),
            normalized_text=data.get("normalized_text", ""),
            tts_text=data.get("tts_text", ""),
            expected_pronunciation=data.get("expected_pronunciation", ""),
            sheva_decisions=data.get("sheva_decisions", []),
            selected_audio_checksum=data.get("selected_audio_checksum", ""),
            human_review_status=data.get("human_review_status", "pending"),
            reviewer_decision=data.get("reviewer_decision", "pending"),
            diagnostic_source_variant=data.get("diagnostic_source_variant", ""),
            review_notes=data.get("review_notes", ""),
        )


class PronunciationLexicon:
    """On-disk JSON pronunciation lexicon keyed by provider/voice/form."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else None
        self.entries: dict[str, PronunciationEntry] = {}
        if self.path and self.path.exists():
            self.load()

    def load(self) -> None:
        """Load entries from the JSON file at ``self.path``."""
        if not self.path or not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.entries = {
            k: PronunciationEntry.from_dict(v) for k, v in data.get("entries", {}).items()
        }

    def save(self) -> None:
        """Persist entries to the JSON file at ``self.path``."""
        if not self.path:
            raise RuntimeError("PronunciationLexicon has no path")
        payload = {
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(
        self,
        lexical_item: str,
        conjugated_form: str,
        provider: str,
        voice: str,
        provider_model: str = "",
    ) -> PronunciationEntry | None:
        key = f"{lexical_item}|{conjugated_form}|{provider}|{voice}|{provider_model}"
        return self.entries.get(key)

    def add_or_update(self, entry: PronunciationEntry) -> None:
        entry.display_text = normalize_unicode(entry.display_text)
        entry.normalized_text = normalize_unicode(entry.normalized_text)
        entry.tts_text = normalize_unicode(entry.tts_text)
        self.entries[entry.key()] = entry

    def list_entries(self) -> list[PronunciationEntry]:
        return list(self.entries.values())
