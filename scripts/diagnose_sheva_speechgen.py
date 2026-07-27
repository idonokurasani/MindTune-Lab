#!/usr/bin/env python3
"""Generate a sheva diagnostic package for fixture 001_lichtov.

For every Hebrew form that contains U+05B0, this script:
  1. classifies each sheva occurrence;
  2. produces three TTS variants (A canonical, B omit-silent, C unpointed);
  3. reuses the accepted Hila audio for variant A;
  4. synthesizes variants B and C with SpeechGen Hila (he-IL) in a separate
     cache/directory;
  5. writes a comparison manifest, a pronunciation lexicon, a review CSV, and
     a local HTML review page.

No Italian segments are regenerated and the accepted mantra output is not
overwritten.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import wave
from pathlib import Path
from typing import Any

from mantra.phase1.assembly import _decode_wav_to_int16, _encode_int16_to_wav, _resample_mono_int16
from mantra.phase1.fixtures import load_fixture_001_lichtov
from mantra.phase1.pronunciation import PronunciationEntry, PronunciationLexicon
from mantra.phase1.sheva import (
    SHEVA,
    ShevaStatus,
    tts_variant,
)
from mantra.phase1.timeline import SegmentType, TimelineSegment
from mantra.phase1.tts import SpeechGenTTSProvider, TTSResult, sha256_hex

OUTPUT_DIR = Path("output/mantra_phase1_sheva_diagnostics")
ACCEPTED_DIR = Path("output/mantra_phase1_speechgen")
ACCEPTED_MANIFEST = ACCEPTED_DIR / "manifest.json"
TARGET_SAMPLE_RATE = 22050


def _load_accepted_segment_map() -> dict[tuple[int, int], Path]:
    """Map (group_index, form_index) to the accepted Hebrew segment WAV path."""
    mapping: dict[tuple[int, int], Path] = {}
    if not ACCEPTED_MANIFEST.exists():
        return mapping
    manifest = json.loads(ACCEPTED_MANIFEST.read_text(encoding="utf-8"))
    for seg in manifest.get("timeline", []):
        if seg["segment_type"] not in {"hebrew_form", "hebrew_infinitive"}:
            continue
        ref = seg.get("artifact_reference")
        if not ref:
            continue
        wav_path = ACCEPTED_DIR / ref
        if wav_path.exists():
            key = (seg["group_index"], seg["form_index"])
            mapping[key] = wav_path
    return mapping


def _synthesize_variant(
    provider: SpeechGenTTSProvider,
    text: str,
    voice: str,
    locale: str,
    segment_id: str,
) -> TTSResult:
    """Synthesize one provider-specific variant with SpeechGen Hila."""
    segment = TimelineSegment(
        segment_id=segment_id,
        segment_type=SegmentType.HEBREW_FORM,
        source_text=text,
        vocalized_text=text,
        grammatical_metadata={},
        repetition_index=0,
        cycle_index=0,
        group_index=0,
        form_index=0,
        planned_start_time=0.0,
        planned_duration=0.0,
        provider="speechgen",
        language="he",
        locale=locale,
        voice=voice,
    )
    result = provider.synthesize(segment)
    # Resample to the canonical target sample rate for consistent playback.
    samples, sr = _decode_wav_to_int16(result.audio_bytes)
    if sr != TARGET_SAMPLE_RATE:
        samples = _resample_mono_int16(samples, sr, TARGET_SAMPLE_RATE)
    resampled_bytes = _encode_int16_to_wav(samples, TARGET_SAMPLE_RATE)
    return TTSResult(
        audio_bytes=resampled_bytes,
        sample_rate=TARGET_SAMPLE_RATE,
        duration=len(samples) / TARGET_SAMPLE_RATE,
        provider=result.provider,
        voice=result.voice,
        text=result.text,
        format=result.format,
        checksum=sha256_hex(resampled_bytes),
        rate=result.rate,
        pitch=result.pitch,
        locale=result.locale,
    )


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def _safe_filename(text: str, form_key: str) -> str:
    """Return a filesystem-safe name that still identifies the form."""
    # Remove diacritics and punctuation, keep Hebrew letters and ASCII.
    base = "".join(c for c in text if c.isalnum() or c.isspace())
    base = base.strip().replace(" ", "_")[:40]
    return f"{form_key}_{base}" if base else form_key


def build_diagnostic_package() -> None:
    """Run the sheva diagnostic workflow."""
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    spec = load_fixture_001_lichtov()
    accepted_map = _load_accepted_segment_map()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    variants_dir = OUTPUT_DIR / "variants"
    variants_dir.mkdir(exist_ok=True)
    for sub in ("canonical", "omit_silent", "unpointed"):
        (variants_dir / sub).mkdir(exist_ok=True)

    provider = SpeechGenTTSProvider(
        voice="Hila",
        rate=spec.speech.rate,
        pitch=spec.speech.pitch,
        fmt=spec.speech.format,
        locale=spec.speech.locale,
    )

    lexicon = PronunciationLexicon(OUTPUT_DIR / "pronunciation_lexicon.json")
    comparison: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    for group_idx, group in enumerate(spec.groups):
        for form_idx, form in enumerate(group.forms):
            if SHEVA not in form.hebrew_with_niqqud:
                continue

            annotations = form.sheva_annotations
            canonical = form.hebrew_with_niqqud
            omit_silent = tts_variant(canonical, annotations, "omit_silent")
            unpointed = tts_variant(canonical, annotations, "unpointed")

            safe = _safe_filename(canonical, form.form_key)
            canonical_path = variants_dir / "canonical" / f"{safe}.wav"
            omit_path = variants_dir / "omit_silent" / f"{safe}.wav"
            unpointed_path = variants_dir / "unpointed" / f"{safe}.wav"

            # Variant A: reuse the accepted Hila audio when possible.
            accepted_key = (group_idx, form_idx)
            if accepted_key in accepted_map:
                shutil.copy(accepted_map[accepted_key], canonical_path)
            else:
                # Fallback: synthesize canonical again with Hila.
                result_a = _synthesize_variant(
                    provider, canonical, "Hila", "he-IL", f"sheva_canonical_{safe}"
                )
                canonical_path.write_bytes(result_a.audio_bytes)

            # Variant B and C: synthesize with Hila.
            result_b = _synthesize_variant(
                provider, omit_silent, "Hila", "he-IL", f"sheva_omit_silent_{safe}"
            )
            omit_path.write_bytes(result_b.audio_bytes)

            result_c = _synthesize_variant(
                provider, unpointed, "Hila", "he-IL", f"sheva_unpointed_{safe}"
            )
            unpointed_path.write_bytes(result_c.audio_bytes)

            canonical_dur = _wav_duration(canonical_path)
            omit_dur = _wav_duration(omit_path)
            unpointed_dur = _wav_duration(unpointed_path)

            expected_pronunciation = " ".join(
                (
                    a.expected_phoneme or "?"
                    if a.status == ShevaStatus.UNCERTAIN
                    else (a.expected_phoneme or "_")
                )
                for a in annotations
            )

            entry = PronunciationEntry(
                lexical_item=spec.verb_id,
                conjugated_form=f"{group.tense}/{form.form_key}",
                provider="speechgen",
                voice="Hila",
                provider_model="",
                display_text=canonical,
                normalized_text=form.normalized_text,
                tts_text=canonical,
                expected_pronunciation=expected_pronunciation,
                sheva_decisions=[a.to_dict() for a in annotations],
                selected_audio_checksum="",
                reviewer_decision="pending",
                review_notes="",
            )
            lexicon.add_or_update(entry)

            sheva_details = [
                {
                    "base_letter_index": a.base_letter_index,
                    "grapheme_cluster_id": a.grapheme_cluster_id,
                    "status": a.status.value,
                    "expected_phoneme": a.expected_phoneme,
                    "source": a.source.value,
                    "reason": a.reason,
                    "review_status": a.review_status,
                }
                for a in annotations
            ]

            comparison.append(
                {
                    "form_key": form.form_key,
                    "tense": group.tense,
                    "group_index": group_idx,
                    "form_index": form_idx,
                    "display_text": canonical,
                    "canonical_text": canonical,
                    "omit_silent_text": omit_silent,
                    "unpointed_text": unpointed,
                    "sheva_annotations": sheva_details,
                    "expected_pronunciation": expected_pronunciation,
                    "canonical_wav": str(canonical_path.relative_to(OUTPUT_DIR)),
                    "omit_silent_wav": str(omit_path.relative_to(OUTPUT_DIR)),
                    "unpointed_wav": str(unpointed_path.relative_to(OUTPUT_DIR)),
                    "canonical_duration": canonical_dur,
                    "omit_silent_duration": omit_dur,
                    "unpointed_duration": unpointed_dur,
                    "canonical_checksum": sha256_hex(canonical_path.read_bytes()),
                    "omit_silent_checksum": sha256_hex(omit_path.read_bytes()),
                    "unpointed_checksum": sha256_hex(unpointed_path.read_bytes()),
                }
            )

            for a in annotations:
                rows.append(
                    {
                        "form_key": form.form_key,
                        "tense": group.tense,
                        "display_text": canonical,
                        "base_letter_index": a.base_letter_index,
                        "grapheme_cluster_id": a.grapheme_cluster_id,
                        "status": a.status.value,
                        "expected_phoneme": a.expected_phoneme,
                        "source": a.source.value,
                        "reason": a.reason,
                        "canonical_text": canonical,
                        "omit_silent_text": omit_silent,
                        "unpointed_text": unpointed,
                        "canonical_wav": canonical_path.name,
                        "omit_silent_wav": omit_path.name,
                        "unpointed_wav": unpointed_path.name,
                        "reviewer_decision": "pending",
                        "review_notes": "",
                    }
                )

    lexicon.save()
    (OUTPUT_DIR / "comparison_manifest.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if rows:
        with (OUTPUT_DIR / "review_sheet.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    _write_html_index(OUTPUT_DIR, comparison)
    _write_report(OUTPUT_DIR, comparison)


def _write_html_index(output_dir: Path, comparison: list[dict[str, Any]]) -> None:
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Sheva Diagnostic Package — 001_lichtov</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;}",
        ".card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0;}",
        "audio{width:100%;margin:.5rem 0;}",
        "table{border-collapse:collapse;width:100%;}",
        "td,th{border:1px solid #ddd;padding:.4rem;text-align:left;}",
        "th{background:#f5f5f5;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;}",
        "</style></head><body>",
        "<h1>Sheva Diagnostic Package — 001_lichtov</h1>",
        f"<p>{len(comparison)} forms contain U+05B0. Listen to each variant and record whether the sheva is pronounced as expected.</p>",
        "<p><strong>Variant A:</strong> canonical pointed text (accepted Hila audio reused).<br>",
        "<strong>Variant B:</strong> sheva marks classified as <em>silent</em> are omitted.<br>",
        "<strong>Variant C:</strong> all Hebrew diacritics removed.</p>",
    ]
    for item in comparison:
        safe = Path(item["canonical_wav"]).stem
        lines.append(f"<div class='card' id='{safe}'>")
        lines.append(f"<h2>{item['form_key']} — {item['tense']}</h2>")
        lines.append(f"<p class='rtl'><strong>Display:</strong> {item['display_text']}</p>")
        lines.append(f"<p class='rtl'><strong>Variant B:</strong> {item['omit_silent_text']}</p>")
        lines.append(f"<p class='rtl'><strong>Variant C:</strong> {item['unpointed_text']}</p>")
        lines.append(
            "<table><tr><th>index</th><th>cluster</th><th>status</th><th>expected</th><th>source</th><th>reason</th></tr>"
        )
        for a in item["sheva_annotations"]:
            lines.append(
                f"<tr><td>{a['base_letter_index']}</td><td>{a['grapheme_cluster_id']}</td>"
                f"<td>{a['status']}</td><td>{a['expected_phoneme']}</td><td>{a['source']}</td><td>{a['reason']}</td></tr>"
            )
        lines.append("</table>")
        for label, wav in [
            ("A canonical", item["canonical_wav"]),
            ("B omit silent", item["omit_silent_wav"]),
            ("C unpointed", item["unpointed_wav"]),
        ]:
            lines.append(f"<p>{label} ({_wav_duration(output_dir / wav):.3f}s)</p>")
            lines.append(f"<audio controls src='{wav}'></audio>")
        lines.append("</div>")
    lines.append("</body></html>")
    (output_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")


def _write_report(output_dir: Path, comparison: list[dict[str, Any]]) -> None:
    total = len(comparison)
    uncertain = sum(
        1 for item in comparison for a in item["sheva_annotations"] if a["status"] == "uncertain"
    )
    silent = sum(
        1 for item in comparison for a in item["sheva_annotations"] if a["status"] == "silent"
    )
    vocalic = sum(
        1 for item in comparison for a in item["sheva_annotations"] if a["status"] == "vocalic"
    )
    report = {
        "total_forms_with_sheva": total,
        "total_sheva_occurrences": sum(len(item["sheva_annotations"]) for item in comparison),
        "vocalic": vocalic,
        "silent": silent,
        "uncertain": uncertain,
        "unresolved_forms": sorted(
            {
                f"{item['tense']}/{item['form_key']}"
                for item in comparison
                if any(a["status"] == "uncertain" for a in item["sheva_annotations"])
            }
        ),
    }
    (output_dir / "sheva_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    build_diagnostic_package()
