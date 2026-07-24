"""Shared pronunciation service wrapper."""
from __future__ import annotations

from pathlib import Path

from ..adapters.phonikud_adapter import phonemize, stress_from_phonemes
from ..models import PronunciationRecord
from ..pronunciation_engine import PronunciationEngine


class PronunciationService:
    """Phonemization and correction service for the entire Hebrew Lab."""

    def __override_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "data" / "hebrew" / "overrides" / "pronunciation.json"

    def __init__(self, override_path: Path | None = None):
        self.engine = PronunciationEngine(
            override_path=override_path or self.__override_path()
        )
        self.engine.load_overrides(self.engine.override_path or self.__override_path())

    def get_pronunciation(self, text: str, context: dict | None = None) -> PronunciationRecord:
        return self.engine.get_pronunciation(text, context=context)

    def add_override(
        self,
        target: str,
        field: str,
        value,
        reason: str = "",
        author: str = "",
    ) -> None:
        self.engine.add_override(target, field, value, reason, author)

    def validate(self, record: PronunciationRecord) -> list[str]:
        return self.engine.validate_pronunciation(record)
