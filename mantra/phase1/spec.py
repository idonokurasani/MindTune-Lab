"""Typed Mantra specification and validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .utils import normalize_unicode


class OutputFormat(str, Enum):
    """Canonical audio output formats."""

    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


@dataclass(frozen=True)
class MantraForm:
    """A single inflected Hebrew form with pronunciation metadata."""

    form_key: str
    hebrew_with_niqqud: str
    hebrew_plain: str = ""
    vocalized: str = ""
    transliteration: str = ""
    ipa_phonemes: str = ""
    stress_syllable_index: int = 0
    stress_override: int | None = None
    pronunciation_override: str | None = None
    italian_gloss: str = ""
    tts_input: str = ""
    person: str | None = None
    number: str | None = None
    gender: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.form_key:
            raise ValueError("MantraForm.form_key is required")
        if not self.hebrew_with_niqqud:
            raise ValueError("MantraForm.hebrew_with_niqqud is required")
        object.__setattr__(self, "hebrew_with_niqqud", normalize_unicode(self.hebrew_with_niqqud))
        object.__setattr__(self, "italian_gloss", normalize_unicode(self.italian_gloss))
        object.__setattr__(self, "transliteration", normalize_unicode(self.transliteration))
        if self.pronunciation_override is not None:
            object.__setattr__(self, "pronunciation_override", normalize_unicode(self.pronunciation_override))
        if not self.tts_input:
            object.__setattr__(self, "tts_input", self.hebrew_with_niqqud)
        else:
            object.__setattr__(self, "tts_input", normalize_unicode(self.tts_input))
        if not self.hebrew_plain:
            object.__setattr__(
                self,
                "hebrew_plain",
                "".join(
                    c
                    for c in self.hebrew_with_niqqud
                    if "\u0590" <= c <= "\u05ff" and not ("\u0591" <= c <= "\u05c7")
                ),
            )
        else:
            object.__setattr__(self, "hebrew_plain", normalize_unicode(self.hebrew_plain))
        if not self.vocalized:
            object.__setattr__(self, "vocalized", self.hebrew_with_niqqud)
        else:
            object.__setattr__(self, "vocalized", normalize_unicode(self.vocalized))
        if self.stress_override is not None and self.stress_override < 0:
            raise ValueError("stress_override must be non-negative")

    def effective_tts_input(self) -> str:
        """Return the pronunciation to be synthesized, respecting overrides."""
        return self.pronunciation_override or self.tts_input

    def effective_stress(self) -> int:
        """Return the effective stress syllable index."""
        return self.stress_override if self.stress_override is not None else self.stress_syllable_index

    def to_dict(self) -> dict[str, Any]:
        return {
            "form_key": self.form_key,
            "hebrew_with_niqqud": self.hebrew_with_niqqud,
            "hebrew_plain": self.hebrew_plain,
            "vocalized": self.vocalized,
            "transliteration": self.transliteration,
            "ipa_phonemes": self.ipa_phonemes,
            "stress_syllable_index": self.stress_syllable_index,
            "stress_override": self.stress_override,
            "pronunciation_override": self.pronunciation_override,
            "italian_gloss": self.italian_gloss,
            "tts_input": self.tts_input,
            "person": self.person,
            "number": self.number,
            "gender": self.gender,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GrammaticalGroup:
    """A tense/conjugation group containing ordered forms."""

    tense: str
    forms: list[MantraForm]
    label_he: str = ""
    label_it: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tense:
            raise ValueError("GrammaticalGroup.tense is required")
        object.__setattr__(self, "tense", normalize_unicode(self.tense))
        object.__setattr__(self, "label_he", normalize_unicode(self.label_he))
        object.__setattr__(self, "label_it", normalize_unicode(self.label_it))
        if not self.forms:
            raise ValueError(f"Group {self.tense!r} must contain at least one form")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tense": self.tense,
            "label_he": self.label_he,
            "label_it": self.label_it,
            "forms": [f.to_dict() for f in self.forms],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PauseConfig:
    """Pause durations in milliseconds."""

    opening_ms: int = 500
    closing_ms: int = 500
    between_forms_ms: int = 500
    between_groups_ms: int = 900
    between_cycles_ms: int = 1200
    segment_pause_ms: int = 300
    italian_cue_pause_ms: int = 300

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith("_ms") and value < 0:
                raise ValueError(f"{name} must be non-negative, got {value}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "opening_ms": self.opening_ms,
            "closing_ms": self.closing_ms,
            "between_forms_ms": self.between_forms_ms,
            "between_groups_ms": self.between_groups_ms,
            "between_cycles_ms": self.between_cycles_ms,
            "segment_pause_ms": self.segment_pause_ms,
            "italian_cue_pause_ms": self.italian_cue_pause_ms,
        }


@dataclass(frozen=True)
class SpeechConfig:
    """TTS provider configuration."""

    provider: str = "speechgen"
    locale: str = "he-IL"
    voice: str = "Avri"
    rate: float = 1.0
    pitch: float = 0.0
    format: str = "wav"
    emotion: str = "good"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError("SpeechConfig.provider is required")
        if not self.voice:
            raise ValueError("SpeechConfig.voice is required")
        if self.rate <= 0.0:
            raise ValueError("rate must be positive")
        if self.format not in {f.value for f in OutputFormat}:
            raise ValueError(f"unsupported format: {self.format!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "locale": self.locale,
            "voice": self.voice,
            "rate": self.rate,
            "pitch": self.pitch,
            "format": self.format,
            "emotion": self.emotion,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MantraSpecification:
    """Complete validated mantra specification."""

    id: str
    version: str
    language: str
    verb_id: str
    hebrew_infinitive: str
    lexical_root: str
    binyan: str
    groups: list[GrammaticalGroup]
    repetitions_per_form: int = 1
    repetitions_per_cycle: int = 1
    cycles: int = 1
    speech: SpeechConfig = field(default_factory=SpeechConfig)
    pauses: PauseConfig = field(default_factory=PauseConfig)
    output_format: str = "wav"
    build_seed: str = ""
    include_italian_cue: bool = True
    include_grammatical_labels: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:  # noqa: C901
        if not self.id:
            raise ValueError("MantraSpecification.id is required")
        if not self.version:
            raise ValueError("MantraSpecification.version is required")
        if not self.language:
            raise ValueError("MantraSpecification.language is required")
        if not self.verb_id:
            raise ValueError("MantraSpecification.verb_id is required")
        if not self.hebrew_infinitive:
            raise ValueError("MantraSpecification.hebrew_infinitive is required")
        object.__setattr__(self, "hebrew_infinitive", normalize_unicode(self.hebrew_infinitive))
        object.__setattr__(self, "lexical_root", normalize_unicode(self.lexical_root))
        object.__setattr__(self, "binyan", normalize_unicode(self.binyan))
        object.__setattr__(self, "build_seed", normalize_unicode(self.build_seed))
        if not self.groups:
            raise ValueError("MantraSpecification.groups must not be empty")
        if self.repetitions_per_form < 0:
            raise ValueError("repetitions_per_form must be non-negative")
        if self.repetitions_per_cycle < 1:
            raise ValueError("repetitions_per_cycle must be at least 1")
        if self.cycles < 1:
            raise ValueError("cycles must be at least 1")
        if self.output_format not in {f.value for f in OutputFormat}:
            raise ValueError(f"unsupported output_format: {self.output_format!r}")

    def base_seconds_per_char(self) -> float:
        """Heuristic base duration per character used for planned durations."""
        # A calm learning cadence: roughly 0.18 s per Hebrew/Italian character,
        # adjusted inversely by speech rate.
        return 0.18 / max(self.speech.rate, 0.1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "language": self.language,
            "verb_id": self.verb_id,
            "hebrew_infinitive": self.hebrew_infinitive,
            "lexical_root": self.lexical_root,
            "binyan": self.binyan,
            "groups": [g.to_dict() for g in self.groups],
            "repetitions_per_form": self.repetitions_per_form,
            "repetitions_per_cycle": self.repetitions_per_cycle,
            "cycles": self.cycles,
            "speech": self.speech.to_dict(),
            "pauses": self.pauses.to_dict(),
            "output_format": self.output_format,
            "build_seed": self.build_seed,
            "include_italian_cue": self.include_italian_cue,
            "include_grammatical_labels": self.include_grammatical_labels,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MantraSpecification":
        """Reconstruct a validated MantraSpecification from a dict."""
        speech = SpeechConfig(**data.get("speech", {}))
        pauses = PauseConfig(**data.get("pauses", {}))
        groups = [
            GrammaticalGroup(
                tense=g["tense"],
                label_he=g.get("label_he", ""),
                label_it=g.get("label_it", ""),
                forms=[MantraForm(**f) for f in g["forms"]],
                metadata=g.get("metadata", {}),
            )
            for g in data.get("groups", [])
        ]
        return cls(
            id=data["id"],
            version=data["version"],
            language=data.get("language", "he-IL"),
            verb_id=data["verb_id"],
            hebrew_infinitive=data["hebrew_infinitive"],
            lexical_root=data.get("lexical_root", ""),
            binyan=data.get("binyan", ""),
            groups=groups,
            repetitions_per_form=data.get("repetitions_per_form", 1),
            repetitions_per_cycle=data.get("repetitions_per_cycle", 1),
            cycles=data.get("cycles", 1),
            speech=speech,
            pauses=pauses,
            output_format=data.get("output_format", "wav"),
            build_seed=data.get("build_seed", ""),
            include_italian_cue=data.get("include_italian_cue", True),
            include_grammatical_labels=data.get("include_grammatical_labels", False),
            metadata=data.get("metadata", {}),
        )
