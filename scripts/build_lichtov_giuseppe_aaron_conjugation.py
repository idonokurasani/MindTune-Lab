#!/usr/bin/env python3
"""Complete לכתוב conjugation package with Giuseppe (it-IT) and Aaron (he-IL).

Produces:
  output/mantra_phase1_lichtov_giuseppe_aaron/

with per-entry Italian labels, Hebrew sentences, isolated Hebrew forms,
per-tense combined WAVs, a complete conjugation WAV, and HTML/manifest/
conjugation/validation files.  No Hila audio or cache is reused.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from mantra.phase1.assembly import _decode_wav_to_int16, _encode_int16_to_wav, _resample_mono_int16
from mantra.phase1.sheva import DIACRITICS
from mantra.phase1.timeline import TimelineSegment
from mantra.phase1.tts import (
    SpeechGenTTSProvider,
    TTSCache,
    TTSRuntimeError,
    _cache_key,
    sha256_hex,
)
from mantra.phase1.utils import normalize_unicode

OUTPUT_DIR = Path("output/mantra_phase1_lichtov_giuseppe_aaron")
CACHE_DIR = OUTPUT_DIR / "cache"
TARGET_SR = 22050

HEBREW_VOICE = "Aaron"
HEBREW_LOCALE = "he-IL"
ITALIAN_VOICE = "Giuseppe"
ITALIAN_LOCALE = "it-IT"
PROVIDER = "speechgen"

HEBREW_RATE = 1.0
HEBREW_PITCH = 0.0
ITALIAN_RATE = 1.0
ITALIAN_PITCH = 0.0
FORMAT = "wav"

POINTED_OBJECT = "מִכְתָּב"
UNPOINTED_OBJECT = "מכתב"


@dataclass
class ConjugationEntry:
    entry_id: str
    tense: str
    mood: str
    person: str
    number: str
    gender: str
    subject: str
    subject_latin: str
    form_source: str
    form_tts: str
    form_latin: str
    sentence_source: str
    sentence_tts: str
    sentence_latin: str
    italian_label: str
    italian_translation: str


def _strip_diacritics(text: str) -> str:
    return "".join(c for c in normalize_unicode(text) if c not in DIACRITICS)


def _safe_name(text: str) -> str:
    """Return a filesystem-safe ASCII name from unpointed Hebrew or Latin."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text).strip("_")[:80]


# ---------------------------------------------------------------------------
# Catalogue / Aaron identifier
# ---------------------------------------------------------------------------


def _fetch_voice_catalogue(api_key: str, email: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"token": api_key, "email": email})
    url = f"https://speechgen.io/index.php?r=api/voices&{params}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return cast(dict[str, Any], json.loads(resp.read().decode("utf-8")))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:500]
        raise TTSRuntimeError(f"SpeechGen voice catalogue HTTP {exc.code}: {body}") from exc


def _resolve_aaron_metadata(catalogue: dict[str, Any]) -> dict[str, Any]:
    for lang, voices in catalogue.items():
        if lang.lower() == "hebrew":
            for v in voices:
                if v.get("voice") == HEBREW_VOICE:
                    return cast(dict[str, Any], v)
    raise TTSRuntimeError(f"{HEBREW_VOICE!r} not found in SpeechGen Hebrew catalogue")


# ---------------------------------------------------------------------------
# Conjugation data
# ---------------------------------------------------------------------------


def _entries() -> list[ConjugationEntry]:
    entries: list[ConjugationEntry] = []

    def add(**kwargs: Any) -> None:
        entries.append(ConjugationEntry(**kwargs))

    # A. Infinitive
    add(
        entry_id="infinitive",
        tense="infinitive",
        mood="infinitive",
        person="",
        number="",
        gender="",
        subject="אֲנִי",
        subject_latin="ani",
        form_source="לִכְתּוֹב",
        form_tts="לכתוב",
        form_latin="likhtov",
        sentence_source="אֲנִי רוֹצֶה לִכְתּוֹב מִכְתָּב",
        sentence_tts="אני רוצה לכתוב מכתב",
        sentence_latin="ani rotse likhtov mikhtav",
        italian_label="Infinito",
        italian_translation="scrivere",
    )

    # B. Present tense (participial)
    present_forms = [
        ("masculine", "singular", "כּוֹתֵב", "kotev"),
        ("feminine", "singular", "כּוֹתֶבֶת", "kotevet"),
        ("masculine", "plural", "כּוֹתְבִים", "kotvim"),
        ("feminine", "plural", "כּוֹתְבוֹת", "kotvot"),
    ]
    present_subjects = [
        ("1", "masculine", "singular", "אֲנִי", "ani", "io scrivo"),
        ("1", "feminine", "singular", "אֲנִי", "ani", "io scrivo (f.)"),
        ("2", "masculine", "singular", "אַתָּה", "ata", "tu scrivi"),
        ("2", "feminine", "singular", "אַתְּ", "at", "tu scrivi (f.)"),
        ("3", "masculine", "singular", "הוּא", "hu", "lui scrive"),
        ("3", "feminine", "singular", "הִיא", "hi", "lei scrive"),
        ("1", "masculine", "plural", "אֲנַחְנוּ", "anachnu", "noi scriviamo"),
        ("1", "feminine", "plural", "אֲנַחְנוּ", "anachnu", "noi scriviamo (f.)"),
        ("2", "masculine", "plural", "אַתֶּם", "atem", "voi scrivete"),
        ("2", "feminine", "plural", "אַתֶּן", "aten", "voi scrivete (f.)"),
        ("3", "masculine", "plural", "הֵם", "hem", "loro scrivono"),
        ("3", "feminine", "plural", "הֵן", "hen", "loro scrivono (f.)"),
    ]
    for person, gender, number, subject, subj_lat, it_trans in present_subjects:
        form_src, form_lat = next(
            (f, lat) for g, n, f, lat in present_forms if g == gender and n == number
        )
        person_it = {"1": "prima", "2": "seconda", "3": "terza"}[person]
        gender_it = "maschile" if gender == "masculine" else "femminile"
        number_it = "singolare" if number == "singular" else "plurale"
        add(
            entry_id=f"present_{person}_{gender}_{number}",
            tense="present",
            mood="participial",
            person=person,
            number=number,
            gender=gender or "",
            subject=subject,
            subject_latin=subj_lat,
            form_source=form_src,
            form_tts=_strip_diacritics(form_src),
            form_latin=form_lat,
            sentence_source=f"{subject} {form_src} {POINTED_OBJECT}",
            sentence_tts=_strip_diacritics(f"{subject} {form_src} {POINTED_OBJECT}"),
            sentence_latin=f"{subj_lat} {form_lat} mikhtav",
            italian_label=f"Presente, {person_it} persona {number_it} {gender_it}",
            italian_translation=it_trans,
        )

    # C. Past tense
    past_forms = [
        ("1", None, "singular", "כָּתַבְתִּי", "katavti", "io scrissi"),
        ("2", "masculine", "singular", "כָּתַבְתָּ", "katavta", "tu scrivesti"),
        ("2", "feminine", "singular", "כָּתַבְתְּ", "katavt", "tu scrivesti (f.)"),
        ("3", "masculine", "singular", "כָּתַב", "katav", "lui scrisse"),
        ("3", "feminine", "singular", "כָּתְבָה", "katva", "lei scrisse"),
        ("1", None, "plural", "כָּתַבְנוּ", "katavnu", "noi scrivemmo"),
        ("2", "masculine", "plural", "כְּתַבְתֶּם", "ktavtem", "voi scriveste"),
        ("2", "feminine", "plural", "כְּתַבְתֶּן", "ktavten", "voi scriveste (f.)"),
        ("3", "masculine", "plural", "כָּתְבוּ", "katvu", "loro scrissero"),
    ]
    subjects_past = {
        ("1", None, "singular"): ("אֲנִי", "ani"),
        ("2", "masculine", "singular"): ("אַתָּה", "ata"),
        ("2", "feminine", "singular"): ("אַתְּ", "at"),
        ("3", "masculine", "singular"): ("הוּא", "hu"),
        ("3", "feminine", "singular"): ("הִיא", "hi"),
        ("1", None, "plural"): ("אֲנַחְנוּ", "anachnu"),
        ("2", "masculine", "plural"): ("אַתֶּם", "atem"),
        ("2", "feminine", "plural"): ("אַתֶּן", "aten"),
        ("3", "masculine", "plural"): ("הֵם", "hem"),
    }
    for past_person, past_gender, past_number, form_src, form_lat, it_trans in past_forms:
        subject, subj_lat = subjects_past[(past_person, past_gender, past_number)]
        person_it = {"1": "prima", "2": "seconda", "3": "terza"}[past_person]
        number_it = "singolare" if past_number == "singular" else "plurale"
        gender_it = ""
        if past_gender:
            gender_it = " maschile" if past_gender == "masculine" else " femminile"
        add(
            entry_id=f"past_{past_person}_{past_gender or 'common'}_{past_number}",
            tense="past",
            mood="indicative",
            person=past_person,
            number=past_number,
            gender=past_gender or "",
            subject=subject,
            subject_latin=subj_lat,
            form_source=form_src,
            form_tts=_strip_diacritics(form_src),
            form_latin=form_lat,
            sentence_source=f"{subject} {form_src} {POINTED_OBJECT}",
            sentence_tts=_strip_diacritics(f"{subject} {form_src} {POINTED_OBJECT}"),
            sentence_latin=f"{subj_lat} {form_lat} mikhtav",
            italian_label=f"Passato, {person_it} persona {number_it}{gender_it}".strip(),
            italian_translation=it_trans,
        )

    # D. Future tense
    # Surface forms are shared by some person/gender pairs; entries duplicate
    # them with explicit subjects.
    future_cases = [
        ("1", None, "singular", "אֶכְתּוֹב", "ekhtov", "io scriverò"),
        ("2", "masculine", "singular", "תִּכְתּוֹב", "tikhtov", "tu scriverai"),
        ("3", "feminine", "singular", "תִּכְתּוֹב", "tikhtov", "lei scriverà"),
        ("2", "feminine", "singular", "תִּכְתְּבִי", "tikhtvi", "tu scriverai (f.)"),
        ("3", "masculine", "singular", "יִכְתּוֹב", "yikhtov", "lui scriverà"),
        ("1", None, "plural", "נִכְתּוֹב", "nikhtov", "noi scriveremo"),
        ("2", "masculine", "plural", "תִּכְתְּבוּ", "tikhtvu", "voi scriverete"),
        ("2", "feminine", "plural", "תִּכְתְּבוּ", "tikhtvu", "voi scriverete (f.)"),
        ("3", "masculine", "plural", "יִכְתְּבוּ", "yikhtvu", "loro scriveranno"),
        ("3", "feminine", "plural", "יִכְתְּבוּ", "yikhtvu", "loro scriveranno (f.)"),
    ]
    subjects_future = {
        ("1", None, "singular"): ("אֲנִי", "ani"),
        ("2", "masculine", "singular"): ("אַתָּה", "ata"),
        ("3", "feminine", "singular"): ("הִיא", "hi"),
        ("2", "feminine", "singular"): ("אַתְּ", "at"),
        ("3", "masculine", "singular"): ("הוּא", "hu"),
        ("1", None, "plural"): ("אֲנַחְנוּ", "anachnu"),
        ("2", "masculine", "plural"): ("אַתֶּם", "atem"),
        ("2", "feminine", "plural"): ("אַתֶּן", "aten"),
        ("3", "masculine", "plural"): ("הֵם", "hem"),
        ("3", "feminine", "plural"): ("הֵן", "hen"),
    }
    for future_person, future_gender, future_number, form_src, form_lat, it_trans in future_cases:
        subject, subj_lat = subjects_future[(future_person, future_gender, future_number)]
        person_it = {"1": "prima", "2": "seconda", "3": "terza"}[future_person]
        number_it = "singolare" if future_number == "singular" else "plurale"
        gender_it = ""
        if future_gender:
            gender_it = " maschile" if future_gender == "masculine" else " femminile"
        add(
            entry_id=f"future_{future_person}_{future_gender or 'common'}_{future_number}",
            tense="future",
            mood="indicative",
            person=future_person,
            number=future_number,
            gender=future_gender or "",
            subject=subject,
            subject_latin=subj_lat,
            form_source=form_src,
            form_tts=_strip_diacritics(form_src),
            form_latin=form_lat,
            sentence_source=f"{subject} {form_src} {POINTED_OBJECT}",
            sentence_tts=_strip_diacritics(f"{subject} {form_src} {POINTED_OBJECT}"),
            sentence_latin=f"{subj_lat} {form_lat} mikhtav",
            italian_label=f"Futuro, {person_it} persona {number_it}{gender_it}".strip(),
            italian_translation=it_trans,
        )

    # E. Imperative
    imperative_forms = [
        ("masculine", "singular", "כְּתֹב", "ktov", "scrivi! (m.s.)"),
        ("feminine", "singular", "כִּתְבִי", "kitvi", "scrivi! (f.s.)"),
        (None, "plural", "כִּתְבוּ", "kitvu", "scrivete!"),
    ]
    for imp_gender, imp_number, form_src, form_lat, it_trans in imperative_forms:
        number_it = "singolare" if imp_number == "singular" else "plurale"
        if imp_gender == "masculine":
            gender_it = "maschile"
        elif imp_gender == "feminine":
            gender_it = "femminile"
        else:
            gender_it = ""
        add(
            entry_id=f"imperative_{imp_gender or 'plural'}_{imp_number}",
            tense="imperative",
            mood="imperative",
            person="2",
            number=imp_number,
            gender=imp_gender or "",
            subject="",
            subject_latin="",
            form_source=form_src,
            form_tts=_strip_diacritics(form_src),
            form_latin=form_lat,
            sentence_source=f"{form_src} {POINTED_OBJECT}",
            sentence_tts=_strip_diacritics(f"{form_src} {POINTED_OBJECT}"),
            sentence_latin=f"{form_lat} mikhtav",
            italian_label=(
                f"Imperativo, {gender_it} {number_it}" if gender_it else f"Imperativo, {number_it}"
            ),
            italian_translation=it_trans,
        )

    # F. Verbal noun
    add(
        entry_id="verbal_noun",
        tense="verbal_noun",
        mood="verbal_noun",
        person="",
        number="",
        gender="",
        subject="",
        subject_latin="",
        form_source="כְּתִיבָה",
        form_tts="כתיבה",
        form_latin="ktiva",
        sentence_source="כְּתִיבַת מִכְתָּב",
        sentence_tts="כתיבת מכתב",
        sentence_latin="ktivat mikhtav",
        italian_label="Nome verbale",
        italian_translation="la scrittura di una lettera",
    )

    return entries


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(
    entries: list[ConjugationEntry], aaron_meta: dict[str, Any]
) -> list[str]:  # noqa: C901
    report: list[str] = ["# Conjugation validation report\n"]
    ok = True

    report.append("## Aaron voice identifier")
    report.append(f"- SpeechGen `voice` field: `{aaron_meta.get('voice')}`")
    report.append(
        f"- type: {aaron_meta.get('type')!r}, sex: {aaron_meta.get('sex')!r}, cpm: {aaron_meta.get('cpm')!r}"
    )
    report.append("")

    report.append("## Entry validation")
    report.append("| entry_id | tense | subject | form | sentence | checks |")
    report.append("|---|---|---|---|---|---|")

    for e in entries:
        issues: list[str] = []
        # source/tts equivalence
        if _strip_diacritics(e.form_source) != e.form_tts:
            issues.append("form source/tts mismatch")
        expected_sentence = _strip_diacritics(e.sentence_source)
        if expected_sentence != e.sentence_tts:
            issues.append("sentence source/tts mismatch")
        # Every contextual sentence should contain the direct object.
        if UNPOINTED_OBJECT not in e.sentence_tts:
            issues.append("missing direct object")
        # source_text must retain niqqud (or at least diacritics).
        if not any(c in DIACRITICS for c in e.form_source + e.sentence_source):
            issues.append("source lacks niqqud")
        # Routing guardrails
        if "Hila" in e.form_source or "Hila" in e.sentence_source or "Hila" in e.italian_label:
            issues.append("Hila in source text")
        if e.tense == "imperative":
            if e.subject:
                issues.append("imperative has subject")
            if e.person != "2":
                issues.append("imperative person not 2")
        if e.tense == "present":
            if not e.person or not e.number or not e.gender:
                issues.append("present metadata incomplete")
        if e.tense in {"past", "future"} and not e.subject:
            issues.append("finite form missing subject")
        if issues:
            ok = False
        status = "OK" if not issues else f"FAILED: {', '.join(issues)}"
        report.append(
            f"| {e.entry_id} | {e.tense} | {e.subject} | {e.form_source} | {e.sentence_source} | {status} |"
        )

    if not ok:
        report.append("")
        report.append("**Validation failed.** No synthesis performed.")
        raise ValueError("Conjugation validation failed; see validation_report.md")

    report.append("")
    report.append("All validation checks passed.")
    return report


# ---------------------------------------------------------------------------
# Synthesis helpers
# ---------------------------------------------------------------------------


def _ensure_audio(
    text: str,
    provider_name: str,
    voice: str,
    locale: str,
    rate: float,
    pitch: float,
    fmt: str,
    cache: TTSCache,
    provider: SpeechGenTTSProvider,
    seg_id: str,
    event_log: list[dict[str, Any]],
) -> tuple[bytes, int, float, str]:
    key = _cache_key(text, provider_name, voice, rate, pitch, fmt, None, locale=locale)
    cached = cache.get(key)
    if cached is not None:
        samples, source_sr = _decode_wav_to_int16(cached.audio_bytes)
        if source_sr != TARGET_SR:
            samples = _resample_mono_int16(samples, source_sr, TARGET_SR)
            out_bytes = _encode_int16_to_wav(samples, TARGET_SR)
        else:
            out_bytes = cached.audio_bytes
        duration = len(samples) / TARGET_SR
        event_log.append(
            {
                "event": "cache_hit",
                "segment_id": seg_id,
                "provider": provider_name,
                "voice": voice,
                "locale": locale,
                "text": text,
                "rate": rate,
                "pitch": pitch,
                "format": fmt,
                "cache_key": key,
                "duration": duration,
            }
        )
        return out_bytes, source_sr, duration, key

    segment = SimpleNamespace(
        segment_id=seg_id,
        source_text=text,
        tts_text=text,
        voice=voice,
        locale=locale,
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            result = provider.synthesize(cast(TimelineSegment, segment))
            break
        except TTSRuntimeError as exc:
            last_error = exc
            if attempt < 2:
                wait = 2**attempt
                print(f"Synthesis failed for {seg_id}, retrying in {wait}s: {exc}")
                time.sleep(wait)
    else:
        raise last_error or TTSRuntimeError(f"Synthesis failed for {seg_id}")

    samples, source_sr = _decode_wav_to_int16(result.audio_bytes)
    if source_sr != TARGET_SR:
        samples = _resample_mono_int16(samples, source_sr, TARGET_SR)
    out_bytes = _encode_int16_to_wav(samples, TARGET_SR)
    duration = len(samples) / TARGET_SR
    cache.put(key, result)
    event_log.append(
        {
            "event": "synthesize",
            "segment_id": seg_id,
            "provider": provider_name,
            "voice": voice,
            "locale": locale,
            "text": text,
            "rate": rate,
            "pitch": pitch,
            "format": fmt,
            "cache_key": key,
            "source_sample_rate": source_sr,
            "duration": duration,
        }
    )
    return out_bytes, source_sr, duration, key


def _silence(seconds: float) -> np.ndarray:
    return np.zeros(int(TARGET_SR * seconds), dtype=np.int16)


def _write_event_log(event_log: list[dict[str, Any]]) -> None:
    path = OUTPUT_DIR / "event_log.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for ev in event_log:
            f.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def main() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "audio" / "italian").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "audio" / "hebrew_sentences").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "audio" / "hebrew_forms").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "sections").mkdir(parents=True, exist_ok=True)

    catalogue = _fetch_voice_catalogue(api_key, email)
    aaron_meta = _resolve_aaron_metadata(catalogue)
    (OUTPUT_DIR / "aaron_metadata.json").write_text(
        json.dumps(aaron_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    event_log: list[dict[str, Any]] = [
        {
            "event": "voice_catalogue_query",
            "hebrew_voice_count": len(catalogue.get("Hebrew", [])),
            "resolved_voice": aaron_meta.get("voice"),
        }
    ]

    entries = _entries()
    validation_report = _validate(entries, aaron_meta)
    (OUTPUT_DIR / "validation_report.md").write_text("\n".join(validation_report), encoding="utf-8")

    cache = TTSCache(CACHE_DIR)
    he_provider = SpeechGenTTSProvider(
        voice=HEBREW_VOICE,
        rate=HEBREW_RATE,
        pitch=HEBREW_PITCH,
        fmt=FORMAT,
        locale=HEBREW_LOCALE,
    )
    it_provider = SpeechGenTTSProvider(
        voice=ITALIAN_VOICE,
        rate=ITALIAN_RATE,
        pitch=ITALIAN_PITCH,
        fmt=FORMAT,
        locale=ITALIAN_LOCALE,
    )

    conjugation: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []

    # form deduplication map keyed by (form_source, form_tts, voice, locale, rate, pitch)
    form_files: dict[tuple[str, str, str, str, float, float], Path] = {}

    section_parts: dict[str, list[np.ndarray]] = {
        "infinitive": [],
        "present": [],
        "past": [],
        "future": [],
        "imperative": [],
        "verbal_noun": [],
    }

    section_order = ["infinitive", "present", "past", "future", "imperative", "verbal_noun"]

    for e in entries:
        # Italian label
        label_path = OUTPUT_DIR / "audio" / "italian" / f"{e.entry_id}.wav"
        label_bytes, label_src_sr, label_dur, label_key = _ensure_audio(
            e.italian_label,
            PROVIDER,
            ITALIAN_VOICE,
            ITALIAN_LOCALE,
            ITALIAN_RATE,
            ITALIAN_PITCH,
            FORMAT,
            cache,
            it_provider,
            f"it_{e.entry_id}",
            event_log,
        )
        label_path.write_bytes(label_bytes)
        manifest.append(
            _manifest_row(
                e,
                "italian_label",
                label_path,
                label_bytes,
                label_src_sr,
                label_dur,
                label_key,
                e.italian_label,
                "it",
            )
        )

        # Hebrew sentence
        sentence_path = OUTPUT_DIR / "audio" / "hebrew_sentences" / f"{e.entry_id}.wav"
        sentence_bytes, sentence_src_sr, sentence_dur, sentence_key = _ensure_audio(
            e.sentence_tts,
            PROVIDER,
            HEBREW_VOICE,
            HEBREW_LOCALE,
            HEBREW_RATE,
            HEBREW_PITCH,
            FORMAT,
            cache,
            he_provider,
            f"he_sent_{e.entry_id}",
            event_log,
        )
        sentence_path.write_bytes(sentence_bytes)
        manifest.append(
            _manifest_row(
                e,
                "hebrew_sentence",
                sentence_path,
                sentence_bytes,
                sentence_src_sr,
                sentence_dur,
                sentence_key,
                e.sentence_tts,
                "he",
            )
        )

        # Hebrew isolated form (deduplicated)
        form_key = (
            e.form_source,
            e.form_tts,
            HEBREW_VOICE,
            HEBREW_LOCALE,
            HEBREW_RATE,
            HEBREW_PITCH,
        )
        if form_key in form_files:
            form_path = form_files[form_key]
            # Re-use cached form metadata for manifest: read file and compute dur
            form_bytes = form_path.read_bytes()
            form_samples, _ = _decode_wav_to_int16(form_bytes)
            form_dur = len(form_samples) / TARGET_SR
            form_src_sr = 0  # not re-synthesized
            form_cache_key = ""
        else:
            form_path = OUTPUT_DIR / "audio" / "hebrew_forms" / f"{_safe_name(e.form_tts)}.wav"
            form_bytes, form_src_sr, form_dur, form_cache_key = _ensure_audio(
                e.form_tts,
                PROVIDER,
                HEBREW_VOICE,
                HEBREW_LOCALE,
                HEBREW_RATE,
                HEBREW_PITCH,
                FORMAT,
                cache,
                he_provider,
                f"he_form_{e.entry_id}",
                event_log,
            )
            form_path.write_bytes(form_bytes)
            form_files[form_key] = form_path
            manifest.append(
                _manifest_row(
                    e,
                    "hebrew_form",
                    form_path,
                    form_bytes,
                    form_src_sr,
                    form_dur,
                    form_cache_key,
                    e.form_tts,
                    "he",
                )
            )

        # Entry combined audio: label, 0.2s, sentence, 0.2s, form, 1.0s
        label_samples, _ = _decode_wav_to_int16(label_bytes)
        sentence_samples, _ = _decode_wav_to_int16(sentence_bytes)
        form_samples, _ = _decode_wav_to_int16(form_bytes)
        entry_audio = np.concatenate(
            [
                label_samples,
                _silence(0.2),
                sentence_samples,
                _silence(0.2),
                form_samples,
                _silence(1.0),
            ]
        )
        section_parts[e.tense].append(entry_audio)

        conjugation.append(
            {
                "entry_id": e.entry_id,
                "tense": e.tense,
                "mood": e.mood,
                "person": e.person,
                "number": e.number,
                "gender": e.gender,
                "subject": e.subject,
                "subject_latin": e.subject_latin,
                "form_source": e.form_source,
                "form_tts": e.form_tts,
                "form_latin": e.form_latin,
                "sentence_source": e.sentence_source,
                "sentence_tts": e.sentence_tts,
                "sentence_latin": e.sentence_latin,
                "italian_label": e.italian_label,
                "italian_translation": e.italian_translation,
                "files": {
                    "italian_label": str(label_path),
                    "hebrew_sentence": str(sentence_path),
                    "hebrew_form": str(form_path),
                },
            }
        )

    # Per-tense WAVs
    complete_parts: list[np.ndarray] = []
    for tense in section_order:
        if section_parts[tense]:
            section_audio = np.concatenate(section_parts[tense])
            section_path = OUTPUT_DIR / "sections" / f"{tense}.wav"
            section_path.write_bytes(_encode_int16_to_wav(section_audio, TARGET_SR))
            manifest.append(
                {
                    "name": f"section_{tense}",
                    "file": str(section_path),
                    "text": tense,
                    "provider": PROVIDER,
                    "voice": HEBREW_VOICE,
                    "locale": HEBREW_LOCALE,
                    "output_sample_rate": TARGET_SR,
                    "duration": len(section_audio) / TARGET_SR,
                    "checksum": sha256_hex(section_path.read_bytes()),
                    "role": "section",
                }
            )
            complete_parts.append(section_audio)
            complete_parts.append(_silence(1.5))

    # Complete conjugation
    if complete_parts:
        # Trim trailing section silence
        if len(complete_parts) > 1 and np.max(np.abs(complete_parts[-1])) == 0:
            complete_parts = complete_parts[:-1]
        complete_audio = np.concatenate(complete_parts)
        complete_path = OUTPUT_DIR / "complete_conjugation.wav"
        complete_path.write_bytes(_encode_int16_to_wav(complete_audio, TARGET_SR))
        manifest.append(
            {
                "name": "complete_conjugation",
                "file": str(complete_path),
                "text": "complete לכתוב conjugation",
                "provider": PROVIDER,
                "voice": HEBREW_VOICE,
                "locale": HEBREW_LOCALE,
                "output_sample_rate": TARGET_SR,
                "duration": len(complete_audio) / TARGET_SR,
                "checksum": sha256_hex(complete_path.read_bytes()),
                "role": "complete",
            }
        )

    (OUTPUT_DIR / "conjugation.json").write_text(
        json.dumps(conjugation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _write_index_html(conjugation)
    _write_event_log(event_log)

    print(f"Generated {len(entries)} entries in {OUTPUT_DIR}")
    print(f"SpeechGen requests: {len([e for e in event_log if e.get('event') == 'synthesize'])}")
    print(f"Cache hits: {len([e for e in event_log if e.get('event') == 'cache_hit'])}")


def _manifest_row(
    e: ConjugationEntry,
    role: str,
    path: Path,
    audio_bytes: bytes,
    source_sr: int,
    duration: float,
    cache_key: str,
    text: str,
    language: str,
) -> dict[str, Any]:
    return {
        "entry_id": e.entry_id,
        "role": role,
        "language": language,
        "text": text,
        "code_points": [f"U+{ord(c):04X}" for c in text],
        "tense": e.tense,
        "mood": e.mood,
        "person": e.person,
        "number": e.number,
        "gender": e.gender,
        "subject": e.subject,
        "subject_latin": e.subject_latin,
        "form_source": e.form_source,
        "sentence_source": e.sentence_source,
        "provider": PROVIDER,
        "voice": HEBREW_VOICE if language == "he" else ITALIAN_VOICE,
        "locale": HEBREW_LOCALE if language == "he" else ITALIAN_LOCALE,
        "rate": HEBREW_RATE if language == "he" else ITALIAN_RATE,
        "pitch": HEBREW_PITCH if language == "he" else ITALIAN_PITCH,
        "format": FORMAT,
        "source_sample_rate": source_sr,
        "output_sample_rate": TARGET_SR,
        "duration": duration,
        "file": str(path),
        "checksum": sha256_hex(audio_bytes),
        "cache_key": cache_key,
    }


def _write_index_html(conjugation: list[dict[str, Any]]) -> None:
    html = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Complete לכתוב Conjugation — Giuseppe & Aaron</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;}",
        ".group{margin:2rem 0;border-top:2px solid #333;padding-top:1rem;}",
        ".card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0;}",
        "audio{width:100%;margin:.3rem 0;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;}",
        "table{border-collapse:collapse;width:100%;font-size:.9rem;}",
        "td,th{border:1px solid #ddd;padding:.3rem .5rem;text-align:left;}",
        "</style></head><body>",
        "<h1>Complete לכתוב Conjugation — Giuseppe & Aaron</h1>",
        "<p><audio controls src='complete_conjugation.wav'></audio> (complete)</p>",
    ]

    groups: dict[str, list[dict[str, Any]]] = {}
    for c in conjugation:
        groups.setdefault(c["tense"], []).append(c)

    group_names = {
        "infinitive": "Infinito",
        "present": "Presente",
        "past": "Passato",
        "future": "Futuro",
        "imperative": "Imperativo",
        "verbal_noun": "Nome verbale",
    }

    for tense in ["infinitive", "present", "past", "future", "imperative", "verbal_noun"]:
        items = groups.get(tense, [])
        if not items:
            continue
        html.append(f"<div class='group'><h2>{group_names.get(tense, tense)}</h2>")
        for c in items:
            html.append("<div class='card'>")
            html.append(f"<h3>{c['entry_id']}</h3>")
            html.append("<table>")
            html.append(f"<tr><th>Italian label</th><td>{c['italian_label']}</td></tr>")
            html.append(f"<tr><th>Tense/mood</th><td>{c['tense']} / {c['mood']}</td></tr>")
            html.append(f"<tr><th>Person</th><td>{c['person'] or '-'}</td></tr>")
            html.append(f"<tr><th>Gender</th><td>{c['gender'] or '-'}</td></tr>")
            html.append(f"<tr><th>Number</th><td>{c['number'] or '-'}</td></tr>")
            html.append(f"<tr><th>Subject</th><td>{c['subject'] or '-'}</td></tr>")
            html.append(f"<tr><th>Canonical form</th><td class='rtl'>{c['form_source']}</td></tr>")
            html.append(f"<tr><th>TTS form</th><td class='rtl'>{c['form_tts']}</td></tr>")
            html.append(
                f"<tr><th>Pointed sentence</th><td class='rtl'>{c['sentence_source']}</td></tr>"
            )
            html.append(f"<tr><th>TTS sentence</th><td class='rtl'>{c['sentence_tts']}</td></tr>")
            html.append(f"<tr><th>Italian translation</th><td>{c['italian_translation']}</td></tr>")
            html.append(f"<tr><th>Expected transliteration</th><td>{c['sentence_latin']}</td></tr>")
            html.append("</table>")
            html.append(
                f"<p>Italian label:</p><audio controls src='audio/italian/{c['entry_id']}.wav'></audio>"
            )
            html.append(
                f"<p>Hebrew sentence:</p><audio controls src='audio/hebrew_sentences/{c['entry_id']}.wav'></audio>"
            )
            form_file = Path(c["files"]["hebrew_form"]).name
            html.append(
                f"<p>Isolated form:</p><audio controls src='audio/hebrew_forms/{form_file}'></audio>"
            )
            html.append("</div>")
        html.append("</div>")

    html.append("</body></html>")
    (OUTPUT_DIR / "index.html").write_text("\n".join(html), encoding="utf-8")


if __name__ == "__main__":
    main()
