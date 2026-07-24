#!/usr/bin/env python3
"""Prepare a human listening review package for a built SpeechGen mantra.

Usage:
    .venv/bin/python scripts/prepare_mantra_review_package.py \
        output/mantra_phase1_speechgen
"""
from __future__ import annotations

import csv
import html
import json
import shutil
import sys
from pathlib import Path

from mantra.phase1.spec import MantraSpecification
from mantra.phase1.utils import normalize_unicode


def _strip_vowels(text: str) -> str:
    """Return the consonantal skeleton of a Hebrew string."""
    normalized = normalize_unicode(text)
    return "".join(
        c for c in normalized if "\u0590" <= c <= "\u05ff" and not ("\u0591" <= c <= "\u05c7")
    )


def _display(value: object) -> str:
    """Render a metadata value for human readers."""
    return "—" if value is None or value == "" else str(value)


def build_review_package(build_dir: Path) -> Path:
    build_dir = build_dir.resolve()
    manifest_path = build_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    spec = MantraSpecification.from_dict(manifest["specification"])

    review_dir = build_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    forms_dir = review_dir / "forms"
    forms_dir.mkdir(parents=True, exist_ok=True)

    # Full mantra copy
    full_wav_src = build_dir / "mantra.wav"
    full_wav_dst = review_dir / "mantra.wav"
    shutil.copy2(full_wav_src, full_wav_dst)
    full_duration = manifest.get("actual_duration", 0.0)

    timeline = manifest["timeline"]
    rows: list[dict] = []
    for segment in timeline:
        if segment["segment_type"] != "hebrew_form":
            continue

        group_index = segment.get("group_index", 0)
        tense = spec.groups[group_index].tense if group_index < len(spec.groups) else ""
        form_index = segment.get("form_index", 0)
        form = (
            spec.groups[group_index].forms[form_index]
            if group_index < len(spec.groups) and form_index < len(spec.groups[group_index].forms)
            else None
        )
        form_key = segment["grammatical_metadata"].get("form_key", form.form_key if form else "unknown")
        hebrew_vocalized = segment["source_text"]
        hebrew_unvocalized = form.hebrew_plain if form else _strip_vowels(hebrew_vocalized)
        person = segment["grammatical_metadata"].get("person") or (form.person if form else "")
        number = segment["grammatical_metadata"].get("number") or (form.number if form else "")
        gender = segment["grammatical_metadata"].get("gender") or (form.gender if form else "")

        # Find the preceding italian_cue in the same cycle/repetition group
        italian_cue_text = ""
        for prev in reversed(timeline[: timeline.index(segment)]):
            if prev["segment_type"] == "italian_cue":
                italian_cue_text = prev["source_text"]
                break

        src_wav = build_dir / segment["artifact_reference"]
        if not src_wav.exists():
            raise FileNotFoundError(f"Segment WAV missing: {src_wav}")

        form_filename = f"{len(rows) + 1:02d}_{form_key}.wav"
        dst_wav = forms_dir / form_filename
        shutil.copy2(src_wav, dst_wav)

        rows.append(
            {
                "segment_id": segment["segment_id"],
                "form_key": form_key,
                "tense": tense,
                "hebrew_unvocalized": hebrew_unvocalized,
                "hebrew_vocalized": hebrew_vocalized,
                "italian_cue": italian_cue_text,
                "person": person,
                "number": number,
                "gender": gender,
                "cycle": segment["cycle_index"],
                "repetition": segment["repetition_index"],
                "source_voice": segment["voice"],
                "segment_filename": form_filename,
                "actual_duration": segment["actual_duration"],
                "pronunciation_ok": "",
                "stress_ok": "",
                "cadence_ok": "",
                "pause_ok": "",
                "comments": "",
            }
        )

    # JSON review sheet
    review_json_path = review_dir / "review_sheet.json"
    review_json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV review sheet
    review_csv_path = review_dir / "review_sheet.csv"
    if rows:
        with review_csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # HTML index
    html_path = review_dir / "index.html"
    html_path.write_text(_render_html(rows, full_duration), encoding="utf-8")

    return review_dir


def _render_html(rows: list[dict], full_duration: float) -> str:
    form_cards = []
    for row in rows:
        form_cards.append(
            f"""
    <div class="form-card">
      <h2>{html.escape(row['form_key'])} <span class="tense">({html.escape(row['tense'])})</span></h2>
      <p class="hebrew unvocalized">{html.escape(row['hebrew_unvocalized'])}</p>
      <p class="hebrew vocalized">{html.escape(row['hebrew_vocalized'])}</p>
      <p class="cue">Italian cue: {html.escape(row['italian_cue'])}</p>
      <p class="meta">
        person={html.escape(_display(row['person']))}
        | number={html.escape(_display(row['number']))}
        | gender={html.escape(_display(row['gender']))}
        | cycle={row['cycle']}
        | repetition={row['repetition']}
        | duration={row['actual_duration']:.3f}s
        | voice={html.escape(row['source_voice'])}
      </p>
      <audio controls src="forms/{html.escape(row['segment_filename'])}"></audio>
      <form class="review-form">
        <label><input type="checkbox" name="pronunciation_ok"> Pronunciation OK</label>
        <label><input type="checkbox" name="stress_ok"> Stress OK</label>
        <label><input type="checkbox" name="cadence_ok"> Cadence OK</label>
        <label><input type="checkbox" name="pause_ok"> Pause OK</label>
        <textarea name="comments" placeholder="Comments..."></textarea>
      </form>
    </div>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mantra Phase 1 — SpeechGen Review</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 1rem; background: #f8f9fa; color: #212529; direction: ltr; }}
    h1 {{ text-align: center; }}
    .hebrew {{ font-size: 2rem; font-family: "Noto Sans Hebrew", "Segoe UI", sans-serif; margin: 0.25rem 0; }}
    .vocalized {{ color: #495057; }}
    .tense {{ font-size: 0.7em; color: #6c757d; font-weight: normal; }}
    .cue {{ color: #6c757d; font-style: italic; }}
    .meta {{ font-size: 0.9rem; color: #6c757d; }}
    .form-card {{ background: #fff; border-radius: 8px; padding: 1rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    audio {{ display: block; width: 100%; margin: 0.75rem 0; }}
    .review-form {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; }}
    .review-form label {{ display: block; }}
    .review-form textarea {{ grid-column: 1 / -1; width: 100%; min-height: 60px; }}
    .full-player {{ text-align: center; padding: 1rem; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  </style>
</head>
<body>
  <h1>Mantra Phase 1 — SpeechGen Hebrew Review</h1>
  <div class="full-player">
    <h2>Full Mantra</h2>
    <audio controls src="mantra.wav"></audio>
    <p>Total duration: {full_duration:.3f}s. Open individual forms below to review pronunciation, stress, cadence, and pauses.</p>
  </div>
  {''.join(form_cards)}
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: prepare_mantra_review_package.py <build_dir>", file=sys.stderr)
        sys.exit(1)
    review_dir = build_review_package(Path(sys.argv[1]))
    print(f"Review package ready: {review_dir}")
