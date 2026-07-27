"""Deterministic Hebrew response scoring without LLMs or live lookups."""

from __future__ import annotations

import re
import unicodedata

from mindtune_clm.hebrew_slice.error_taxonomy import HebrewErrorCode
from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem, HebrewResponse, HebrewScore
from mpe.domains.hebrew.normalization import (
    is_empty_response,
    normalize_hebrew_response,
)

_HAYA_FAMILY = {"להיות", "להוות", "להתהוות"}


def _is_transliteration_only(text: str) -> bool:
    """True when the text is plain ASCII / Latin (no Hebrew letters)."""
    return bool(re.fullmatch(r"[A-Za-z0-9\s\-\_'\"\.\,;:\!\?]+", text))


def _has_invalid_unicode(text: str) -> bool:
    """True when text contains isolated surrogate or undefined code points."""
    try:
        encoded = text.encode("utf-8", "surrogatepass")
        encoded.decode("utf-8", "strict")
        return text != unicodedata.normalize("NFC", text)
    except (UnicodeDecodeError, UnicodeEncodeError):
        return True


def _strip_niqqud(text: str) -> str:
    """Remove Hebrew points, dagesh and shin/sin dots (not letters)."""
    return re.sub(r"[\u0591-\u05bd\u05bf-\u05c7]", "", text)


def _is_likely_empty(text: str | None) -> bool:
    return bool(is_empty_response(text))


def _root_matches(a: str, b: str) -> bool:
    return a.strip().lower().replace("-", "") == b.strip().lower().replace("-", "")


def score_response(  # noqa: C901
    item: HebrewAdaptiveItem,
    response: HebrewResponse,
    *,
    latency_bound_ms: float = 12000.0,
) -> HebrewScore:
    """Return a deterministic HebrewScore for a submitted response."""
    raw = response.raw_response
    if _is_likely_empty(raw):
        return HebrewScore(
            overall="not_answered",
            lemma="invalid",
            root="invalid",
            binyan="invalid",
            tense_mood="invalid",
            person="invalid",
            gender="invalid",
            number="invalid",
            pointed_orthography="invalid",
            unpointed_orthography="invalid",
            meaning="invalid",
            contextual_agreement="invalid",
            accepted_alternate_used=False,
            error_codes=[HebrewErrorCode.OMITTED_RESPONSE.value],
        )

    normalized = response.normalized_response
    if _has_invalid_unicode(raw) or _is_transliteration_only(normalized):
        codes = [HebrewErrorCode.TRANSLITERATION_INSTEAD_OF_HEBREW.value]
        if _has_invalid_unicode(raw):
            codes.append(HebrewErrorCode.INVALID_UNICODE.value)
        return HebrewScore(
            overall="invalid",
            lemma="invalid",
            root="invalid",
            binyan="invalid",
            tense_mood="invalid",
            person="invalid",
            gender="invalid",
            number="invalid",
            pointed_orthography="invalid",
            unpointed_orthography="invalid",
            meaning="invalid",
            contextual_agreement="invalid",
            accepted_alternate_used=False,
            error_codes=codes,
        )

    expected_pointed = normalize_hebrew_response(item.canonical_pointed)
    expected_unpointed = normalize_hebrew_response(item.canonical_unpointed)
    resp_pointed = normalized
    resp_unpointed = normalize_hebrew_response(_strip_niqqud(resp_pointed))

    accepted_pointed = {normalize_hebrew_response(a) for a in item.accepted_alternates}
    accepted_unpointed = {normalize_hebrew_response(_strip_niqqud(a)) for a in item.accepted_alternates}

    is_pointed_exact = resp_pointed == expected_pointed
    is_unpointed_exact = resp_unpointed == expected_unpointed
    is_accepted_pointed = resp_pointed in accepted_pointed
    is_accepted_unpointed = resp_unpointed in accepted_unpointed

    # Meaning/context dimensions are not evaluated from typing alone in this slice.
    meaning_status = "correct" if is_pointed_exact or is_unpointed_exact or is_accepted_pointed or is_accepted_unpointed else "incorrect"
    context_status = meaning_status

    if is_pointed_exact:
        return HebrewScore(
            overall="correct",
            lemma="correct",
            root="correct",
            binyan="correct",
            tense_mood="correct",
            person="correct",
            gender="correct",
            number="correct",
            pointed_orthography="correct",
            unpointed_orthography="correct",
            meaning=meaning_status,
            contextual_agreement=context_status,
            accepted_alternate_used=False,
            error_codes=[],
        )

    if is_unpointed_exact:
        return HebrewScore(
            overall="correct_unpointed",
            lemma="correct",
            root="correct",
            binyan="correct",
            tense_mood="correct",
            person="correct",
            gender="correct",
            number="correct",
            pointed_orthography="incorrect",
            unpointed_orthography="correct",
            meaning=meaning_status,
            contextual_agreement=context_status,
            accepted_alternate_used=False,
            error_codes=[
                HebrewErrorCode.POINTED_UNPOINTED_MISMATCH.value,
                HebrewErrorCode.WRONG_NIQQUD.value,
            ],
        )

    if is_accepted_pointed or is_accepted_unpointed:
        return HebrewScore(
            overall="accepted_alternate",
            lemma="correct",
            root="correct",
            binyan="correct",
            tense_mood="correct",
            person="correct_unpointed" if is_accepted_unpointed else "correct",
            gender="correct",
            number="correct",
            pointed_orthography="correct" if is_accepted_pointed else "correct_unpointed",
            unpointed_orthography="correct",
            meaning=meaning_status,
            contextual_agreement=context_status,
            accepted_alternate_used=True,
            error_codes=[HebrewErrorCode.ACCEPTED_ALTERNATE.value],
        )

    # Incorrect branch: collect error codes.
    error_codes: list[str] = []
    if resp_unpointed in _HAYA_FAMILY and item.lemma_unpointed != resp_unpointed:
        error_codes.append(HebrewErrorCode.HAYA_HAVA_HIT_HAVA_CONFUSION.value)
    if resp_unpointed in {normalize_hebrew_response(e) for e in item.error_confusion_set}:
        error_codes.append(HebrewErrorCode.SEMANTICALLY_RELATED_VERB_CONFUSION.value)
    if resp_unpointed != expected_unpointed:
        error_codes.append(HebrewErrorCode.WRONG_LEMMA.value)
    if not _root_matches(resp_unpointed, item.root) and not _root_matches(resp_unpointed, ""):
        error_codes.append(HebrewErrorCode.WRONG_ROOT.value)
    if resp_unpointed != expected_unpointed:
        error_codes.append(HebrewErrorCode.POINTED_UNPOINTED_MISMATCH.value)
        error_codes.append(HebrewErrorCode.WRONG_NIQQUD.value)
    if _has_invalid_unicode(raw):
        error_codes.append(HebrewErrorCode.INVALID_UNICODE.value)

    error_codes = list(dict.fromkeys(error_codes))

    # Morphological dimensions are conservatively marked incorrect when the form does not match.
    dim = "incorrect"
    return HebrewScore(
        overall="incorrect",
        lemma=dim,
        root=dim,
        binyan=dim,
        tense_mood=dim,
        person=dim,
        gender=dim,
        number=dim,
        pointed_orthography="incorrect",
        unpointed_orthography="incorrect" if resp_unpointed != expected_unpointed else "correct_unpointed",
        meaning=dim,
        contextual_agreement=dim,
        accepted_alternate_used=False,
        error_codes=error_codes,
    )
