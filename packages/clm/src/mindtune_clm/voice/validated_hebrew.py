"""Validated Hebrew pedagogical item adapter for CLM-03B.

This module reconciles the existing ``hebrew/`` linguistic engine with the
CLM-03B SpeechGen pipeline.  It does not generate new morphology or replace
``hebrew/``; it only consumes already approved forms and constructs a
production-safe voice request.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

try:
    from hebrew.normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
except ModuleNotFoundError:
    from mindtune_clm.voice.hebrew import normalize_source

    _COMBINING_MARKS = re.compile(
        r"[\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]"
    )

    def normalize_hebrew(text: str) -> str:
        """Fallback: NFC, maqaf to space, collapse whitespace."""
        text = normalize_source(text)
        text = text.replace("\u05be", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def strip_niqqud(text: str) -> str:
        """Fallback: remove Hebrew combining marks."""
        return _COMBINING_MARKS.sub("", text)

    _HEBREW_LETTER = re.compile(r"[\u05D0-\u05EA]")
    _HOLAM = "\u05b9"
    _QUBUTS = "\u05bb"
    _VAV = "\u05d5"
    _YOD = "\u05d9"

    def standard_unvocalized(vocalized: str) -> str:
        """Fallback mater-insertion for holam/qubuts before a following consonant."""
        chars = list(unicodedata.normalize("NFD", vocalized))
        result: list[str] = []
        i = 0
        n = len(chars)
        while i < n:
            c = chars[i]
            if not _HEBREW_LETTER.match(c):
                result.append(c)
                i += 1
                continue
            marks: list[str] = []
            j = i + 1
            while j < n and _COMBINING_MARKS.match(chars[j]):
                marks.append(chars[j])
                j += 1
            has_next = False
            k = j
            while k < n:
                if _HEBREW_LETTER.match(chars[k]):
                    has_next = True
                    break
                k += 1
            result.append(c)
            if has_next and c not in (_VAV, _YOD) and (_HOLAM in marks or _QUBUTS in marks):
                result.append(_VAV)
            i = j
        return strip_niqqud("".join(result))

from mindtune_clm.voice.hebrew import (
    HEBREW_BLOCK,
    HEBREW_COMBINING_MARKS,
    has_niqqud,
    normalize_source,
    validate_source_text,
    validate_tts_text,
    validate_word_separation,
)
from mindtune_clm.voice.hebrew_validation import (
    HumanReviewPendingError,
    InconsistentMorphologyError,
    MalformedUnicodeError,
    MissingCanonicalHebrewError,
    PointingProvenanceError,
    RejectedCurriculumError,
    UnresolvedMorphologyConflictError,
    UnvalidatedGeneratedFormError,
)
from mindtune_clm.voice.models import PedagogicalVoiceRequest, sha256_text


def _canonical_json(payload: dict[str, Any]) -> str:
    """Return a deterministic compact JSON string with sorted keys."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _validation_checksum(fields: dict[str, Any]) -> str:
    """Deterministic checksum of the canonical linguistic identity fields."""
    return hashlib.sha256(_canonical_json(fields).encode("utf-8")).hexdigest()


def _stable_item_id(
    curriculum_version: str,
    form_key: str,
    canonical_pointed_surface: str,
    canonical_unpointed_surface: str,
) -> str:
    """Return a deterministic stable id for an approved form."""
    payload = {
        "curriculum_version": curriculum_version,
        "form_key": form_key,
        "canonical_pointed_surface": canonical_pointed_surface,
        "canonical_unpointed_surface": canonical_unpointed_surface,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]


def _extract_hebrew_mark_order(text: str) -> list[str]:
    """Return Hebrew base letters and combining marks in code-point order."""
    return [c for c in text if HEBREW_BLOCK.match(c) or HEBREW_COMBINING_MARKS.match(c)]


@dataclass(frozen=True)
class ValidatedHebrewPedagogicalItem:
    """A fully validated Hebrew form ready for CLM-03B Aaron synthesis.

    The dataclass captures the complete upstream provenance needed to prove
    that a given ``tts_text`` is not arbitrary free-text Hebrew, but a
    curriculum-approved, consensus-backed, pointed surface form.
    """

    item_id: str
    curriculum_version: str
    source_entry_ids: tuple[str, ...]
    canonical_lemma: str
    pointed_lemma: str
    unpointed_lemma: str
    root: str
    binyan: str
    tense: str
    mood: str
    person: str
    gender: str
    number: str
    subject: str
    register: str
    formal_or_contemporary: str
    canonical_pointed_surface: str
    canonical_unpointed_surface: str
    transliteration: str
    pointed_contextual_sentence: str
    unpointed_contextual_sentence: str
    italian_gloss: str
    italian_sentence: str
    morphology_source_ids: tuple[str, ...]
    conflict_status: str
    pointing_provenance: tuple[str, ...]
    help_references: tuple[str, ...]
    curriculum_status: str
    linguistic_validation_status: str
    human_review_status: str
    unicode_normalization_status: str
    validation_checksum: str
    unpointed_exception_approved: bool = False
    unpointed_override_notes: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:  # noqa: C901
        """Run all production validation checks; raise typed exceptions on failure."""
        if self.curriculum_status != "approved":
            raise RejectedCurriculumError(
                f"curriculum_status={self.curriculum_status!r}; only 'approved' forms pass production"
            )

        if self.linguistic_validation_status not in (
            "validated",
            "verified_consensus",
            "approved",
        ):
            raise UnvalidatedGeneratedFormError(
                f"linguistic_validation_status={self.linguistic_validation_status!r}"
            )

        if self.conflict_status:
            raise UnresolvedMorphologyConflictError(
                f"unresolved morphology conflicts: {self.conflict_status}"
            )

        if not self.canonical_pointed_surface:
            raise MissingCanonicalHebrewError("canonical_pointed_surface is empty")

        if not has_niqqud(self.canonical_pointed_surface):
            raise MissingCanonicalHebrewError(
                "canonical_pointed_surface is missing Hebrew niqqud"
            )

        for name, text in (
            ("canonical_pointed_surface", self.canonical_pointed_surface),
            ("pointed_lemma", self.pointed_lemma),
        ):
            normalized = normalize_source(text)
            if _extract_hebrew_mark_order(normalized) != _extract_hebrew_mark_order(text):
                raise MalformedUnicodeError(
                    f"{name} combining-mark order changed during NFC normalization"
                )

        if self.unicode_normalization_status != "NFC" and self.unicode_normalization_status:
            raise MalformedUnicodeError(
                f"unicode_normalization_status={self.unicode_normalization_status!r}"
            )

        expected_unpointed = standard_unvocalized(self.canonical_pointed_surface)
        if (
            expected_unpointed != self.canonical_unpointed_surface
            and self.canonical_unpointed_surface
        ):
            raise InconsistentMorphologyError(
                f"standard_unvocalized(pointed)={expected_unpointed!r} "
                f"does not match unpointed={self.canonical_unpointed_surface!r}"
            )

        if has_niqqud(self.canonical_unpointed_surface):
            raise InconsistentMorphologyError(
                "canonical_unpointed_surface contains Hebrew niqqud"
            )

        if not self.pointing_provenance:
            raise PointingProvenanceError("pointing_provenance is empty")

        if self.human_review_status == "rejected":
            raise HumanReviewPendingError(
                f"human_review_status={self.human_review_status!r}"
            )

    def _canonical_fields(self) -> dict[str, Any]:
        """Fields that participate in the stable validation checksum."""
        return {
            "item_id": self.item_id,
            "curriculum_version": self.curriculum_version,
            "source_entry_ids": list(self.source_entry_ids),
            "canonical_lemma": self.canonical_lemma,
            "canonical_pointed_surface": self.canonical_pointed_surface,
            "canonical_unpointed_surface": self.canonical_unpointed_surface,
            "root": self.root,
            "binyan": self.binyan,
            "tense": self.tense,
            "mood": self.mood,
            "person": self.person,
            "gender": self.gender,
            "number": self.number,
            "morphology_source_ids": list(self.morphology_source_ids),
            "conflict_status": self.conflict_status,
            "curriculum_status": self.curriculum_status,
            "linguistic_validation_status": self.linguistic_validation_status,
        }

    @classmethod
    def from_verb_form(
        cls,
        form: Any,
        *,
        curriculum_version: str = "1.0.0",
        pointed_contextual_sentence: str | None = None,
        unpointed_contextual_sentence: str | None = None,
        italian_gloss: str = "",
        italian_sentence: str = "",
        unpointed_exception_approved: bool = False,
        unpointed_override_notes: str = "",
    ) -> "ValidatedHebrewPedagogicalItem":
        """Consume an existing ``hebrew.models.VerbForm`` without re-conjugating."""
        as_dict = getattr(form, "as_dict", None)
        if not callable(as_dict):
            raise TypeError("form must provide an as_dict() method")
        form_data: dict[str, Any] = as_dict()
        return cls.from_approved_json(
            form_data,
            curriculum_version=curriculum_version,
            pointed_contextual_sentence=pointed_contextual_sentence,
            unpointed_contextual_sentence=unpointed_contextual_sentence,
            italian_gloss=italian_gloss,
            italian_sentence=italian_sentence,
            unpointed_exception_approved=unpointed_exception_approved,
            unpointed_override_notes=unpointed_override_notes,
        )

    @classmethod
    def from_approved_json(  # noqa: C901
        cls,
        data: dict[str, Any],
        *,
        form_key: str | None = None,
        item_id: str | None = None,
        curriculum_version: str = "1.0.0",
        pointed_contextual_sentence: str | None = None,
        unpointed_contextual_sentence: str | None = None,
        italian_gloss: str = "",
        italian_sentence: str = "",
        unpointed_exception_approved: bool = False,
        unpointed_override_notes: str = "",
    ) -> "ValidatedHebrewPedagogicalItem":
        """Consume an approved JSON form dict or full approved JSON document.

        When ``data`` is the top-level approved document, ``form_key`` selects
        the form under ``data["paradigm"]["forms"]``.
        """
        form: dict[str, Any]
        if "paradigm" in data and isinstance(data.get("paradigm"), dict):
            if form_key is None:
                raise ValueError("form_key is required when passing a full approved JSON document")
            forms = data["paradigm"]["forms"]
            if form_key not in forms:
                raise ValueError(f"form_key {form_key!r} not found in approved forms")
            form = forms[form_key]
        elif "surface_vocalized" in data:
            form = data
        else:
            raise ValueError(
                "data must be either a full approved JSON document with 'paradigm' "
                "or a form dict containing 'surface_vocalized'"
            )

        form_key_value = form.get("form_key") or form_key or "unknown"
        pointed_lemma = normalize_hebrew(form.get("lemma_vocalized", ""))
        unpointed_lemma = form.get("lemma_plain", "")
        canonical_pointed_surface = normalize_hebrew(form.get("surface_vocalized", ""))
        canonical_unpointed_surface = form.get("surface_plain", "")
        root = form.get("root", "")
        binyan = form.get("binyan", "")

        source_evidence = form.get("source_evidence", [])
        if not isinstance(source_evidence, list):
            source_evidence = []

        applied_overrides = form.get("applied_overrides", [])
        if not isinstance(applied_overrides, list):
            applied_overrides = []

        morphology_source_ids: list[str] = []
        pointing_provenance: list[str] = []
        for ev in source_evidence:
            sid = ev.get("source") or ev.get("source_id", "")
            if sid:
                morphology_source_ids.append(sid)
                pointing_provenance.append(sid)
        for ov in applied_overrides:
            sid = ov.get("source") or ov.get("source_id", "") or "manual_override"
            if sid:
                morphology_source_ids.append(sid)
                pointing_provenance.append(sid)

        source_entry_ids = [form_key_value]
        source_entry_ids.extend(morphology_source_ids)
        source_entry_ids = list(dict.fromkeys(source_entry_ids))

        unresolved_conflicts = form.get("unresolved_conflicts", [])
        if not isinstance(unresolved_conflicts, list):
            unresolved_conflicts = []
        conflict_status = ",".join(
            c.get("field_name", "") for c in unresolved_conflicts if c.get("field_name")
        )

        approval_status = form.get("approval_status", "candidate")
        curriculum_status = (
            "approved" if approval_status == "approved" else form.get("curriculum_status", approval_status)
        )
        linguistic_validation_status = (
            "validated"
            if approval_status == "approved"
            else form.get("linguistic_status", "candidate")
        )
        human_review_status = form.get("reviewer_status") or "pending"

        stable_id = item_id or _stable_item_id(
            curriculum_version,
            form_key_value,
            canonical_pointed_surface,
            canonical_unpointed_surface,
        )

        checksum = _validation_checksum(
            {
                "item_id": stable_id,
                "curriculum_version": curriculum_version,
                "source_entry_ids": source_entry_ids,
                "canonical_lemma": pointed_lemma or "",
                "canonical_pointed_surface": canonical_pointed_surface,
                "canonical_unpointed_surface": canonical_unpointed_surface,
                "root": root,
                "binyan": binyan,
                "tense": form.get("tense", ""),
                "mood": form.get("mood", ""),
                "person": form.get("person", ""),
                "gender": form.get("gender", ""),
                "number": form.get("number", ""),
                "morphology_source_ids": morphology_source_ids,
                "conflict_status": conflict_status,
                "curriculum_status": curriculum_status,
                "linguistic_validation_status": linguistic_validation_status,
            }
        )

        return cls(
            item_id=stable_id,
            curriculum_version=curriculum_version,
            source_entry_ids=tuple(source_entry_ids),
            canonical_lemma=pointed_lemma or unpointed_lemma,
            pointed_lemma=pointed_lemma,
            unpointed_lemma=unpointed_lemma,
            root=root,
            binyan=binyan,
            tense=form.get("tense", ""),
            mood=form.get("mood", ""),
            person=form.get("person", ""),
            gender=form.get("gender", ""),
            number=form.get("number", ""),
            subject=form.get("subject", ""),
            register=form.get("usage_classification") or form.get("register", "") or "core_modern",
            formal_or_contemporary=form.get("formality") or "contemporary",
            canonical_pointed_surface=canonical_pointed_surface,
            canonical_unpointed_surface=canonical_unpointed_surface,
            transliteration=form.get("transliteration", ""),
            pointed_contextual_sentence=pointed_contextual_sentence or canonical_pointed_surface,
            unpointed_contextual_sentence=unpointed_contextual_sentence or canonical_unpointed_surface,
            italian_gloss=italian_gloss,
            italian_sentence=italian_sentence,
            morphology_source_ids=tuple(morphology_source_ids),
            conflict_status=conflict_status,
            pointing_provenance=tuple(pointing_provenance),
            help_references=tuple(form.get("help_references", [])) if isinstance(form.get("help_references"), list) else (),
            curriculum_status=curriculum_status,
            linguistic_validation_status=linguistic_validation_status,
            human_review_status=human_review_status,
            unicode_normalization_status="NFC",
            validation_checksum=checksum,
            unpointed_exception_approved=unpointed_exception_approved,
            unpointed_override_notes=unpointed_override_notes,
        )

    def to_voice_request(
        self,
        source_text: str | None = None,
        tts_text: str | None = None,
    ) -> PedagogicalVoiceRequest:
        """Return a production ``PedagogicalVoiceRequest`` for Aaron.

        Defaults:
          - ``source_text`` = fully pointed contextual sentence.
          - ``tts_text`` = fully pointed surface form.

        An unpointed override is only allowed when the item was explicitly
        marked with ``unpointed_exception_approved=True``.
        """
        source_text = normalize_source(source_text or self.pointed_contextual_sentence)
        tts_text = normalize_source(tts_text or self.canonical_pointed_surface)

        validate_source_text(source_text)
        validate_tts_text(
            tts_text,
            source_text,
            unpointed_exception_approved=self.unpointed_exception_approved,
        )
        validate_word_separation(source_text)

        grammatical_metadata = {
            "item_id": self.item_id,
            "curriculum_version": self.curriculum_version,
            "source_entry_ids": list(self.source_entry_ids),
            "canonical_lemma": self.canonical_lemma,
            "pointed_lemma": self.pointed_lemma,
            "unpointed_lemma": self.unpointed_lemma,
            "root": self.root,
            "binyan": self.binyan,
            "tense": self.tense,
            "mood": self.mood,
            "person": self.person,
            "gender": self.gender,
            "number": self.number,
            "subject": self.subject,
            "register": self.register,
            "formal_or_contemporary": self.formal_or_contemporary,
            "canonical_pointed_surface": self.canonical_pointed_surface,
            "canonical_unpointed_surface": self.canonical_unpointed_surface,
            "transliteration": self.transliteration,
            "morphology_source_ids": list(self.morphology_source_ids),
            "conflict_status": self.conflict_status,
            "pointing_provenance": list(self.pointing_provenance),
            "help_references": list(self.help_references),
            "curriculum_status": self.curriculum_status,
            "linguistic_validation_status": self.linguistic_validation_status,
            "human_review_status": self.human_review_status,
            "unicode_normalization_status": self.unicode_normalization_status,
            "validation_checksum": self.validation_checksum,
        }

        semantic_metadata = {
            "italian_gloss": self.italian_gloss,
            "italian_sentence": self.italian_sentence,
            "unpointed_contextual_sentence": self.unpointed_contextual_sentence,
            "unpointed_exception_approved": self.unpointed_exception_approved,
            "unpointed_override_notes": self.unpointed_override_notes,
        }

        return PedagogicalVoiceRequest(
            request_id=self.item_id,
            language="he",
            locale="he-IL",
            voice_display_name="Aaron",
            provider_voice_id="Aaron",
            source_text=source_text,
            tts_text=tts_text,
            source_text_checksum=sha256_text(source_text),
            tts_text_checksum=sha256_text(tts_text),
            grammatical_metadata=grammatical_metadata,
            semantic_metadata=semantic_metadata,
            register=self.register,
            source_curriculum_item_id=self.item_id,
            source_render_cycle_id="",
            source_actuation_receipt_id="",
            normalization_policy_version="1.0.0",
            synthesis_parameter_version="1.0.0",
            unpointed_exception_approved=self.unpointed_exception_approved,
            unpointed_override_notes=self.unpointed_override_notes,
        )
