#!/usr/bin/env python3
"""Minimal Aaron voice validation for Hebrew לכתוב.

Synthesizes four unpointed Hebrew sentences with SpeechGen voice Aaron
(locale he-IL), builds a Giuseppe-identified comparison track, and writes
the results to output/mantra_phase1_aaron_validation/.  No Hila cache is
used.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from mantra.phase1.assembly import _decode_wav_to_int16, _encode_int16_to_wav, _resample_mono_int16
from mantra.phase1.timeline import TimelineSegment
from mantra.phase1.tts import SpeechGenTTSProvider, TTSRuntimeError, sha256_hex

OUTPUT_DIR = Path("output/mantra_phase1_aaron_validation")
TARGET_SR = 22050
HEBREW_VOICE = "Aaron"
HEBREW_LOCALE = "he-IL"
ITALIAN_VOICE = "Giuseppe"
ITALIAN_LOCALE = "it-IT"

ITEMS = [
    ("lichtov", "לכתוב", "infinito isolato"),
    ("infinitive_sentence", "אני רוצה לכתוב מכתב", "frase infinito"),
    ("feminine_future_sentence", "את תכתבי מכתב", "futuro femminile"),
    ("first_plural_future_sentence", "אנחנו נכתוב מכתב", "futuro plurale prima persona"),
]


def _silence(seconds: float) -> np.ndarray:
    return np.zeros(int(TARGET_SR * seconds), dtype=np.int16)


def _synthesize(
    provider: SpeechGenTTSProvider, text: str, seg_id: str
) -> tuple[bytes, int, float] | None:
    segment = SimpleNamespace(
        segment_id=seg_id,
        source_text=text,
        tts_text=text,
        voice=provider.voice,
        locale=provider.locale,
    )
    try:
        result = provider.synthesize(cast(TimelineSegment, segment))
    except TTSRuntimeError as exc:
        print(f"Synthesis failed for {seg_id}: {exc}")
        return None
    samples, source_sr = _decode_wav_to_int16(result.audio_bytes)
    if source_sr != TARGET_SR:
        samples = _resample_mono_int16(samples, source_sr, TARGET_SR)
    out_bytes = _encode_int16_to_wav(samples, TARGET_SR)
    duration = len(samples) / TARGET_SR
    return out_bytes, source_sr, duration


def build_validation() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    he_provider = SpeechGenTTSProvider(
        voice=HEBREW_VOICE,
        rate=1.0,
        pitch=0.0,
        fmt="wav",
        locale=HEBREW_LOCALE,
    )
    it_provider = SpeechGenTTSProvider(
        voice=ITALIAN_VOICE,
        rate=1.0,
        pitch=0.0,
        fmt="wav",
        locale=ITALIAN_LOCALE,
    )

    manifest: list[dict[str, Any]] = []
    comparison_parts: list[np.ndarray] = []

    for name, text, it_label in ITEMS:
        out_path = OUTPUT_DIR / f"{name}.wav"
        result = _synthesize(he_provider, text, f"aaron_{name}")
        if result is None:
            raise SystemExit(f"Failed to synthesize {name}")
        out_bytes, source_sr, duration = result
        out_path.write_bytes(out_bytes)

        manifest.append(
            {
                "name": name,
                "file": str(out_path),
                "text": text,
                "code_points": [f"U+{ord(c):04X}" for c in text],
                "provider": "speechgen",
                "voice": HEBREW_VOICE,
                "locale": HEBREW_LOCALE,
                "source_sample_rate": source_sr,
                "output_sample_rate": TARGET_SR,
                "duration": duration,
                "checksum": sha256_hex(out_bytes),
            }
        )

        # Add Giuseppe identifier and the Hebrew audio to the comparison track.
        intro = _synthesize(it_provider, f"Aaron, {it_label}", f"giuseppe_{name}")
        if intro is None:
            raise SystemExit(f"Failed to synthesize Italian intro for {name}")
        comparison_parts.append(_decode_wav_to_int16(intro[0])[0])
        comparison_parts.append(_decode_wav_to_int16(out_bytes)[0])
        comparison_parts.append(_silence(2.0))

    combined = np.concatenate(comparison_parts)
    comparison_bytes = _encode_int16_to_wav(combined, TARGET_SR)
    comparison_path = OUTPUT_DIR / "comparison.wav"
    comparison_path.write_bytes(comparison_bytes)

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Generated Aaron validation in {OUTPUT_DIR}")
    print(f"comparison.wav: {len(combined)/TARGET_SR:.1f}s")


if __name__ == "__main__":
    build_validation()
