#!/usr/bin/env python3
"""Full-niqqud Hannah diagnostic for לְהִתְקַשֵּׁר.

Produces:
  output/mantra_phase1_lehitkasher_hannah_full_niqqud/

Every Hebrew string sent to SpeechGen is fully vocalized with niqqud.
Italian labels use Giuseppe.  No Aaron, no Hila.
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

from mantra.domain.audio_profile import AudioProfile
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

OUTPUT_DIR = Path("output/mantra_phase1_lehitkasher_hannah_full_niqqud")
CACHE_DIR = OUTPUT_DIR / "cache"
TARGET_SR = 22050

HEBREW_VOICE = "Hannah"
HEBREW_LOCALE = "he-IL"
ITALIAN_VOICE = "Giuseppe"
ITALIAN_LOCALE = "it-IT"
PROVIDER = "speechgen"

HEBREW_RATE = 1.0
HEBREW_PITCH = 0.0
ITALIAN_RATE = 1.0
ITALIAN_PITCH = 0.0
FORMAT = "wav"

# Deterministic silence values (seconds), stored in the manifest.
SILENCE_AFTER_LABEL = 0.5
SILENCE_SENTENCE_TO_FORM = 0.85
SILENCE_BETWEEN_ENTRIES = 1.7


@dataclass
class ConjugationEntry:
    entry_id: str
    tense: str
    mood: str
    binyan: str
    root: str
    person: str
    number: str
    gender: str
    subject: str
    subject_latin: str
    form_source: str
    form_tts: str
    sentence_source: str
    sentence_tts: str
    italian_label: str
    italian_translation: str
    human_review_status: str = "pending"


def _has_niqqud(text: str) -> bool:
    return any(c in DIACRITICS for c in normalize_unicode(text))


def _safe_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text).strip("_")[:80]


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


def _resolve_voice_metadata(catalogue: dict[str, Any], voice: str) -> dict[str, Any]:
    for lang, voices in catalogue.items():
        if lang.lower() == "hebrew":
            for v in voices:
                if v.get("voice") == voice:
                    return cast(dict[str, Any], v)
    raise TTSRuntimeError(f"{voice!r} not found in SpeechGen Hebrew catalogue")


def _entries() -> list[ConjugationEntry]:
    entries: list[ConjugationEntry] = []

    def add(**kwargs: Any) -> None:
        entries.append(ConjugationEntry(**kwargs))

    # Infinitive
    add(
        entry_id="infinitive",
        tense="infinitive",
        mood="infinitive",
        binyan="Hitpa'el",
        root="ק-ש-ר",
        person="",
        number="",
        gender="",
        subject="",
        subject_latin="",
        form_source="לְהִתְקַשֵּׁר",
        form_tts="לְהִתְקַשֵּׁר",
        sentence_source="לְהִתְקַשֵּׁר",
        sentence_tts="לְהִתְקַשֵּׁר",
        italian_label="Infinito",
        italian_translation="telefonare / contattare",
    )

    # Present (participial)
    present_forms = [
        ("masculine", "singular", "מִתְקַשֵּׁר", "mitkashér"),
        ("feminine", "singular", "מִתְקַשֶּׁרֶת", "mitkashéret"),
        ("masculine", "plural", "מִתְקַשְּׁרִים", "mitkashrim"),
        ("feminine", "plural", "מִתְקַשְּׁרוֹת", "mitkashrot"),
    ]
    for gender, number, form, _lat in present_forms:
        add(
            entry_id=f"present_{gender}_{number}",
            tense="present",
            mood="participial",
            binyan="Hitpa'el",
            root="ק-ש-ר",
            person="",
            number=number,
            gender=gender,
            subject="",
            subject_latin="",
            form_source=form,
            form_tts=form,
            sentence_source=form,
            sentence_tts=form,
            italian_label=f"Presente, {gender} {number}",
            italian_translation="telefonare / contattare",
        )

    # Past
    past_entries = [
        ("1", None, "singular", "אֲנִי", "ani", "הִתְקַשַּׁרְתִּי", "hitkasharti", "io ho telefonato"),
        ("2", "masculine", "singular", "אַתָּה", "ata", "הִתְקַשַּׁרְתָּ", "hitkasharta", "tu hai telefonato"),
        ("2", "feminine", "singular", "אַתְּ", "at", "הִתְקַשַּׁרְתְּ", "hitkashart", "tu hai telefonato (f.)"),
        ("3", "masculine", "singular", "הוּא", "hu", "הִתְקַשֵּׁר", "hitkasher", "lui ha telefonato"),
        ("3", "feminine", "singular", "הִיא", "hi", "הִתְקַשְּׁרָה", "hitkashra", "lei ha telefonato"),
        (
            "1",
            None,
            "plural",
            "אֲנַחְנוּ",
            "anachnu",
            "הִתְקַשַּׁרְנוּ",
            "hitkasharnu",
            "noi abbiamo telefonato",
        ),
        (
            "2",
            "masculine",
            "plural",
            "אַתֶּם",
            "atem",
            "הִתְקַשַּׁרְתֶּם",
            "hitkashartem",
            "voi avete telefonato",
        ),
        (
            "2",
            "feminine",
            "plural",
            "אַתֶּן",
            "aten",
            "הִתְקַשַּׁרְתֶּן",
            "hitkasharten",
            "voi avete telefonato (f.)",
        ),
        ("3", "masculine", "plural", "הֵם", "hem", "הִתְקַשְּׁרוּ", "hitkashru", "loro hanno telefonato"),
        (
            "3",
            "feminine",
            "plural",
            "הֵן",
            "hen",
            "הִתְקַשְּׁרוּ",
            "hitkashru",
            "loro hanno telefonato (f.)",
        ),
    ]
    for person, past_gender, number, subject, subj_lat, form, _form_lat, it_trans in past_entries:
        sentence = f"{subject} {form}"
        add(
            entry_id=f"past_{person}_{past_gender or 'common'}_{number}",
            tense="past",
            mood="indicative",
            binyan="Hitpa'el",
            root="ק-ש-ר",
            person=person,
            number=number,
            gender=past_gender or "",
            subject=subject,
            subject_latin=subj_lat,
            form_source=form,
            form_tts=form,
            sentence_source=sentence,
            sentence_tts=sentence,
            italian_label=f"Passato, {person}a persona {number}",
            italian_translation=it_trans,
        )

    # Future
    future_entries = [
        ("1", None, "singular", "אֲנִי", "ani", "אֶתְקַשֵּׁר", "etkasher", "io telefonerò"),
        ("2", "masculine", "singular", "אַתָּה", "ata", "תִּתְקַשֵּׁר", "titkasher", "tu telefonerai"),
        ("2", "feminine", "singular", "אַתְּ", "at", "תִּתְקַשְּׁרִי", "titkashri", "tu telefonerai (f.)"),
        ("3", "masculine", "singular", "הוּא", "hu", "יִתְקַשֵּׁר", "yitkaser", "lui telefonerà"),
        ("3", "feminine", "singular", "הִיא", "hi", "תִּתְקַשֵּׁר", "titkasher", "lei telefonerà"),
        ("1", None, "plural", "אֲנַחְנוּ", "anachnu", "נִתְקַשֵּׁר", "nitkasher", "noi telefoneremo"),
        ("2", "masculine", "plural", "אַתֶּם", "atem", "תִּתְקַשְּׁרוּ", "titkashru", "voi telefonerete"),
        ("2", "feminine", "plural", "אַתֶּן", "aten", "תִּתְקַשְּׁרוּ", "titkashru", "voi telefonerete (f.)"),
        ("3", "masculine", "plural", "הֵם", "hem", "יִתְקַשְּׁרוּ", "yitkashru", "loro telefoneranno"),
        ("3", "feminine", "plural", "הֵן", "hen", "יִתְקַשְּׁרוּ", "yitkashru", "loro telefoneranno (f.)"),
    ]
    for (
        person,
        future_gender,
        number,
        subject,
        subj_lat,
        form,
        _form_lat,
        it_trans,
    ) in future_entries:
        sentence = f"{subject} {form}"
        add(
            entry_id=f"future_{person}_{future_gender or 'common'}_{number}",
            tense="future",
            mood="indicative",
            binyan="Hitpa'el",
            root="ק-ש-ר",
            person=person,
            number=number,
            gender=future_gender or "",
            subject=subject,
            subject_latin=subj_lat,
            form_source=form,
            form_tts=form,
            sentence_source=sentence,
            sentence_tts=sentence,
            italian_label=f"Futuro, {person}a persona {number}",
            italian_translation=it_trans,
        )

    # Imperative
    imperative_forms = [
        ("masculine", "singular", "הִתְקַשֵּׁר", "hitkasher"),
        ("feminine", "singular", "הִתְקַשְּׁרִי", "hitkashri"),
        ("masculine", "plural", "הִתְקַשְּׁרוּ", "hitkashru"),
    ]
    for gender, number, form, _lat in imperative_forms:
        add(
            entry_id=f"imperative_{gender}_{number}",
            tense="imperative",
            mood="imperative",
            binyan="Hitpa'el",
            root="ק-ש-ר",
            person="2",
            number=number,
            gender=gender,
            subject="",
            subject_latin="",
            form_source=form,
            form_tts=form,
            sentence_source=form,
            sentence_tts=form,
            italian_label=f"Imperativo, {gender} {number}",
            italian_translation="telefona!",
        )

    return entries


def _validate(entries: list[ConjugationEntry], hannah_meta: dict[str, Any]) -> list[str]:
    report: list[str] = ["# Hannah full-niqqud validation report\n"]
    ok = True

    report.append("## Hannah voice identifier")
    report.append(f"- SpeechGen `voice` field: `{hannah_meta.get('voice')}`")
    report.append(
        f"- type: {hannah_meta.get('type')!r}, sex: {hannah_meta.get('sex')!r}, cpm: {hannah_meta.get('cpm')!r}"
    )
    report.append("")

    report.append("## Full-niqqud validation")
    report.append("| entry_id | voice | sentence | checks |")
    report.append("|---|---|---|---|")

    for e in entries:
        issues: list[str] = []
        if not _has_niqqud(e.form_tts):
            issues.append("form_tts lacks niqqud")
        if not _has_niqqud(e.sentence_tts):
            issues.append("sentence_tts lacks niqqud")
        if e.sentence_source != e.sentence_tts:
            issues.append("source/tts mismatch")
        if HEBREW_VOICE not in (e.sentence_tts + e.form_tts + e.italian_label):
            pass
        if "Hila" in e.sentence_tts or "Aaron" in e.sentence_tts:
            issues.append("wrong voice name in text")
        if issues:
            ok = False
        status = "OK" if not issues else f"FAILED: {', '.join(issues)}"
        report.append(f"| {e.entry_id} | {HEBREW_VOICE} | {e.sentence_tts} | {status} |")

    if not ok:
        report.append("")
        report.append("**Validation failed.** No synthesis performed.")
        raise ValueError("Validation failed; see validation_report.md")

    report.append("")
    report.append("All validation checks passed.")
    return report


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
    voice: str,
) -> dict[str, Any]:
    return {
        "entry_id": e.entry_id,
        "role": role,
        "language": language,
        "text": text,
        "code_points": [f"U+{ord(c):04X}" for c in text],
        "tense": e.tense,
        "mood": e.mood,
        "binyan": e.binyan,
        "root": e.root,
        "person": e.person,
        "number": e.number,
        "gender": e.gender,
        "subject": e.subject,
        "subject_latin": e.subject_latin,
        "form_source": e.form_source,
        "sentence_source": e.sentence_source,
        "provider": PROVIDER,
        "voice": voice,
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
        "<title>לְהִתְקַשֵּׁר — Hannah full-niqqud test</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;}",
        ".group{margin:2rem 0;border-top:2px solid #333;padding-top:1rem;}",
        ".card{border:1px solid #ccc;border-radius:8px;padding:1rem;margin:1rem 0;}",
        "audio{width:100%;margin:.3rem 0;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;}",
        "table{border-collapse:collapse;width:100%;font-size:.9rem;}",
        "td,th{border:1px solid #ddd;padding:.3rem .5rem;text-align:left;}",
        "</style></head><body>",
        "<h1>לְהִתְקַשֵּׁר — Hannah full-niqqud test</h1>",
        f"<p>Hebrew voice: <strong>{HEBREW_VOICE}</strong> | Italian labels: <strong>{ITALIAN_VOICE}</strong></p>",
        "<p><audio controls src='complete_conjugation.wav'></audio> (complete)</p>",
    ]

    group_names = {
        "infinitive": "Infinito",
        "present": "Presente",
        "past": "Passato",
        "future": "Futuro",
        "imperative": "Imperativo",
    }
    section_order = ["infinitive", "present", "past", "future", "imperative"]
    groups: dict[str, list[dict[str, Any]]] = {}
    for c in conjugation:
        groups.setdefault(c["tense"], []).append(c)

    for tense in section_order:
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
            html.append(f"<tr><th>Subject</th><td class='rtl'>{c['subject'] or '-'}</td></tr>")
            html.append(
                f"<tr><th>Canonical / TTS text (same)</th><td class='rtl'>{c['sentence_source']}</td></tr>"
            )
            html.append(
                f"<tr><th>Voice sent to Hannah</th><td>{c.get('hebrew_voice', HEBREW_VOICE)}</td></tr>"
            )
            html.append(f"<tr><th>Human review</th><td>{c['human_review_status']}</td></tr>")
            html.append(f"<tr><th>Italian translation</th><td>{c['italian_translation']}</td></tr>")
            html.append("</table>")
            html.append(
                f"<p>Italian label:</p><audio controls src='audio/italian/{c['entry_id']}.wav'></audio>"
            )
            html.append(
                f"<p>Hebrew sentence/form:</p><audio controls src='audio/hebrew_sentences/{c['entry_id']}.wav'></audio>"
            )
            html.append("</div>")
        html.append("</div>")

    html.append("</body></html>")
    (OUTPUT_DIR / "index.html").write_text("\n".join(html), encoding="utf-8")


def _write_event_log(event_log: list[dict[str, Any]]) -> None:
    path = OUTPUT_DIR / "event_log.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for ev in event_log:
            f.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    profile = AudioProfile.load("hannah")
    he_voice, he_locale = profile.voice_for("he")
    it_voice, it_locale = profile.voice_for("it")

    global HEBREW_VOICE, HEBREW_LOCALE, ITALIAN_VOICE, ITALIAN_LOCALE
    global HEBREW_RATE, HEBREW_PITCH, ITALIAN_RATE, ITALIAN_PITCH, FORMAT, TARGET_SR
    HEBREW_VOICE = he_voice
    HEBREW_LOCALE = he_locale
    ITALIAN_VOICE = it_voice
    ITALIAN_LOCALE = it_locale
    HEBREW_RATE = profile.synthesis_parameters.get("rate", 1.0)
    HEBREW_PITCH = profile.synthesis_parameters.get("pitch", 0.0)
    ITALIAN_RATE = HEBREW_RATE
    ITALIAN_PITCH = HEBREW_PITCH
    FORMAT = profile.output_format
    TARGET_SR = profile.sample_rate

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "audio" / "italian").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "audio" / "hebrew_sentences").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "sections").mkdir(parents=True, exist_ok=True)

    catalogue = _fetch_voice_catalogue(api_key, email)
    hannah_meta = _resolve_voice_metadata(catalogue, HEBREW_VOICE)
    (OUTPUT_DIR / "hannah_metadata.json").write_text(
        json.dumps(hannah_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    event_log: list[dict[str, Any]] = [
        {
            "event": "voice_catalogue_query",
            "hebrew_voice_count": len(catalogue.get("Hebrew", [])),
            "resolved_voice": hannah_meta.get("voice"),
        }
    ]

    entries = _entries()
    validation_report = _validate(entries, hannah_meta)
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

    # Audio-file deduplication keyed by (role, text, voice, locale, rate, pitch).
    audio_files: dict[tuple[str, str, str, str, float, float], Path] = {}

    section_parts: dict[str, list[np.ndarray]] = {
        "infinitive": [],
        "present": [],
        "past": [],
        "future": [],
        "imperative": [],
    }
    section_order = ["infinitive", "present", "past", "future", "imperative"]

    for e in entries:
        # Italian label (Giuseppe)
        label_key = (
            "italian_label",
            e.italian_label,
            ITALIAN_VOICE,
            ITALIAN_LOCALE,
            ITALIAN_RATE,
            ITALIAN_PITCH,
        )
        if label_key in audio_files:
            label_path = audio_files[label_key]
            label_bytes = label_path.read_bytes()
            label_samples, _ = _decode_wav_to_int16(label_bytes)
            label_src_sr = 0
            label_dur = len(label_samples) / TARGET_SR
            label_cache_key = ""
        else:
            label_path = OUTPUT_DIR / "audio" / "italian" / f"{e.entry_id}.wav"
            label_bytes, label_src_sr, label_dur, label_cache_key = _ensure_audio(
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
            audio_files[label_key] = label_path
        manifest.append(
            _manifest_row(
                e,
                "italian_label",
                label_path,
                label_bytes,
                label_src_sr,
                label_dur,
                label_cache_key,
                e.italian_label,
                "it",
                ITALIAN_VOICE,
            )
        )

        # Hebrew sentence/form (Hannah) — source_text == tts_text
        he_text = e.sentence_tts
        he_key = (
            "hebrew_sentence",
            he_text,
            HEBREW_VOICE,
            HEBREW_LOCALE,
            HEBREW_RATE,
            HEBREW_PITCH,
        )
        if he_key in audio_files:
            sentence_path = audio_files[he_key]
            sentence_bytes = sentence_path.read_bytes()
            sentence_samples, _ = _decode_wav_to_int16(sentence_bytes)
            sentence_src_sr = 0
            sentence_dur = len(sentence_samples) / TARGET_SR
            sentence_cache_key = ""
        else:
            sentence_path = OUTPUT_DIR / "audio" / "hebrew_sentences" / f"{e.entry_id}.wav"
            sentence_bytes, sentence_src_sr, sentence_dur, sentence_cache_key = _ensure_audio(
                he_text,
                PROVIDER,
                HEBREW_VOICE,
                HEBREW_LOCALE,
                HEBREW_RATE,
                HEBREW_PITCH,
                FORMAT,
                cache,
                he_provider,
                f"he_{e.entry_id}",
                event_log,
            )
            sentence_path.write_bytes(sentence_bytes)
            audio_files[he_key] = sentence_path
        manifest.append(
            _manifest_row(
                e,
                "hebrew_sentence",
                sentence_path,
                sentence_bytes,
                sentence_src_sr,
                sentence_dur,
                sentence_cache_key,
                he_text,
                "he",
                HEBREW_VOICE,
            )
        )

        # Entry combined audio: label, silence, Hebrew sentence/form, trailing silence.
        label_samples, _ = _decode_wav_to_int16(label_bytes)
        sentence_samples, _ = _decode_wav_to_int16(sentence_bytes)
        entry_audio = np.concatenate(
            [
                label_samples,
                _silence(SILENCE_AFTER_LABEL),
                sentence_samples,
                _silence(SILENCE_BETWEEN_ENTRIES),
            ]
        )
        section_parts[e.tense].append(entry_audio)

        conjugation.append(
            {
                "entry_id": e.entry_id,
                "tense": e.tense,
                "mood": e.mood,
                "binyan": e.binyan,
                "root": e.root,
                "person": e.person,
                "number": e.number,
                "gender": e.gender,
                "subject": e.subject,
                "subject_latin": e.subject_latin,
                "form_source": e.form_source,
                "form_tts": e.form_tts,
                "sentence_source": e.sentence_source,
                "sentence_tts": e.sentence_tts,
                "italian_label": e.italian_label,
                "italian_translation": e.italian_translation,
                "hebrew_voice": HEBREW_VOICE,
                "human_review_status": e.human_review_status,
                "files": {
                    "italian_label": str(label_path),
                    "hebrew_sentence": str(sentence_path),
                },
            }
        )

    # Silence constants manifest entry.
    manifest.append(
        {
            "name": "silence_constants",
            "role": "constants",
            "after_label_ms": int(SILENCE_AFTER_LABEL * 1000),
            "sentence_to_form_ms": int(SILENCE_SENTENCE_TO_FORM * 1000),
            "between_entries_ms": int(SILENCE_BETWEEN_ENTRIES * 1000),
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
        if len(complete_parts) > 1 and np.max(np.abs(complete_parts[-1])) == 0:
            complete_parts = complete_parts[:-1]
        complete_audio = np.concatenate(complete_parts)
        complete_path = OUTPUT_DIR / "complete_conjugation.wav"
        complete_path.write_bytes(_encode_int16_to_wav(complete_audio, TARGET_SR))
        manifest.append(
            {
                "name": "complete_conjugation",
                "file": str(complete_path),
                "text": "complete לְהִתְקַשֵּׁר conjugation",
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


if __name__ == "__main__":
    main()
