"""Phase 4D Hebrew linguistic specification domain model.

The model separates pointed source text from unpointed TTS input, keeps
linguistic and human-audio review statuses independent, and distinguishes
production core forms from alternate and reference forms.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _normalize(text: str) -> str:
    """Return NFC-normalized Unicode text."""
    return unicodedata.normalize("NFC", text)


def _has_niqqud(text: str) -> bool:
    """Return True if *text* contains Hebrew pointing diacritics."""
    return any("\u0591" <= char <= "\u05c7" for char in text)


def _without_niqqud(text: str) -> str:
    """Return *text* with Hebrew pointing diacritics removed."""
    return "".join(
        char
        for char in _normalize(text)
        if not ("\u0591" <= char <= "\u05c7")
    )


class Binyan(str, Enum):
    """Hebrew binyan (verbal pattern)."""

    PAAL = "paal"
    PIEL = "piel"
    PAUL = "paul"
    HIFIL = "hifil"
    HOFAL = "hofal"
    HITPAEL = "hitpael"
    NIFAL = "nifal"
    NOT_APPLICABLE = "not_applicable"


class GrammaticalSection(str, Enum):
    """Tense/section of a Hebrew verbal form."""

    INFINITIVE = "infinitive"
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"
    IMPERATIVE = "imperative"
    PAST_PARTICIPLE = "past_participle"
    NOT_APPLICABLE = "not_applicable"


class GrammaticalPerson(str, Enum):
    """Grammatical person."""

    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    NOT_APPLICABLE = "not_applicable"


class GrammaticalGender(str, Enum):
    """Grammatical gender."""

    MASCULINE = "masculine"
    FEMININE = "feminine"
    COMMON = "common"
    NOT_APPLICABLE = "not_applicable"


class GrammaticalNumber(str, Enum):
    """Grammatical number."""

    SINGULAR = "singular"
    PLURAL = "plural"
    DUAL = "dual"
    NOT_APPLICABLE = "not_applicable"


class PedagogicalRegister(str, Enum):
    """Pedagogical classification of a form's register."""

    CORE_MODERN = "core_modern"
    LITERARY = "literary"
    ARCHAIC = "archaic"
    SPOKEN = "spoken"
    NOT_APPLICABLE = "not_applicable"


class EntryRole(str, Enum):
    """Role of an entry within the specification fixture."""

    CORE = "core"
    ALTERNATE = "alternate"
    REFERENCE = "reference"
    REJECTED = "rejected"


class LinguisticReviewStatus(str, Enum):
    """Status of linguistic (not audio) review."""

    VERIFIED_CONSENSUS = "verified_consensus"
    HIGH_CONFIDENCE_CANDIDATE = "high_confidence_candidate"
    UNRESOLVED = "unresolved"
    REJECTED = "rejected"
    NOT_REVIEWED = "not_reviewed"


class HumanAudioReviewStatus(str, Enum):
    """Status of human review of a generated audio asset."""

    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    PENDING = "pending"
    NOT_REVIEWED = "not_reviewed"


class AssetKind(str, Enum):
    """Kind of textual asset an entry may carry."""

    TTS_INPUT = "tts_input"
    SOURCE_TEXT = "source_text"
    ITALIAN_PROMPT = "italian_prompt"
    TRANSLITERATION = "transliteration"
    IPA = "ipa"
    NOT_APPLICABLE = "not_applicable"


class EligibilityStatus(str, Enum):
    """Eligibility of a source or form for production use."""

    PRODUCTION_APPROVED = "production_approved"
    REFERENCE_ONLY = "reference_only"
    PRIVATE_RESEARCH_ONLY = "private_research_only"
    REJECTED = "rejected"


class RejectionReasonCode(str, Enum):
    """Canonical reason for rejecting or flagging an entry."""

    PHONETIC_MISMATCH = "phonetic_mismatch"
    NIQQUD_ERROR = "niqqud_error"
    SOURCE_CONFLICT = "source_conflict"
    OUT_OF_SCOPE = "out_of_scope"
    STYLE = "style"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class HebrewTextPair:
    """Pointed source text and explicit unpointed TTS text for Hebrew.

    *source_text* preserves niqqud and is treated as the authoritative source.
    *tts_text* is the unpointed string fed to the Aaron TTS voice.
    """

    source_text: str
    tts_text: str
    script: str = "he"

    def __post_init__(self) -> None:
        source = _normalize(self.source_text)
        tts = _normalize(self.tts_text)
        script = _normalize(self.script)
        if not source:
            raise ValueError("HebrewTextPair.source_text is required")
        if not tts:
            raise ValueError("HebrewTextPair.tts_text is required")
        if not _has_niqqud(source):
            raise ValueError(
                f"HebrewTextPair.source_text must be pointed: {source!r}"
            )
        if _has_niqqud(tts):
            raise ValueError(
                f"HebrewTextPair.tts_text must be unpointed: {tts!r}"
            )
        if script != "he":
            raise ValueError(
                f"HebrewTextPair.script must be 'he': {script!r}"
            )
        object.__setattr__(self, "source_text", source)
        object.__setattr__(self, "tts_text", tts)
        object.__setattr__(self, "script", script)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_text": self.source_text,
            "tts_text": self.tts_text,
            "script": self.script,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HebrewTextPair":
        return cls(
            source_text=data["source_text"],
            tts_text=data["tts_text"],
            script=data.get("script", "he"),
        )


@dataclass(frozen=True)
class ItalianPrompt:
    """Italian prompt intended for the Giuseppe TTS voice.

    The actual TTS voice is resolved from the audio profile at execution time;
    this object stores only the Italian text and language code so that voice
    changes do not require editing linguistic specifications.
    """

    text: str
    language: str = "it"

    def __post_init__(self) -> None:
        text = _normalize(self.text)
        language = _normalize(self.language)
        if not text:
            raise ValueError("ItalianPrompt.text is required")
        if language != "it":
            raise ValueError(
                f"ItalianPrompt.language must be 'it': {language!r}"
            )
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "language", language)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItalianPrompt":
        return cls(
            text=data["text"],
            language=data.get("language", "it"),
        )


@dataclass(frozen=True)
class LinguisticProvenance:
    """Provenance metadata for a linguistic specification."""

    source_id: str
    source_url: str
    retrieved_date: str
    license: str
    trust_tier: int
    source_eligibility: EligibilityStatus

    def __post_init__(self) -> None:
        source_id = _normalize(self.source_id)
        source_url = _normalize(self.source_url)
        retrieved_date = _normalize(self.retrieved_date)
        license_ = _normalize(self.license)
        if not source_id:
            raise ValueError("LinguisticProvenance.source_id is required")
        if not source_url:
            raise ValueError("LinguisticProvenance.source_url is required")
        if not retrieved_date:
            raise ValueError("LinguisticProvenance.retrieved_date is required")
        if not license_:
            raise ValueError("LinguisticProvenance.license is required")
        if not 1 <= self.trust_tier <= 5:
            raise ValueError(
                f"LinguisticProvenance.trust_tier must be 1-5: {self.trust_tier}"
            )
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "retrieved_date", retrieved_date)
        object.__setattr__(self, "license", license_)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "retrieved_date": self.retrieved_date,
            "license": self.license,
            "trust_tier": self.trust_tier,
            "source_eligibility": self.source_eligibility.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LinguisticProvenance":
        return cls(
            source_id=data["source_id"],
            source_url=data["source_url"],
            retrieved_date=data["retrieved_date"],
            license=data["license"],
            trust_tier=int(data["trust_tier"]),
            source_eligibility=EligibilityStatus(data["source_eligibility"]),
        )


@dataclass(frozen=True)
class PedagogicalEntry:
    """A single reviewed Hebrew form with Italian prompt and review status."""

    entry_id: str
    role: EntryRole
    hebrew: HebrewTextPair
    italian: ItalianPrompt
    section: GrammaticalSection
    person: GrammaticalPerson
    gender: GrammaticalGender
    number: GrammaticalNumber
    register: PedagogicalRegister
    linguistic_review_status: LinguisticReviewStatus
    human_audio_review_status: HumanAudioReviewStatus
    rejection_reason: RejectionReasonCode = RejectionReasonCode.NOT_APPLICABLE
    phonemes: str = ""
    stress_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        entry_id = _normalize(self.entry_id)
        phonemes = _normalize(self.phonemes)
        if not entry_id:
            raise ValueError("PedagogicalEntry.entry_id is required")
        if self.stress_index < 0:
            raise ValueError(
                f"PedagogicalEntry.stress_index must be non-negative: {self.stress_index}"
            )
        if self.role == EntryRole.REJECTED:
            if self.rejection_reason == RejectionReasonCode.NOT_APPLICABLE:
                raise ValueError(
                    "Rejected PedagogicalEntry must specify a rejection_reason"
                )
        object.__setattr__(self, "entry_id", entry_id)
        object.__setattr__(self, "phonemes", phonemes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "role": self.role.value,
            "hebrew": self.hebrew.to_dict(),
            "italian": self.italian.to_dict(),
            "section": self.section.value,
            "person": self.person.value,
            "gender": self.gender.value,
            "number": self.number.value,
            "register": self.register.value,
            "linguistic_review_status": self.linguistic_review_status.value,
            "human_audio_review_status": self.human_audio_review_status.value,
            "rejection_reason": self.rejection_reason.value,
            "phonemes": self.phonemes,
            "stress_index": self.stress_index,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PedagogicalEntry":
        return cls(
            entry_id=data["entry_id"],
            role=EntryRole(data["role"]),
            hebrew=HebrewTextPair.from_dict(data["hebrew"]),
            italian=ItalianPrompt.from_dict(data["italian"]),
            section=GrammaticalSection(data["section"]),
            person=GrammaticalPerson(data["person"]),
            gender=GrammaticalGender(data["gender"]),
            number=GrammaticalNumber(data["number"]),
            register=PedagogicalRegister(data["register"]),
            linguistic_review_status=LinguisticReviewStatus(
                data["linguistic_review_status"]
            ),
            human_audio_review_status=HumanAudioReviewStatus(
                data["human_audio_review_status"]
            ),
            rejection_reason=RejectionReasonCode(
                data.get("rejection_reason", RejectionReasonCode.NOT_APPLICABLE.value)
            ),
            phonemes=data.get("phonemes", ""),
            stress_index=int(data.get("stress_index", 0)),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class HebrewVerbSpecification:
    """Phase 4D Hebrew linguistic specification for one verb."""

    spec_id: str
    schema_version: str
    specification_version: str
    curriculum_version: str
    verb_id: str
    approved_lemma: HebrewTextPair
    root: str
    binyan: Binyan
    primary_italian_gloss: str
    secondary_italian_glosses: tuple[str, ...]
    pedagogical_register: PedagogicalRegister
    expected_transliteration: str
    provenance: LinguisticProvenance
    entries: tuple[PedagogicalEntry, ...]
    content_checksum: str
    notes: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:  # noqa: C901
        spec_id = _normalize(self.spec_id)
        schema_version = _normalize(self.schema_version)
        specification_version = _normalize(self.specification_version)
        curriculum_version = _normalize(self.curriculum_version)
        verb_id = _normalize(self.verb_id)
        root = _normalize(self.root)
        primary_italian_gloss = _normalize(self.primary_italian_gloss)
        expected_transliteration = _normalize(self.expected_transliteration)
        content_checksum = _normalize(self.content_checksum)
        notes = _normalize(self.notes)
        created_at = _normalize(self.created_at)
        if not spec_id:
            raise ValueError("HebrewVerbSpecification.spec_id is required")
        if not schema_version:
            raise ValueError("HebrewVerbSpecification.schema_version is required")
        if not specification_version:
            raise ValueError("HebrewVerbSpecification.specification_version is required")
        if not curriculum_version:
            raise ValueError("HebrewVerbSpecification.curriculum_version is required")
        if not verb_id:
            raise ValueError("HebrewVerbSpecification.verb_id is required")
        if not root:
            raise ValueError("HebrewVerbSpecification.root is required")
        if not primary_italian_gloss:
            raise ValueError("HebrewVerbSpecification.primary_italian_gloss is required")
        if not content_checksum:
            raise ValueError(
                "HebrewVerbSpecification.content_checksum is required"
            )
        if not self.entries:
            raise ValueError(
                f"HebrewVerbSpecification {spec_id!r} must contain at least one entry"
            )
        ids = [entry.entry_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError(
                f"HebrewVerbSpecification {spec_id!r} contains duplicate entry IDs"
            )
        sorted_entries = tuple(sorted(self.entries, key=lambda e: e.entry_id))
        object.__setattr__(self, "spec_id", spec_id)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "specification_version", specification_version)
        object.__setattr__(self, "curriculum_version", curriculum_version)
        object.__setattr__(self, "verb_id", verb_id)
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "primary_italian_gloss", primary_italian_gloss)
        object.__setattr__(self, "expected_transliteration", expected_transliteration)
        object.__setattr__(self, "content_checksum", content_checksum)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "entries", sorted_entries)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "spec_id": self.spec_id,
            "schema_version": self.schema_version,
            "specification_version": self.specification_version,
            "curriculum_version": self.curriculum_version,
            "verb_id": self.verb_id,
            "approved_lemma": self.approved_lemma.to_dict(),
            "root": self.root,
            "binyan": self.binyan.value,
            "primary_italian_gloss": self.primary_italian_gloss,
            "secondary_italian_glosses": list(self.secondary_italian_glosses),
            "pedagogical_register": self.pedagogical_register.value,
            "expected_transliteration": self.expected_transliteration,
            "provenance": self.provenance.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
            "content_checksum": self.content_checksum,
        }
        if self.notes:
            data["notes"] = self.notes
        if self.created_at:
            data["created_at"] = self.created_at
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HebrewVerbSpecification":
        entries = sorted(
            (PedagogicalEntry.from_dict(entry) for entry in data.get("entries", [])),
            key=lambda e: e.entry_id,
        )
        return cls(
            spec_id=data["spec_id"],
            schema_version=data["schema_version"],
            specification_version=data.get("specification_version", "1.0.0"),
            curriculum_version=data.get("curriculum_version", "1.0.0"),
            verb_id=data["verb_id"],
            approved_lemma=HebrewTextPair.from_dict(data["approved_lemma"]),
            root=data["root"],
            binyan=Binyan(data["binyan"]),
            primary_italian_gloss=data.get("primary_italian_gloss", ""),
            secondary_italian_glosses=tuple(data.get("secondary_italian_glosses", [])),
            pedagogical_register=PedagogicalRegister(
                data.get("pedagogical_register", PedagogicalRegister.CORE_MODERN.value)
            ),
            expected_transliteration=data.get("expected_transliteration", ""),
            provenance=LinguisticProvenance.from_dict(data["provenance"]),
            entries=tuple(entries),
            content_checksum=data["content_checksum"],
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass(frozen=True)
class SpecificationValidationResult:
    """Result of validating a Hebrew verb specification fixture."""

    valid: bool
    errors: tuple[str, ...]
    checksum_match: bool
    schema_version_supported: bool
