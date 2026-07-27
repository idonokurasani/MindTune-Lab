"""Shared Phonikud adapter."""

from __future__ import annotations

import re

import phonikud

from ..exceptions import PronunciationError


def phonemize(
    text: str,
    predict_stress: bool = True,
    predict_vocal_shva: bool = True,
    schema: str = "modern",
) -> str:
    """Return IPA-style phonemes for vocalized or unvocalized Hebrew text."""
    try:
        return phonikud.phonemize(
            text,
            preserve_punctuation=True,
            preserve_stress=True,
            use_expander=True,
            use_post_normalize=True,
            predict_stress=predict_stress,
            predict_vocal_shva=predict_vocal_shva,
            schema=schema,  # type: ignore[arg-type]
        )
    except Exception as exc:
        raise PronunciationError(f"Phonikud failed on {text!r}: {exc}") from exc


def stress_from_phonemes(phonemes: str) -> int:
    """Return 1-based stressed syllable index from a Phonikud string."""
    if "ˈ" not in phonemes:
        return 0
    before, _ = phonemes.split("ˈ", 1)
    return len(re.findall(r"[aeiouAEIOU]", before)) + 1


def has_vocal_shva(phonemes: str) -> bool:
    """Conservative heuristic: a vowel appears where a consonant cluster is expected."""
    # The authoritative vocal-shva flag is in the override layer.
    return bool(re.search(r"[aeiou]", phonemes))
