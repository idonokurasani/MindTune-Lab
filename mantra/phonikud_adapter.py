"""Phonikud adapter: vocalized Hebrew → IPA phonemes."""

from __future__ import annotations

from dataclasses import dataclass

import phonikud

from .utils import stress_from_phonemes


@dataclass
class PhonikudResult:
    phonemes: str
    stress: int


def phonemize(
    vocalized: str, predict_stress: bool = True, predict_vocal_shva: bool = True
) -> PhonikudResult:
    """Phonemize vocalized Hebrew using the phonikud library.

    Returns IPA-style phonemes and the stress syllable index derived from the
    stress marker inserted by phonikud.
    """
    phonemes = phonikud.phonemize(
        vocalized,
        preserve_punctuation=True,
        preserve_stress=True,
        use_expander=True,
        use_post_normalize=True,
        predict_stress=predict_stress,
        predict_vocal_shva=predict_vocal_shva,
        schema="modern",
    )
    return PhonikudResult(phonemes=phonemes, stress=stress_from_phonemes(phonemes))
