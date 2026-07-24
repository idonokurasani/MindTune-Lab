#!/usr/bin/env python3
"""Full conjugation of לכתוב embedded in natural Hebrew sentences.

Reads data/mantra/scripts/001_lichtov.json, builds a subject + conjugated verb
+ direct object sentence for every form, validates agreement, synthesizes
pointed and unpointed variants with SpeechGen Hila, and assembles a review
package under output/mantra_phase1_full_context_conjugation/.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from mantra.phase1.assembly import _decode_wav_to_int16, _encode_int16_to_wav, _resample_mono_int16
from mantra.phase1.sheva import DIACRITICS
from mantra.phase1.timeline import TimelineSegment
from mantra.phase1.tts import SpeechGenTTSProvider, TTSRuntimeError, sha256_hex
from mantra.phase1.utils import load_json, normalize_unicode

OUTPUT_DIR = Path("output/mantra_phase1_full_context_conjugation")
TARGET_SR = 22050
FIXTURE_PATH = Path("data/mantra/scripts/001_lichtov.json")
POINTED_OBJECT = "מִכְתָּב"
UNPOINTED_OBJECT = "מכתב"

SUBJECT_PRONOUNS = {
    ("1", "singular", "masculine"): ("אני", "ani"),
    ("1", "singular", "feminine"): ("אני", "ani"),
    ("2", "singular", "masculine"): ("אתה", "ata"),
    ("2", "singular", "feminine"): ("את", "at"),
    ("3", "singular", "masculine"): ("הוא", "hu"),
    ("3", "singular", "feminine"): ("היא", "hi"),
    ("1", "plural", "masculine"): ("אנחנו", "anachnu"),
    ("1", "plural", "feminine"): ("אנחנו", "anachnu"),
    ("2", "plural", "masculine"): ("אתם", "atem"),
    ("2", "plural", "feminine"): ("אתן", "aten"),
    ("3", "plural", "masculine"): ("הם", "hem"),
    ("3", "plural", "feminine"): ("הן", "hen"),
}

# Expected transliterations for the conjugated verb stem, keyed by tense/form_key.
VERB_TRANSLIT: dict[str, str] = {
    "infinitive/infinitive": "likhtov",
    "infinitive/example": "kotev",
    "present/masculine_singular": "kotev",
    "present/feminine_singular": "kotevet",
    "present/masculine_plural": "kotvim",
    "present/feminine_plural": "kotvot",
    "past/1_singular": "katavti",
    "past/2_masculine_singular": "katavta",
    "past/2_feminine_singular": "katavt",
    "past/3_masculine_singular": "katav",
    "past/3_feminine_singular": "katva",
    "past/1_plural": "katavnu",
    "past/2_masculine_plural": "ktavtem",
    "past/2_feminine_plural": "ktavten",
    "past/3_plural": "katvu",
    "future/1_singular": "ekhtov",
    "future/2_masculine_singular": "tikhtov",
    "future/2_feminine_singular": "tikhtvi",
    "future/3_masculine_singular": "yikhtov",
    "future/3_feminine_singular": "tikhtov",
    "future/1_plural": "nikhtov",
    "future/2_plural": "tikhtvu",
    "future/3_plural": "yikhtvu",
}


def _strip_diacritics(text: str) -> str:
    return "".join(c for c in normalize_unicode(text) if c not in DIACRITICS)


def _parse_form_key(form_key: str, tense: str) -> dict[str, Any] | None:
    """Infer person, number, gender from a fixture form key."""
    if form_key == "infinitive" and tense == "infinitive":
        return {"form_key": form_key, "person": None, "number": None, "gender": None, "mood": "infinitive"}
    if form_key == "example" and tense == "infinitive":
        # The example is a present masculine-singular sentence.
        return {"form_key": form_key, "person": "1", "number": "singular", "gender": "masculine", "mood": "indicative"}

    parts = form_key.split("_")
    person = None
    number = None
    gender = None
    for part in parts:
        if part in {"1", "2", "3"}:
            person = part
        elif part in {"singular", "plural"}:
            number = part
        elif part in {"masculine", "feminine"}:
            gender = part
    return {"form_key": form_key, "person": person, "number": number, "gender": gender, "mood": "indicative"}


def _subject_for(tense: str, morph: dict[str, Any]) -> tuple[str, str]:
    """Return (hebrew, latin) subject pronoun for a form."""
    if tense == "infinitive" and morph["mood"] == "infinitive":
        return "אני", "ani"
    if tense == "infinitive" and morph["form_key"] == "example":
        return "אני", "ani"
    if tense == "present":
        # Use first-person for singular (illustrative) and third-person for plural.
        if morph["number"] == "singular":
            return "אני", "ani"
        if morph.get("gender") == "masculine":
            return "הם", "hem"
        return "הן", "hen"
    # First person is common gender in singular and plural.
    if morph.get("person") == "1":
        if morph.get("number") == "plural":
            return "אנחנו", "anachnu"
        return "אני", "ani"
    # Unmarked plural defaults to masculine (e.g., 3_plural, 2_plural without gender).
    gender = morph.get("gender") or "masculine"
    key = (morph.get("person"), morph.get("number"), gender)
    return SUBJECT_PRONOUNS.get(key, ("", ""))


def _expected_transliteration(tense: str, form_key: str, subject_latin: str, verb_latin: str) -> str:
    if tense == "infinitive" and form_key == "infinitive":
        return f"{subject_latin} rotse {verb_latin} mikhtav"
    if tense == "infinitive" and form_key == "example":
        return f"{subject_latin} {verb_latin} mikhtav"
    return f"{subject_latin} {verb_latin} mikhtav"


def _build_sentences(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Construct the full sentence table from the fixture."""
    sentences: list[dict[str, Any]] = []
    for section in data["sections"]:
        tense = section["section"]
        for line in section["lines"]:
            form_key = line["form_key"]
            morph = _parse_form_key(form_key, tense)
            if morph is None:
                raise ValueError(f"Could not parse form_key {form_key!r} in tense {tense!r}")

            raw_text = normalize_unicode(line["hebrew_with_niqqud"])
            subject_he, subject_latin = _subject_for(tense, morph)
            verb_latin = VERB_TRANSLIT.get(f"{tense}/{form_key}", "")

            if tense == "infinitive" and form_key == "infinitive":
                # Contextual phrase: "I want to write a letter."
                auxiliary = "רוֹצֶה"
                verb_pointed = raw_text
                pointed_sentence = f"{subject_he} {auxiliary} {verb_pointed} {POINTED_OBJECT}"
            elif tense == "infinitive" and form_key == "example":
                # Fixture already provides a full example sentence; extract the verb token.
                pointed_sentence = raw_text
                words = pointed_sentence.split()
                if len(words) >= 2:
                    verb_pointed = words[1]
                else:
                    verb_pointed = raw_text
            else:
                verb_pointed = raw_text
                pointed_sentence = f"{subject_he} {verb_pointed} {POINTED_OBJECT}"

            unpointed_sentence = _strip_diacritics(pointed_sentence)
            expected = _expected_transliteration(tense, form_key, subject_latin, verb_latin)

            sentences.append(
                {
                    "form_id": f"{tense}/{form_key}",
                    "tense": tense,
                    "mood": morph["mood"],
                    "form_key": form_key,
                    "person": morph["person"],
                    "number": morph["number"],
                    "gender": morph["gender"],
                    "subject_hebrew": subject_he,
                    "subject_latin": subject_latin,
                    "verb_hebrew": verb_pointed,
                    "verb_latin": verb_latin,
                    "object_hebrew": POINTED_OBJECT,
                    "object_latin": "mikhtav",
                    "pointed_sentence": pointed_sentence,
                    "unpointed_sentence": unpointed_sentence,
                    "expected_transliteration": expected,
                    "italian_gloss": line.get("italian_gloss", ""),
                }
            )
    return sentences


def _validate(sentences: list[dict[str, Any]]) -> tuple[bool, list[str]]:  # noqa: C901
    """Validate subject-verb agreement and pointed/unpointed equivalence."""
    ok = True
    report: list[str] = []
    report.append("# Full Context Conjugation Validation Report\n")
    report.append("| form_id | subject | verb | object | pointed | unpointed | check |")
    report.append("|---|---|---|---|---|---|---|")

    for s in sentences:
        form_id = s["form_id"]
        # 1. Verify unpointed is the diacritic-free version of pointed.
        stripped = _strip_diacritics(s["pointed_sentence"])
        if stripped != s["unpointed_sentence"]:
            ok = False
            report.append(f"| {form_id} | ... | ... | ... | ... | ... | FAILED: pointed/unpointed mismatch |")
            continue

        # 2. Verify the verb token in the pointed sentence matches the fixture verb.
        pointed_words = s["pointed_sentence"].split()
        if s["tense"] == "infinitive" and s["form_key"] == "infinitive":
            # verb is the third token (subject, auxiliary, verb, object).
            verb_in_sentence = pointed_words[2] if len(pointed_words) >= 4 else ""
        elif s["tense"] == "infinitive" and s["form_key"] == "example":
            # Fixture example: subject verb object.
            verb_in_sentence = pointed_words[1] if len(pointed_words) >= 3 else ""
        else:
            # subject verb object.
            verb_in_sentence = pointed_words[1] if len(pointed_words) >= 3 else ""

        if _strip_diacritics(verb_in_sentence) != _strip_diacritics(s["verb_hebrew"]):
            ok = False
            report.append(
                f"| {form_id} | ... | ... | ... | ... | ... | FAILED: verb token mismatch |"
            )
            continue

        # 3. Basic subject-verb agreement sanity.
        issues: list[str] = []
        if s["tense"] == "present":
            # The verb form carries number/gender.  Subject must agree in number/gender.
            if s["number"] == "singular":
                # First-person singular subjects are fine for any singular verb form.
                pass
            else:
                if s["gender"] == "masculine" and s["subject_hebrew"] not in ("הם", "אנחנו", "אתם"):
                    issues.append("m.pl subject mismatch")
                if s["gender"] == "feminine" and s["subject_hebrew"] not in ("הן", "אנחנו", "אתן"):
                    issues.append("f.pl subject mismatch")
        if issues:
            ok = False
            report.append(
                f"| {form_id} | {s['subject_hebrew']} | {s['verb_hebrew']} | {s['object_hebrew']} | "
                f"{s['pointed_sentence']} | {s['unpointed_sentence']} | FAILED: {', '.join(issues)} |"
            )
            continue

        report.append(
            f"| {form_id} | {s['subject_hebrew']} | {s['verb_hebrew']} | {s['object_hebrew']} | "
            f"{s['pointed_sentence']} | {s['unpointed_sentence']} | OK |"
        )

    return ok, report


def _synthesize(
    provider: SpeechGenTTSProvider, text: str, seg_id: str
) -> tuple[bytes, int, float] | None:
    """Synthesize and normalize one text to 22050 Hz mono WAV."""
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


def _safe_filename(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text).strip("_")[:80]


def _italian_label(sentence: dict[str, Any]) -> str:
    """Return an Italian grammatical label for the comparison track."""
    tense_map = {
        "infinitive": "infinito",
        "present": "presente",
        "past": "passato",
        "future": "futuro",
    }
    tense_it = tense_map.get(sentence["tense"], sentence["tense"])
    if sentence["tense"] == "infinitive" and sentence["form_key"] == "infinitive":
        return "Infinitivo"
    if sentence["tense"] == "infinitive" and sentence["form_key"] == "example":
        return "Esempio"
    parts = [tense_it]
    if sentence["person"]:
        parts.append(sentence["person"])
    if sentence["gender"]:
        parts.append("maschile" if sentence["gender"] == "masculine" else "femminile")
    if sentence["number"]:
        parts.append("singolare" if sentence["number"] == "singular" else "plurale")
    return " ".join(parts).capitalize()


def _silence(seconds: float) -> np.ndarray:
    return np.zeros(int(TARGET_SR * seconds), dtype=np.int16)


def build_diagnostic() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    data = load_json(FIXTURE_PATH)
    sentences = _build_sentences(data)

    print("Complete sentence table:")
    for s in sentences:
        print(f"  {s['form_id']}: {s['pointed_sentence']}  /  {s['unpointed_sentence']}")

    ok, report_lines = _validate(sentences)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "sentences.json").write_text(
        json.dumps(sentences, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "validation_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    if not ok:
        raise SystemExit("Validation failed; see validation_report.md")

    pointed_dir = OUTPUT_DIR / "pointed"
    unpointed_dir = OUTPUT_DIR / "unpointed"
    pointed_dir.mkdir(exist_ok=True)
    unpointed_dir.mkdir(exist_ok=True)

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

    for s in sentences:
        form_id = s["form_id"]
        safe_id = _safe_filename(form_id)
        pointed_path = pointed_dir / f"{safe_id}.wav"
        unpointed_path = unpointed_dir / f"{safe_id}.wav"

        pointed = _synthesize(he_provider, s["pointed_sentence"], f"ctx_pointed_{safe_id}")
        unpointed = _synthesize(he_provider, s["unpointed_sentence"], f"ctx_unpointed_{safe_id}")

        if pointed is None or unpointed is None:
            print(f"Synthesis failed for {form_id}")
            manifest.append(
                {
                    "form_id": form_id,
                    "status": "failed",
                    "error": "synthesis failed",
                }
            )
            continue

        pointed_path.write_bytes(pointed[0])
        unpointed_path.write_bytes(unpointed[0])

        label = _italian_label(s)
        label_audio = _synthesize(it_provider, label, f"ctx_label_{safe_id}")
        if label_audio is None:
            print(f"Italian label failed for {form_id}")
            continue

        # comparison: label, pointed, 1s, unpointed, 2s.
        comparison_parts.append(_decode_wav_to_int16(label_audio[0])[0])
        comparison_parts.append(_decode_wav_to_int16(pointed[0])[0])
        comparison_parts.append(_silence(1.0))
        comparison_parts.append(_decode_wav_to_int16(unpointed[0])[0])
        comparison_parts.append(_silence(2.0))

        for _, variant, (audio, src_sr, dur), path in [
            ("pointed", "pointed", pointed, pointed_path),
            ("unpointed", "unpointed", unpointed, unpointed_path),
        ]:
            manifest.append(
                {
                    "form_id": form_id,
                    "submitted_text": s["pointed_sentence"] if variant == "pointed" else s["unpointed_sentence"],
                    "code_points": [
                        f"U+{ord(c):04X}"
                        for c in (s["pointed_sentence"] if variant == "pointed" else s["unpointed_sentence"])
                    ],
                    "subject": s["subject_hebrew"],
                    "conjugated_verb": s["verb_hebrew"],
                    "direct_object": s["object_hebrew"],
                    "tense_mood": s["tense"],
                    "person": s["person"],
                    "number": s["number"],
                    "gender": s["gender"],
                    "variant": variant,
                    "provider": "speechgen",
                    "voice": "Hila",
                    "locale": "he-IL",
                    "source_sample_rate": src_sr,
                    "normalized_sample_rate": TARGET_SR,
                    "duration": dur,
                    "checksum": sha256_hex(audio),
                    "file": str(path),
                    "expected_transliteration": s["expected_transliteration"],
                }
            )

    if comparison_parts:
        combined = np.concatenate(comparison_parts)
        comparison_bytes = _encode_int16_to_wav(combined, TARGET_SR)
        comparison_path = OUTPUT_DIR / "comparison.wav"
        comparison_path.write_bytes(comparison_bytes)
        print(f"comparison.wav: {len(combined)/TARGET_SR:.1f}s")

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_html_index(OUTPUT_DIR, sentences)
    print(f"Generated {len(manifest)//2} form pairs in {OUTPUT_DIR}")


def _write_html_index(output_dir: Path, sentences: list[dict[str, Any]]) -> None:
    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Full Context Conjugation — 001_lichtov</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;}",
        ".card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0;}",
        "audio{width:100%;margin:.5rem 0;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;}",
        "textarea{width:100%;height:60px;}",
        "</style></head><body>",
        "<h1>Full Context Conjugation — 001_lichtov</h1>",
        "<p><audio controls src='comparison.wav'></audio> (full comparison)</p>",
    ]
    for s in sentences:
        safe_id = _safe_filename(s["form_id"])
        lines.append("<div class='card'>")
        lines.append(f"<h2>{s['form_id']}</h2>")
        lines.append(f"<p>subject: {s['subject_hebrew']} ({s['subject_latin']})</p>")
        lines.append(f"<p>tense/mood: {s['tense']} / {s['mood']}</p>")
        lines.append(f"<p>person: {s['person'] or '-'} | number: {s['number'] or '-'} | gender: {s['gender'] or '-'}</p>")
        lines.append(f"<p>canonical verb: <span class='rtl'>{s['verb_hebrew']}</span></p>")
        lines.append(f"<p>expected: <em>{s['expected_transliteration']}</em></p>")
        lines.append(f"<p class='rtl'><strong>Pointed:</strong> {s['pointed_sentence']}</p>")
        lines.append(f"<audio controls src='pointed/{safe_id}.wav'></audio>")
        lines.append(f"<p class='rtl'><strong>Unpointed:</strong> {s['unpointed_sentence']}</p>")
        lines.append(f"<audio controls src='unpointed/{safe_id}.wav'></audio>")
        lines.append("<p>Review notes:</p>")
        lines.append(f"<textarea placeholder='notes for {s['form_id']}'></textarea>")
        lines.append("</div>")
    lines.append("</body></html>")
    (output_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    build_diagnostic()
