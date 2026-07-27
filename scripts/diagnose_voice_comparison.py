#!/usr/bin/env python3
"""Targeted voice comparison for the Hebrew infinitive לכתוב.

Queries the SpeechGen voice catalogue, filters to the Hebrew language group,
synthesizes two unpointed Hebrew texts with every listed he-IL voice, and
builds a comparison track with Italian identifiers.  No engine files are
modified; output is written to
output/mantra_phase1_lichtov_voice_comparison/.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from mantra.phase1.assembly import _decode_wav_to_int16, _encode_int16_to_wav, _resample_mono_int16
from mantra.phase1.timeline import TimelineSegment
from mantra.phase1.tts import SpeechGenTTSProvider, TTSRuntimeError, sha256_hex

OUTPUT_DIR = Path("output/mantra_phase1_lichtov_voice_comparison")
TARGET_SR = 22050
ISOLATED_TEXT = "לכתוב"
SENTENCE_TEXT = "אני רוצה לכתוב מכתב"
CATALOGUE_URL = "https://speechgen.io/index.php?r=api/voices"


def _safe_filename(name: str) -> str:
    """Return a filesystem-safe version of a voice name."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_")[:60]


def _fetch_voices(api_key: str, email: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"token": api_key, "email": email})
    url = f"{CATALOGUE_URL}&{params}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:500]
        raise TTSRuntimeError(f"SpeechGen voice catalogue HTTP {exc.code}: {body}") from exc
    except Exception as exc:
        raise TTSRuntimeError(f"Failed to fetch voice catalogue: {exc}") from exc

    # The catalogue is keyed by human-readable language name.  Pick the Hebrew group.
    for lang, voices in data.items():
        if lang.lower() == "hebrew" and isinstance(voices, list):
            return voices
    raise TTSRuntimeError(
        f"No Hebrew voice group found in catalogue; languages: {list(data.keys())}"
    )


def _synthesize(
    provider: SpeechGenTTSProvider, text: str, voice: str, locale: str, seg_id: str
) -> tuple[bytes, int, float] | None:
    """Synthesize one text and normalize to 22050 Hz mono WAV."""
    segment = SimpleNamespace(
        segment_id=seg_id,
        source_text=text,
        tts_text=text,
        voice=voice,
        locale=locale,
    )
    try:
        result = provider.synthesize(cast(TimelineSegment, segment))
    except TTSRuntimeError as exc:
        print(f"Synthesis failed for {voice}/{locale}: {exc}")
        return None
    samples, source_sr = _decode_wav_to_int16(result.audio_bytes)
    if source_sr != TARGET_SR:
        samples = _resample_mono_int16(samples, source_sr, TARGET_SR)
    out_bytes = _encode_int16_to_wav(samples, TARGET_SR)
    duration = len(samples) / TARGET_SR
    return out_bytes, source_sr, duration


def _silence(seconds: float) -> np.ndarray:
    return np.zeros(int(TARGET_SR * seconds), dtype=np.int16)


def build_diagnostic() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_dir = OUTPUT_DIR / "audio"
    audio_dir.mkdir(exist_ok=True)

    voices = _fetch_voices(api_key, email)
    (OUTPUT_DIR / "voices.json").write_text(
        json.dumps(voices, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    he_provider = SpeechGenTTSProvider(
        voice="Hila",
        rate=1.0,
        pitch=0.0,
        fmt="wav",
        locale="he-IL",
    )
    it_provider = SpeechGenTTSProvider(
        voice="Giuseppe",
        rate=1.0,
        pitch=0.0,
        fmt="wav",
        locale="it-IT",
    )

    manifest: list[dict[str, Any]] = []
    comparison_parts: list[np.ndarray] = []

    for voice_info in voices:
        voice = voice_info.get("voice", "")
        if not voice:
            continue
        safe = _safe_filename(voice)
        gender = voice_info.get("sex", "")
        tier = voice_info.get("type", "")
        pro = voice_info.get("pro", "")
        cpm = voice_info.get("cpm", "")

        isolated_file = audio_dir / f"{safe}_isolated.wav"
        sentence_file = audio_dir / f"{safe}_sentence.wav"

        isolated = _synthesize(he_provider, ISOLATED_TEXT, voice, "he-IL", f"vc_iso_{safe}")
        sentence = _synthesize(he_provider, SENTENCE_TEXT, voice, "he-IL", f"vc_sent_{safe}")

        if isolated is None or sentence is None:
            manifest.append(
                {
                    "voice": voice,
                    "gender": gender,
                    "tier": tier,
                    "pro": pro,
                    "cpm": cpm,
                    "status": "failed",
                    "isolated_file": "",
                    "sentence_file": "",
                    "error": "synthesis failed",
                }
            )
            continue

        isolated_file.write_bytes(isolated[0])
        sentence_file.write_bytes(sentence[0])

        iso_entry = {
            "label": "isolated",
            "text": ISOLATED_TEXT,
            "code_points": [f"U+{ord(c):04X}" for c in ISOLATED_TEXT],
            "locale": "he-IL",
            "source_sample_rate": isolated[1],
            "output_sample_rate": TARGET_SR,
            "duration": isolated[2],
            "checksum": sha256_hex(isolated[0]),
            "file": str(isolated_file),
        }
        sent_entry = {
            "label": "sentence",
            "text": SENTENCE_TEXT,
            "code_points": [f"U+{ord(c):04X}" for c in SENTENCE_TEXT],
            "locale": "he-IL",
            "source_sample_rate": sentence[1],
            "output_sample_rate": TARGET_SR,
            "duration": sentence[2],
            "checksum": sha256_hex(sentence[0]),
            "file": str(sentence_file),
        }
        manifest.append(
            {
                "voice": voice,
                "gender": gender,
                "tier": tier,
                "pro": pro,
                "cpm": cpm,
                "status": "ok",
                "isolated": iso_entry,
                "sentence": sent_entry,
            }
        )

        # Build Italian announcement phrases for this voice.
        intro_inf = _synthesize(
            it_provider, f"Voce {voice}, infinito", "Giuseppe", "it-IT", f"it_inf_{safe}"
        )
        intro_sent = _synthesize(
            it_provider, f"Voce {voice}, frase", "Giuseppe", "it-IT", f"it_sent_{safe}"
        )

        if intro_inf is None or intro_sent is None:
            print(f"Italian intro failed for {voice}; skipping comparison segment")
            continue

        # Comparison: intro infinito, isolated, 1s, intro frase, sentence, 2s.
        comparison_parts.append(_decode_wav_to_int16(intro_inf[0])[0])
        comparison_parts.append(_decode_wav_to_int16(isolated[0])[0])
        comparison_parts.append(_silence(1.0))
        comparison_parts.append(_decode_wav_to_int16(intro_sent[0])[0])
        comparison_parts.append(_decode_wav_to_int16(sentence[0])[0])
        comparison_parts.append(_silence(2.0))

    if comparison_parts:
        combined = np.concatenate(comparison_parts)
        comparison_bytes = _encode_int16_to_wav(combined, TARGET_SR)
        comparison_path = OUTPUT_DIR / "comparison.wav"
        comparison_path.write_bytes(comparison_bytes)
        print(f"comparison.wav: {len(combined)/TARGET_SR:.1f}s")
    else:
        comparison_path = None

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_html_index(OUTPUT_DIR, voices, manifest)
    print(f"Processed {len(manifest)} voices; output in {OUTPUT_DIR}")


def _write_html_index(
    output_dir: Path, voices: list[dict[str, Any]], manifest: list[dict[str, Any]]
) -> None:
    voice_map = {v.get("voice", ""): v for v in voices}
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Lichtov Voice Comparison — לכתוב</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;}",
        ".card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0;}",
        "audio{width:100%;margin:.5rem 0;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;}",
        "label{margin-right:1rem;}",
        "textarea{width:100%;height:60px;}",
        "</style></head><body>",
        "<h1>Lichtov Voice Comparison — לכתוב</h1>",
        "<p>Expected pronunciation: <strong>likhtov</strong> (IPA approximately /liχˈtov/)</p>",
        "<p><audio controls src='comparison.wav'></audio> (full comparison)</p>",
    ]
    for entry in manifest:
        voice = entry.get("voice", "")
        info = voice_map.get(voice, {})
        safe = _safe_filename(voice)
        lines.append(f"<div class='card' id='{safe}'>")
        lines.append(f"<h2>{voice}</h2>")
        lines.append(
            f"<p>gender: {info.get('sex', '')} | tier: {info.get('type', '')} | "
            f"pro: {info.get('pro', '')} | cpm: {info.get('cpm', '')}</p>"
        )
        if entry.get("status") == "ok":
            lines.append(f"<p class='rtl'>{ISOLATED_TEXT}</p>")
            lines.append(f"<audio controls src='audio/{safe}_isolated.wav'></audio>")
            lines.append(f"<p class='rtl'>{SENTENCE_TEXT}</p>")
            lines.append(f"<audio controls src='audio/{safe}_sentence.wav'></audio>")
            lines.append("<p>Review:</p>")
            lines.append(
                f"<label><input type='radio' name='review_{safe}' value='correct'> correct</label>"
                f"<label><input type='radio' name='review_{safe}' value='acceptable'> acceptable</label>"
                f"<label><input type='radio' name='review_{safe}' value='incorrect'> incorrect</label>"
            )
            lines.append(f"<textarea placeholder='comments for {voice}'></textarea>")
        else:
            lines.append(f"<p>Status: {entry.get('status')} — {entry.get('error', '')}</p>")
        lines.append("</div>")
    lines.append("</body></html>")
    (output_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    build_diagnostic()
