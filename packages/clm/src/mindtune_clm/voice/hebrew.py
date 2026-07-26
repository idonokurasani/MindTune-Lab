"""Hebrew text validation for pointed source and pointed Aaron synthesis."""

from __future__ import annotations

import re
import unicodedata

HEBREW_BLOCK = re.compile(r"[\u0590-\u05FF]")

# Hebrew combining diacritics (points, dagesh, shin/sin dots)
HEBREW_COMBINING_MARKS = re.compile(
    r"[\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]"
)

# Shin dot U+05C1, sin dot U+05C2, dagesh U+05BC
DAGESH = "\u05BC"
SHIN_DOT = "\u05C1"
SIN_DOT = "\u05C2"
MAQAF = "\u05BE"

# Pronunciation-related punctuation/combining marks that must be preserved
PRESERVED_MARKS = {
    "\u05B0",  # sheva
    "\u05B1",  # hataf segol
    "\u05B2",  # hataf patah
    "\u05B3",  # hataf qamats
    "\u05B4",  # hiriq
    "\u05B5",  # tsere
    "\u05B6",  # segol
    "\u05B7",  # patah
    "\u05B8",  # qamats
    "\u05B9",  # holam
    "\u05BA",  # holam haser for vav
    "\u05BB",  # qubuts
    "\u05BC",  # dagesh / mapiq
    "\u05BD",  # meteg
    "\u05BF",  # rafe
    "\u05C1",  # shin dot
    "\u05C2",  # sin dot
    "\u05C4",  # upper dot
    "\u05C5",  # lower dot
    "\u05C7",  # qamats qatan
    "\u05BE",  # maqaf
    "\u05F3",  # geresh
    "\u05F4",  # gershayim
}


def has_hebrew(text: str) -> bool:
    """Return True if the text contains any Hebrew code points."""
    return HEBREW_BLOCK.search(text) is not None


def has_niqqud(text: str) -> bool:
    """Return True if text contains Hebrew combining diacritics."""
    return HEBREW_COMBINING_MARKS.search(text) is not None


def count_niqqud(text: str) -> int:
    """Count Hebrew combining diacritics in text."""
    return len(HEBREW_COMBINING_MARKS.findall(text))


def normalize_source(text: str) -> str:
    """Normalize source text deterministically without removing Hebrew marks.

    Uses NFC to combine decomposed base+mark sequences into precomposed forms
    where possible, but preserves every combining mark that remains.
    """
    return unicodedata.normalize("NFC", text)


def _extract_hebrew_mark_order(text: str) -> list[str]:
    """Return list of Hebrew base letters and combining marks in code-point order."""
    return [c for c in text if HEBREW_BLOCK.match(c) or HEBREW_COMBINING_MARKS.match(c)]


def validate_source_text(text: str) -> None:
    """Validate pointed Hebrew source_text preserves niqqud and combining order."""
    if not text:
        raise HebrewTextError("source_text is empty")
    if not has_hebrew(text):
        raise HebrewTextError("source_text contains no Hebrew characters")
    if not has_niqqud(text):
        raise HebrewTextError("source_text is missing Hebrew niqqud")

    normalized = normalize_source(text)
    if _extract_hebrew_mark_order(normalized) != _extract_hebrew_mark_order(text):
        raise HebrewTextError("source_text combining-mark order changed during normalization")


def validate_tts_text(tts_text: str, source_text: str, *, unpointed_exception_approved: bool = False) -> None:
    """Validate Aaron tts_text."""
    if not tts_text:
        raise HebrewTextError("tts_text is empty")
    if not has_hebrew(tts_text):
        raise HebrewTextError("tts_text contains no Hebrew characters")
    if not has_niqqud(tts_text) and not unpointed_exception_approved:
        raise HebrewTextError(
            "Aaron tts_text lacks niqqud; set unpointed_exception_approved=True only for validated overrides"
        )

    normalized = normalize_source(tts_text)
    if _extract_hebrew_mark_order(normalized) != _extract_hebrew_mark_order(tts_text):
        raise HebrewTextError("tts_text combining-mark order changed during normalization")


def validate_word_separation(source_text: str) -> None:
    """Ensure multi-word Hebrew phrases use whitespace or maqaf separators."""
    if not source_text:
        return
    stripped = source_text.strip()
    # Extract sequences of Hebrew letters/punctuation (geresh/gershayim).
    hebrew_tokens = re.split(r"[^\u0590-\u05FF\u05F3\u05F4]+", stripped)
    non_empty = [t for t in hebrew_tokens if t]
    if len(non_empty) >= 2 and stripped.count(" ") == 0 and stripped.count(MAQAF) == 0:
        raise HebrewTextError("Hebrew words are not separated by whitespace or maqaf")


class HebrewTextError(Exception):
    """Raised when Hebrew text violates the pointed-source/tts contract."""
