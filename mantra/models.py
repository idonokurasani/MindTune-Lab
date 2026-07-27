"""Data models for the Mantra production pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MantraForm:
    """A single inflected form with full pronunciation metadata."""

    form_key: str
    hebrew_with_niqqud: str
    hebrew_plain: str
    transliteration: str
    ipa_phonemes: str
    corrected_phonemes: str
    lexical_stress: int
    vocal_shva: bool = False
    italian_gloss: str = ""
    tts_input: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "form_key": self.form_key,
            "hebrew_with_niqqud": self.hebrew_with_niqqud,
            "hebrew_plain": self.hebrew_plain,
            "transliteration": self.transliteration,
            "ipa_phonemes": self.ipa_phonemes,
            "corrected_phonemes": self.corrected_phonemes,
            "lexical_stress": self.lexical_stress,
            "vocal_shva": self.vocal_shva,
            "italian_gloss": self.italian_gloss,
            "tts_input": self.tts_input,
        }


@dataclass
class Conjugations:
    """All conjugated forms grouped by tense."""

    present: Dict[str, MantraForm] = field(default_factory=dict)
    past: Dict[str, MantraForm] = field(default_factory=dict)
    future: Dict[str, MantraForm] = field(default_factory=dict)

    def as_dict(self) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            "present": {k: v.as_dict() for k, v in self.present.items()},
            "past": {k: v.as_dict() for k, v in self.past.items()},
            "future": {k: v.as_dict() for k, v in self.future.items()},
        }


@dataclass
class MantraMetadata:
    """Top-level metadata for a mantra package."""

    order: int
    hebrew_infinitive_with_niqqud: str
    hebrew_infinitive_plain: str
    italian_translation: str
    transliteration: str
    root: str
    binyan: str
    lexical_stress: int
    source: str
    verification_status: str
    example_hebrew_with_niqqud: str = ""
    example_hebrew_plain: str = ""
    example_italian: str = ""
    example_transliteration: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "hebrew_infinitive_with_niqqud": self.hebrew_infinitive_with_niqqud,
            "hebrew_infinitive_plain": self.hebrew_infinitive_plain,
            "italian_translation": self.italian_translation,
            "transliteration": self.transliteration,
            "root": self.root,
            "binyan": self.binyan,
            "lexical_stress": self.lexical_stress,
            "source": self.source,
            "verification_status": self.verification_status,
            "example_hebrew_with_niqqud": self.example_hebrew_with_niqqud,
            "example_hebrew_plain": self.example_hebrew_plain,
            "example_italian": self.example_italian,
            "example_transliteration": self.example_transliteration,
        }


@dataclass
class CorrectionEntry:
    """One pronunciation correction applied by the override layer."""

    form_key: str
    hebrew_with_niqqud: str
    raw_phonikud_phonemes: str
    corrected_phonemes: str
    raw_stress: int
    corrected_stress: int
    raw_vocal_shva: bool
    corrected_vocal_shva: bool
    correction_applied: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "form_key": self.form_key,
            "hebrew_with_niqqud": self.hebrew_with_niqqud,
            "raw_phonikud_phonemes": self.raw_phonikud_phonemes,
            "corrected_phonemes": self.corrected_phonemes,
            "raw_stress": self.raw_stress,
            "corrected_stress": self.corrected_stress,
            "raw_vocal_shva": self.raw_vocal_shva,
            "corrected_vocal_shva": self.corrected_vocal_shva,
            "correction_applied": self.correction_applied,
            "reason": self.reason,
        }


@dataclass
class MantraPackage:
    """Complete production-ready package for one verb."""

    metadata: MantraMetadata
    infinitive: MantraForm
    conjugations: Conjugations
    example_sentence: str
    corrections: list[CorrectionEntry] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.as_dict(),
            "infinitive": self.infinitive.as_dict(),
            "conjugations": self.conjugations.as_dict(),
            "example_sentence": self.example_sentence,
            "corrections": [c.as_dict() for c in self.corrections],
        }
