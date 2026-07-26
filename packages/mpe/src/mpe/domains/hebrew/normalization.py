"""Deterministic Hebrew response normalization for immediate recall.

Normalization is intentionally conservative: only whitespace, Unicode form,
and a small set of Hebrew punctuation marks are regularised.  No fuzzy
matching or semantic grading is performed.
"""

from __future__ import annotations

import re
import unicodedata


# Hebrew punctuation marks that do not change lexical identity for recall.
_HEBREW_PUNCTUATION = frozenset({
    "\u05be",  # maqqaf (Hebrew hyphen)
    "\u05f3",  # geresh
    "\u05f4",  # gershayim
    "\u00b4",  # acute accent sometimes used as geresh
    "\u0027",  # ASCII apostrophe
    "\u0022",  # ASCII double quote
})


def normalize_hebrew_response(raw_response: str | None) -> str:
    """Return a normalised form of a typed Hebrew (or mixed) response.

    Rules applied, in order:

    1. ``None`` becomes the empty string.
    2. Strip leading and trailing whitespace.
    3. Collapse repeated internal whitespace to a single space.
    4. Apply Unicode NFC normalisation.
    5. Remove a bounded set of Hebrew punctuation marks.
    """
    if raw_response is None:
        return ""
    text = str(raw_response)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if ch not in _HEBREW_PUNCTUATION)
    return text


def is_empty_response(raw_response: str | None) -> bool:
    """Return True if the raw response is None or only whitespace."""
    if raw_response is None:
        return True
    return str(raw_response).strip() == ""
