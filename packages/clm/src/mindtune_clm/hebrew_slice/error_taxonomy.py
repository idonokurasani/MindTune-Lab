"""Typed error taxonomy for Hebrew adaptive responses."""

from __future__ import annotations

from enum import Enum


class HebrewErrorCode(str, Enum):
    """Canonical error code strings emitted by the Hebrew scorer."""

    WRONG_LEMMA = "wrong_lemma"
    WRONG_ROOT = "wrong_root"
    WRONG_BINYAN = "wrong_binyan"
    WRONG_TENSE = "wrong_tense"
    WRONG_MOOD = "wrong_mood"
    WRONG_PERSON = "wrong_person"
    WRONG_GENDER = "wrong_gender"
    WRONG_NUMBER = "wrong_number"
    PARTICIPLE_PERSON_CONFUSION = "participle_person_confusion"
    POINTED_UNPOINTED_MISMATCH = "pointed_unpointed_mismatch"
    WRONG_NIQQUD = "wrong_niqqud"
    DAGESH_ERROR = "dagesh_error"
    SHIN_SIN_DOT_ERROR = "shin_sin_dot_error"
    SUBJECT_VERB_DISAGREEMENT = "subject_verb_disagreement"
    SINGULAR_PLURAL_PREDICATE_DISAGREEMENT = "singular_plural_predicate_disagreement"
    SEMANTICALLY_RELATED_VERB_CONFUSION = "semantically_related_verb_confusion"
    HAYA_HAVA_HIT_HAVA_CONFUSION = "haya_hava_hit_hava_confusion"
    MODERN_FORMAL_VARIANT_MISMATCH = "modern_formal_variant_mismatch"
    TRANSLITERATION_INSTEAD_OF_HEBREW = "transliteration_instead_of_hebrew"
    OMITTED_RESPONSE = "omitted_response"
    INVALID_UNICODE = "invalid_unicode"
    ACCEPTED_ALTERNATE = "accepted_alternate"
    UNKNOWN_INCORRECT = "unknown_incorrect"


# Aggregate groups reused by the adaptation layer.
MORPHOLOGY_ERROR_CODES = {
    HebrewErrorCode.WRONG_LEMMA,
    HebrewErrorCode.WRONG_ROOT,
    HebrewErrorCode.WRONG_BINYAN,
    HebrewErrorCode.WRONG_TENSE,
    HebrewErrorCode.WRONG_MOOD,
    HebrewErrorCode.WRONG_PERSON,
    HebrewErrorCode.WRONG_GENDER,
    HebrewErrorCode.WRONG_NUMBER,
    HebrewErrorCode.PARTICIPLE_PERSON_CONFUSION,
}

POINTING_ERROR_CODES = {
    HebrewErrorCode.WRONG_NIQQUD,
    HebrewErrorCode.DAGESH_ERROR,
    HebrewErrorCode.SHIN_SIN_DOT_ERROR,
    HebrewErrorCode.POINTED_UNPOINTED_MISMATCH,
}

CONTEXT_ERROR_CODES = {
    HebrewErrorCode.SUBJECT_VERB_DISAGREEMENT,
    HebrewErrorCode.SINGULAR_PLURAL_PREDICATE_DISAGREEMENT,
    HebrewErrorCode.SEMANTICALLY_RELATED_VERB_CONFUSION,
    HebrewErrorCode.HAYA_HAVA_HIT_HAVA_CONFUSION,
    HebrewErrorCode.MODERN_FORMAL_VARIANT_MISMATCH,
}


def is_morphology_error(code: str) -> bool:
    return code in {c.value for c in MORPHOLOGY_ERROR_CODES}


def is_pointing_error(code: str) -> bool:
    return code in {c.value for c in POINTING_ERROR_CODES}


def is_context_error(code: str) -> bool:
    return code in {c.value for c in CONTEXT_ERROR_CODES}
