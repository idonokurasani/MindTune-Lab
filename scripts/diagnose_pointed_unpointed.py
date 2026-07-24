#!/usr/bin/env python3
"""Compact pointed-vs-unpointed diagnostic for all unique Hebrew forms.

For every Hebrew form in fixture 001_lichtov, synthesizes two variants with
SpeechGen Hila:
  A. canonical pointed display_text
  B. unpointed tts_text

Produces per-form WAVs, a paired comparison WAV, a manifest, and an HTML
review page.  No Italian segments are generated and the accepted mantra
output is not touched.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np

from mantra.phase1.assembly import _decode_wav_to_int16, _encode_int16_to_wav, _resample_mono_int16
from mantra.phase1.fixtures import load_fixture_001_lichtov
from mantra.phase1.pronunciation import PronunciationLexicon
from mantra.phase1.sheva import DIACRITICS
from mantra.phase1.timeline import TimelineSegment
from mantra.phase1.tts import SpeechGenTTSProvider, sha256_hex
from mantra.phase1.utils import normalize_unicode

OUTPUT_DIR = Path("output/mantra_phase1_pointed_vs_unpointed")
TARGET_SR = 22050
PAIR_PAUSE_S = 1.0
FORM_PAUSE_S = 2.0


def _strip_diacritics(text: str) -> str:
    return "".join(c for c in normalize_unicode(text) if c not in DIACRITICS)


def _synthesize(provider: SpeechGenTTSProvider, text: str, seg_id: str) -> tuple[bytes, int, float]:
    segment = SimpleNamespace(
        segment_id=seg_id,
        source_text=text,
        tts_text=text,
        voice=provider.voice,
        locale=provider.locale,
    )
    result = provider.synthesize(cast(TimelineSegment, segment))
    samples, source_sr = _decode_wav_to_int16(result.audio_bytes)
    if source_sr != TARGET_SR:
        samples = _resample_mono_int16(samples, source_sr, TARGET_SR)
    out_bytes = _encode_int16_to_wav(samples, TARGET_SR)
    duration = len(samples) / TARGET_SR
    return out_bytes, source_sr, duration


def build_diagnostic() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    spec = load_fixture_001_lichtov()
    lexicon = None
    if spec.pronunciation_lexicon_path:
        lexicon = PronunciationLexicon(Path(spec.pronunciation_lexicon_path))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pointed_dir = OUTPUT_DIR / "pointed"
    unpointed_dir = OUTPUT_DIR / "unpointed"
    pointed_dir.mkdir(exist_ok=True)
    unpointed_dir.mkdir(exist_ok=True)

    provider = SpeechGenTTSProvider(
        voice="Hila",
        rate=spec.speech.rate,
        pitch=spec.speech.pitch,
        fmt=spec.speech.format,
        locale=spec.speech.locale,
    )

    manifest: list[dict[str, object]] = []
    comparison_parts: list[np.ndarray] = []

    for group in spec.groups:
        for form in group.forms:
            display_text = form.hebrew_with_niqqud
            # Use the approved lexicon tts_text when available; otherwise strip diacritics.
            conjugated = f"{group.tense}/{form.form_key}"
            approved_tts_text = ""
            if lexicon:
                entry = lexicon.get(
                    lexical_item=spec.verb_id,
                    conjugated_form=conjugated,
                    provider="speechgen",
                    voice="Hila",
                    provider_model="",
                )
                if entry and entry.human_review_status == "approved":
                    approved_tts_text = entry.tts_text
            unpointed_text = approved_tts_text or _strip_diacritics(display_text)

            safe = "".join(c for c in form.form_key if c.isalnum() or c in "-_").strip()
            pointed_name = f"{group.tense}_{safe}_pointed.wav"
            unpointed_name = f"{group.tense}_{safe}_unpointed.wav"
            pointed_path = pointed_dir / pointed_name
            unpointed_path = unpointed_dir / unpointed_name

            pointed_bytes, pointed_src_sr, pointed_dur = _synthesize(
                provider, display_text, f"pvu_pointed_{group.tense}_{safe}"
            )
            unpointed_bytes, unpointed_src_sr, unpointed_dur = _synthesize(
                provider, unpointed_text, f"pvu_unpointed_{group.tense}_{safe}"
            )

            pointed_path.write_bytes(pointed_bytes)
            unpointed_path.write_bytes(unpointed_bytes)

            manifest.append(
                {
                    "tense": group.tense,
                    "form_key": form.form_key,
                    "display_text": display_text,
                    "tts_text": unpointed_text,
                    "review_status": "approved" if approved_tts_text else "pending",
                    "pointed_file": str(pointed_path),
                    "unpointed_file": str(unpointed_path),
                    "pointed_source_sample_rate": pointed_src_sr,
                    "unpointed_source_sample_rate": unpointed_src_sr,
                    "output_sample_rate": TARGET_SR,
                    "pointed_duration": pointed_dur,
                    "unpointed_duration": unpointed_dur,
                    "pointed_checksum": sha256_hex(pointed_bytes),
                    "unpointed_checksum": sha256_hex(unpointed_bytes),
                }
            )

            # Build comparison track: pointed, pause, unpointed, pause.
            p_samples, _ = _decode_wav_to_int16(pointed_bytes)
            u_samples, _ = _decode_wav_to_int16(unpointed_bytes)
            comparison_parts.append(p_samples)
            comparison_parts.append(np.zeros(int(TARGET_SR * PAIR_PAUSE_S), dtype=np.int16))
            comparison_parts.append(u_samples)
            comparison_parts.append(np.zeros(int(TARGET_SR * FORM_PAUSE_S), dtype=np.int16))

    # Drop the trailing form pause for a cleaner ending.
    comparison_parts = comparison_parts[:-1]
    combined = np.concatenate(comparison_parts)
    comparison_bytes = _encode_int16_to_wav(combined, TARGET_SR)
    comparison_path = OUTPUT_DIR / "comparison.wav"
    comparison_path.write_bytes(comparison_bytes)

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_html_index(OUTPUT_DIR, manifest)
    print(f"Generated {len(manifest)} form pairs in {OUTPUT_DIR}")
    print(f"Comparison: {comparison_path}")


def _write_html_index(output_dir: Path, manifest: list[dict[str, object]]) -> None:
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Pointed vs Unpointed Diagnostic — 001_lichtov</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;}",
        ".card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0;}",
        "audio{width:100%;margin:.5rem 0;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;}",
        "</style></head><body>",
        "<h1>Pointed vs Unpointed Diagnostic — 001_lichtov</h1>",
        "<p>For each form, compare the canonical pointed display text (A) with the provider-specific unpointed tts text (B).</p>",
        "<p><audio controls src='comparison.wav'></audio> (comparison WAV, all forms)</p>",
    ]
    for item in manifest:
        lines.append("<div class='card'>")
        lines.append(f"<h2>{item['tense']} — {item['form_key']} ({item['review_status']})</h2>")
        lines.append(f"<p class='rtl'><strong>Display:</strong> {item['display_text']}</p>")
        lines.append(f"<p class='rtl'><strong>TTS:</strong> {item['tts_text']}</p>")
        lines.append(f"<p>A: pointed ({item['pointed_duration']:.3f}s)</p><audio controls src='{item['pointed_file']}'></audio>")
        lines.append(f"<p>B: unpointed ({item['unpointed_duration']:.3f}s)</p><audio controls src='{item['unpointed_file']}'></audio>")
        lines.append("</div>")
    lines.append("</body></html>")
    (output_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    build_diagnostic()
