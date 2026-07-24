"""Typed learner-answer diagnosis schema and comparison logic."""
from __future__ import annotations

from .models import ValidationResult, VerbForm
from .morphology import morphology_features_to_form_key
from .normalization import strip_niqqud, standard_unvocalized


def _feature_diff(submitted_form: VerbForm, expected_form: VerbForm) -> str:
    """Return the first differing grammatical feature, if any."""
    for attr in ("tense", "person", "gender", "number", "binyan", "root"):
        if getattr(submitted_form, attr) != getattr(expected_form, attr):
            return attr
    return ""


def _to_form(surface: str, base: VerbForm) -> VerbForm:
    """Build a minimal VerbForm from a user string, copying features from base."""
    return VerbForm(
        surface_vocalized=surface,
        surface_plain=standard_unvocalized(surface),
        tense=base.tense,
        person=base.person,
        gender=base.gender,
        number=base.number,
        binyan=base.binyan,
        root=base.root,
    )


def diagnose_answer(
    submitted: str,
    expected_form: VerbForm,
    accepted_variants: list[str] | None = None,
    known_forms: dict[str, VerbForm] | None = None,
) -> ValidationResult:
    """Diagnose a learner answer against an expected gold form.

    Returns status + diagnosis_type + affected_feature.
    """
    variants = accepted_variants or []
    known = known_forms or {}
    result = ValidationResult(
        submitted=submitted,
        expected=expected_form.surface_vocalized,
        accepted_variants=variants,
    )

    if submitted == expected_form.surface_vocalized:
        result.status = "correct"
        result.diagnosis_type = "exact"
        result.score = 1.0
        return result

    submitted_plain = strip_niqqud(submitted)
    expected_plain = strip_niqqud(expected_form.surface_vocalized)

    if submitted_plain == expected_plain:
        result.status = "missing_niqqud" if submitted == submitted_plain else "spelling_error"
        result.diagnosis_type = "niqqud_only" if submitted == submitted_plain else "spelling_only"
        result.affected_feature = "niqqud"
        result.score = 0.8
        return result

    if any(submitted == v or submitted_plain == strip_niqqud(v) for v in variants):
        result.status = "valid_alternate_spelling"
        result.diagnosis_type = "valid_alternate"
        result.score = 1.0
        return result

    # Try to match against other forms in the paradigm for feature diagnosis
    for key, candidate in known.items():
        if strip_niqqud(candidate.surface_vocalized) == submitted_plain:
            submitted_form = _to_form(submitted, candidate)
            diff = _feature_diff(submitted_form, expected_form)
            result.status = f"wrong_{diff}" if diff else "valid_alternate_spelling"
            result.diagnosis_type = diff or "valid_alternate"
            result.affected_feature = diff or "spelling"
            result.score = 0.0 if diff else 1.0
            return result

    # Root / binyan mismatch: if plain form shares no consonantal skeleton with expected
    if not set(submitted_plain).intersection(set(expected_plain)):
        result.status = "wrong_root"
        result.diagnosis_type = "root"
        result.affected_feature = "root"
        result.score = 0.0
        return result

    result.status = "spelling/vocalization mismatch"
    result.diagnosis_type = "spelling"
    result.score = 0.0
    return result
