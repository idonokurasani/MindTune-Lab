"""Piper / Phonikud-TTS voice adapter.

This module is the only place that depends on the Piper ONNX voice. Replacing
it with another voice engine requires only re-implementing this adapter.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List, Tuple

import numpy as np
import soundfile as sf
from piper_onnx import Piper

from .utils import wav_to_mp3


class PiperVoice:
    """Wrapper around a Piper ONNX voice model."""

    def __init__(self, model_path: Path, config_path: Path):
        self.model_path = model_path
        self.config_path = config_path
        self._piper: Piper | None = None

    def _get_piper(self) -> Piper:
        if self._piper is None:
            self._piper = Piper(str(self.model_path), str(self.config_path))
        return self._piper

    def synthesize(self, phonemes: str, is_phonemes: bool = True) -> Tuple[np.ndarray, int]:
        """Synthesize audio from a phoneme string.

        Returns (samples, sample_rate). Samples are float32 mono.
        """
        return self._get_piper().create(phonemes, is_phonemes=is_phonemes)

    def synthesize_to_file(self, phonemes: str, wav_path: Path, is_phonemes: bool = True) -> int:
        """Synthesize to a WAV file. Returns the sample rate."""
        samples, sr = self.synthesize(phonemes, is_phonemes=is_phonemes)
        sf.write(wav_path, samples, sr)
        return sr


def silence_samples(seconds: float, sample_rate: int, dtype: np.dtype) -> np.ndarray:
    """Generate a mono silence segment of a given duration."""
    length = int(round(seconds * sample_rate))
    return np.zeros(length, dtype=dtype)


def concatenate_segments(
    segments: List[Tuple[np.ndarray, int]],
    break_seconds: float = 0.5,
    section_break_seconds: float = 0.9,
    section_end_indices: List[int] | None = None,
) -> Tuple[np.ndarray, int]:
    """Concatenate audio segments with pauses.

    ``section_end_indices`` is a list of 0-based indices after which a longer
    section break should be inserted instead of the normal form break.
    """
    if not segments:
        raise ValueError("No audio segments provided")

    sample_rate = segments[0][1]
    dtype = segments[0][0].dtype

    parts: List[np.ndarray] = []
    for idx, (samples, sr) in enumerate(segments):
        if sr != sample_rate:
            raise ValueError(f"Sample rate mismatch: {sr} != {sample_rate}")
        if samples.dtype != dtype:
            samples = samples.astype(dtype)
        parts.append(samples)

        if idx == len(segments) - 1:
            break

        pause = (
            section_break_seconds
            if section_end_indices and idx in section_end_indices
            else break_seconds
        )
        parts.append(silence_samples(pause, sample_rate, dtype))

    return np.concatenate(parts), sample_rate


def render_mantra_mp3(
    voice: PiperVoice,
    phoneme_segments: List[str],
    mp3_path: Path,
    break_seconds: float = 0.5,
    section_break_seconds: float = 0.9,
    section_end_indices: List[int] | None = None,
) -> Path:
    """Generate the full mantra MP3 from a list of phoneme strings."""
    if not phoneme_segments:
        raise ValueError("No phoneme segments provided")

    segments: List[Tuple[np.ndarray, int]] = []
    for text in phoneme_segments:
        samples, sr = voice.synthesize(text, is_phonemes=True)
        segments.append((samples, sr))

    combined, sr = concatenate_segments(
        segments,
        break_seconds=break_seconds,
        section_break_seconds=section_break_seconds,
        section_end_indices=section_end_indices,
    )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    sf.write(tmp_path, combined, sr)
    wav_to_mp3(tmp_path, mp3_path)
    tmp_path.unlink(missing_ok=True)
    return mp3_path
