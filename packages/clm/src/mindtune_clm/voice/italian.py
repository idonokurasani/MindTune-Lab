"""Italian text normalization for Giuseppe."""

from __future__ import annotations

import unicodedata


def normalize_source(text: str) -> str:
    """Normalize Italian source text deterministically.

    Preserves accents, apostrophes, punctuation, abbreviations, numbers,
    grammatical labels, and prosodic punctuation.
    """
    return unicodedata.normalize("NFC", text)


def validate_italian_text(text: str) -> None:
    """Validate Italian text for Giuseppe."""
    if not text:
        raise ItalianTextError("Italian text is empty")
    if has_hebrew_codepoints(text):
        raise ItalianTextError("Italian text contains Hebrew code points; Hebrew must not route to Giuseppe")


def has_hebrew_codepoints(text: str) -> bool:
    """Return True if text contains Hebrew Unicode block code points."""
    return any("\u0590" <= c <= "\u05FF" for c in text)


class ItalianTextError(Exception):
    """Raised when Italian text violates Giuseppe routing rules."""
