#!/usr/bin/env python3
"""Read-only HeLP projections for the Hebrew domain.

The HeLP Lexicon Project norms and the personal HeLP Profiler are deliberately
separate. Norms describe stimuli and aggregate experimental performance; the
profiler describes only observations produced by MindTune Lab.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sqlite3
import statistics
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROFILE_SCHEMA_VERSION = "help-profiler-profile/1.1.0"
PROFILER_MODEL_VERSION = "h1-root-binyan-input-mode/0.2.1"
NORMS_DATASET_ID = "help-lexicon-norms"
NORMS_RELEASE_ID = "stein-frost-siegelman-2024-local-ingest-v1"
MIN_OBSERVATIONS = 8
MIN_SESSIONS = 2
MIN_ITEMS = 2
HEBREW_MARKS_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
HEBREW_LETTER_RE = re.compile(r"[\u05d0-\u05ea]")


def normalize_hebrew(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    return "".join(HEBREW_MARKS_RE.sub("", text).split())


def normalize_hebrew_root(value: Any) -> str:
    """Return only the Hebrew consonants of a root in canonical compact form."""
    text = HEBREW_MARKS_RE.sub("", unicodedata.normalize("NFC", str(value or "")))
    return "".join(HEBREW_LETTER_RE.findall(text))


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _int(value: Any) -> int | None:
    number = _float(value)
    return int(number) if number is not None else None


def _round(value: float | None, digits: int = 3) -> float | None:
    return None if value is None else round(value, digits)


def _median(values: Iterable[float | None]) -> float | None:
    usable = [value for value in values if value is not None and math.isfinite(value)]
    return statistics.median(usable) if usable else None


def _seconds_to_ms(value: Any) -> float | None:
    seconds = _float(value)
    return seconds * 1000 if seconds is not None and seconds > 0 else None


def _mean(values: Iterable[float | None]) -> float | None:
    usable = [value for value in values if value is not None and math.isfinite(value)]
    return statistics.fmean(usable) if usable else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error, UnicodeError):
        return []


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError:
        return ""
    return digest.hexdigest()


class HeLPNorms:
    """Exact-form index over the processed HeLP lexical norm tables."""

    def __init__(self, lexical_metrics: Path, ld_summary: Path, naming_summary: Path):
        self.lexical_metrics_path = lexical_metrics
        self.ld_summary_path = ld_summary
        self.naming_summary_path = naming_summary
        self.lexical: dict[str, dict[str, Any]] = {}
        self.ld: dict[str, dict[str, Any]] = {}
        self.naming: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        for row in _read_csv(self.lexical_metrics_path):
            key = normalize_hebrew(row.get("word"))
            if not key:
                continue
            self.lexical[key] = {
                "word": row.get("word") or "",
                "lexicality": row.get("lexicality") or "word",
                "frequency": _float(row.get("frequency")),
                "word_length": _int(row.get("word_length")),
                "orthographic_neighborhood_density": _float(
                    row.get("orthographic_neighborhood_density")
                ),
                "phonological_entropy": _float(row.get("phonological_entropy")),
                "clitic_count": _float(row.get("clitic_count")),
                "semitic_structure": _float(row.get("semitic_structure")),
            }
        for row in _read_csv(self.ld_summary_path):
            if str(row.get("stimulus_type") or "").lower() == "nonword":
                continue
            key = normalize_hebrew(row.get("word_key") or row.get("word"))
            if key:
                self.ld[key] = {
                    "trials": _int(row.get("ld_trials")),
                    "median_rt_ms": _float(row.get("ld_median_rt")),
                    "mean_rt_ms": _float(row.get("ld_mean_rt")),
                    "sd_rt_ms": _float(row.get("ld_sd_rt")),
                    "accuracy": _float(row.get("ld_accuracy")),
                }
        for row in _read_csv(self.naming_summary_path):
            key = normalize_hebrew(row.get("word_key") or row.get("word"))
            if key:
                self.naming[key] = {
                    "trials": _int(row.get("naming_trials")),
                    "valid_trials": _int(row.get("naming_valid_trials")),
                    "median_rt_ms": _float(row.get("naming_median_rt")),
                    "mean_rt_ms": _float(row.get("naming_mean_rt")),
                    "sd_rt_ms": _float(row.get("naming_sd_rt")),
                    "accuracy": _float(row.get("naming_accuracy")),
                }

    @property
    def reference(self) -> dict[str, Any]:
        paths = (self.lexical_metrics_path, self.ld_summary_path, self.naming_summary_path)
        composite = hashlib.sha256()
        file_hashes = {}
        for path in paths:
            digest = _file_sha256(path)
            file_hashes[path.name] = digest
            composite.update(f"{path.name}:{digest}\n".encode())
        return {
            "dataset_id": NORMS_DATASET_ID,
            "release_id": NORMS_RELEASE_ID,
            "citation": "Stein, Frost & Siegelman (2024), Behavior Research Methods, DOI 10.3758/s13428-024-02502-4",
            "sha256": composite.hexdigest(),
            "files": file_hashes,
            "lexical_items": len(self.lexical),
            "lexical_decision_items": len(self.ld),
            "naming_items": len(self.naming),
        }

    def item(self, hebrew: Any) -> dict[str, Any]:
        key = normalize_hebrew(hebrew)
        lexical = self.lexical.get(key)
        ld = self.ld.get(key)
        naming = self.naming.get(key)
        return {
            "matched": bool(lexical or ld or naming),
            "match_type": "exact_normalized_form" if lexical or ld or naming else "none",
            "word_key": key,
            "lexical": lexical,
            "lexical_decision_norms": ld,
            "naming_norms": naming,
            "interpretation": (
                "Norme aggregate dello stimolo; non sono una misura della competenza personale e non sono confrontabili direttamente con il tempo di richiamo di una flashcard."
                if lexical or ld or naming
                else "Forma non rappresentata nel dataset HeLP; questo non implica che sia errata o rara."
            ),
        }


def _observation_status(count: int, sessions: int, items: int) -> str:
    if count >= MIN_OBSERVATIONS and sessions >= MIN_SESSIONS and items >= MIN_ITEMS:
        return "preliminary"
    return "insufficient_data"


def _observation(
    *,
    source: str,
    source_ref: str,
    session_ref: str,
    item_ref: str,
    word: str,
    outcome: str,
    latency_ms: float | None,
    root: str = "",
    binyan: str = "",
    timestamp: str = "",
    input_mode: str = "",
    transcription_provider: str = "",
    transcription_confidence: float | None = None,
    speech_duration_ms: float | None = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "source_ref": source_ref,
        "session_ref": session_ref or "unknown-session",
        "item_ref": item_ref or normalize_hebrew(word) or "unknown-item",
        "word": word,
        "word_key": normalize_hebrew(word),
        "root": normalize_hebrew_root(root),
        "binyan": str(binyan or "").strip(),
        "outcome": outcome,
        "correct": outcome == "correct",
        "latency_ms": latency_ms,
        "timestamp": timestamp,
        "input_mode": str(input_mode or "unspecified"),
        "transcription_provider": str(transcription_provider or ""),
        "transcription_confidence": transcription_confidence,
        "speech_duration_ms": speech_duration_ms,
    }


def flashcard_observations(memory: dict[str, Any]) -> list[dict[str, Any]]:
    items = {
        str(item.get("id") or ""): item
        for item in memory.get("items", [])
        if isinstance(item, dict)
    }
    events = [event for event in memory.get("events", []) if isinstance(event, dict)]
    if not events:
        events = [
            event
            for item in items.values()
            for event in item.get("events", [])
            if isinstance(event, dict)
        ]
    result = []
    seen: set[tuple[Any, ...]] = set()
    for index, event in enumerate(events, 1):
        item = items.get(str(event.get("item_id") or ""), {})
        outcome = {"correct": "correct", "partial": "partial", "miss": "incorrect"}.get(
            str(event.get("result") or "")
        )
        if not outcome:
            continue
        timestamp = str(event.get("label") or event.get("at") or "")
        session_ref = str(
            (event.get("eeg_annotation") or {}).get("jsonl")
            or str(event.get("label") or "")[:10]
            or "flashcard-local"
        )
        key = (event.get("item_id"), event.get("at"), event.get("result"), event.get("latency_s"))
        if key in seen:
            continue
        seen.add(key)
        result.append(
            _observation(
                source="flashcard_recall",
                source_ref=f"{event.get('item_id') or 'unknown'}:{event.get('at') or timestamp}:{index}",
                session_ref=session_ref,
                item_ref=str(item.get("canonical_item_id") or event.get("item_id") or ""),
                word=str(
                    event.get("front")
                    or item.get("raw_front")
                    or item.get("term")
                    or event.get("term")
                    or ""
                ),
                outcome=outcome,
                latency_ms=_seconds_to_ms(event.get("latency_s")),
                timestamp=timestamp,
            )
        )
    return result


def conjugation_observations(*session_dirs: Path | None) -> list[dict[str, Any]]:
    result = []
    seen: set[str] = set()
    paths: list[Path] = []
    for sessions_dir in session_dirs:
        if sessions_dir is not None and sessions_dir.exists():
            paths.extend(sessions_dir.glob("*.events.jsonl"))
    for path in sorted(set(paths)):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, 1):
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            if row.get("type") != "conjugation_response":
                continue
            event = row.get("event") if isinstance(row.get("event"), dict) else {}
            source_ref = str(
                row.get("behavioral_event_id") or event.get("event_id") or f"{path.name}:{index}"
            )
            if source_ref in seen:
                continue
            seen.add(source_ref)
            expected = str(event.get("expected_phrase") or event.get("expected") or "")
            speech = (
                event.get("speech_recognition")
                if isinstance(event.get("speech_recognition"), dict)
                else {}
            )
            result.append(
                _observation(
                    source="conjugation_response",
                    source_ref=source_ref,
                    session_ref=str(row.get("behavioral_session_id") or path.stem),
                    item_ref=str(event.get("verb_id") or normalize_hebrew(expected)),
                    word=expected.split("|")[0],
                    outcome="correct" if event.get("ok") is True else "incorrect",
                    latency_ms=_float(event.get("reaction_time_ms")),
                    root=str(event.get("root") or ""),
                    binyan=str(event.get("binyan") or ""),
                    timestamp=str(event.get("timestamp") or row.get("recorded_at") or ""),
                    input_mode=str(event.get("input_mode") or "keyboard"),
                    transcription_provider=str(speech.get("provider") or ""),
                    transcription_confidence=_float(speech.get("recognition_confidence")),
                    speech_duration_ms=_float(speech.get("duration_ms")),
                )
            )
    return result


def recovery_observations(*session_dirs: Path | None) -> list[dict[str, Any]]:
    """Project lexical recovery events without treating warm-up or summaries as language evidence."""
    accepted_types = {
        "hebrew_recovery_lexical_response",
        "hebrew_recovery_comprehension_response",
        "hebrew_recovery_reentry_response",
    }
    result = []
    seen: set[str] = set()
    paths: list[Path] = []
    for sessions_dir in session_dirs:
        if sessions_dir is not None and sessions_dir.exists():
            paths.extend(sessions_dir.glob("*.events.jsonl"))
    for path in sorted(set(paths)):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, 1):
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            event_type = str(row.get("type") or "")
            if event_type not in accepted_types:
                continue
            event = row.get("event") if isinstance(row.get("event"), dict) else {}
            source_ref = str(
                row.get("behavioral_event_id") or event.get("event_id") or f"{path.name}:{index}"
            )
            if source_ref in seen:
                continue
            seen.add(source_ref)
            word = str(
                event.get("infinitive") or event.get("phrase") or event.get("expected") or ""
            )
            result.append(
                _observation(
                    source=event_type,
                    source_ref=source_ref,
                    session_ref=str(row.get("behavioral_session_id") or path.stem),
                    item_ref=str(event.get("verb_id") or normalize_hebrew(word)),
                    word=word,
                    outcome="correct" if event.get("correct") is True else "incorrect",
                    latency_ms=_float(event.get("reaction_time_ms")),
                    root=str(event.get("root") or ""),
                    binyan=str(event.get("binyan") or ""),
                    timestamp=str(event.get("timestamp") or row.get("recorded_at") or ""),
                    input_mode="keyboard_or_choice",
                )
            )
    return result


def shoresh_observations(sessions_dir: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted(sessions_dir.glob("*.csv")) if sessions_dir.exists() else []:
        for index, row in enumerate(_read_csv(path), 1):
            correct_value = str(row.get("is_correct") or row.get("correct") or "").strip().lower()
            if correct_value not in {"true", "false", "1", "0"}:
                continue
            word = str(row.get("stimulus") or row.get("word") or row.get("target") or "")
            result.append(
                _observation(
                    source="shoresh_response",
                    source_ref=f"{path.name}:{index}",
                    session_ref=path.stem,
                    item_ref=str(row.get("item_id") or row.get("root") or word),
                    word=word,
                    outcome="correct" if correct_value in {"true", "1"} else "incorrect",
                    latency_ms=_float(row.get("reaction_time_ms") or row.get("rt_ms")),
                    root=str(row.get("root") or row.get("correct_answer") or ""),
                    timestamp=str(row.get("timestamp") or row.get("answered_at") or ""),
                )
            )
    return result


def mlf_observations(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        rows = connection.execute(
            "SELECT event_id, event_type, timestamp, monotonic_ns, session_id, unit_id, payload_json FROM events ORDER BY monotonic_ns, timestamp, event_id"
        ).fetchall()
    except (sqlite3.Error, OSError):
        return []
    finally:
        try:
            connection.close()
        except (UnboundLocalError, sqlite3.Error):
            pass
    starts: dict[str, dict[str, Any]] = {}
    responses: dict[str, dict[str, Any]] = {}
    score_events: dict[str, list[tuple[str, str, str, str, dict[str, Any]]]] = defaultdict(list)
    for event_id, event_type, timestamp, _order, session_id, unit_id, raw_payload in rows:
        try:
            payload = json.loads(raw_payload)
        except (json.JSONDecodeError, TypeError):
            continue
        trial_id = str(payload.get("trial_id") or "")
        if not trial_id:
            continue
        if event_type == "trial.start":
            starts[trial_id] = {
                "payload": payload,
                "unit_id": unit_id,
                "session_id": session_id,
                "timestamp": timestamp,
            }
        elif event_type == "trial.response":
            responses[trial_id] = payload
        elif event_type == "trial.score":
            score_events[trial_id].append((event_id, timestamp, session_id, unit_id, payload))
    scores: dict[str, tuple[str, str, str, str, dict[str, Any]]] = {}
    for trial_id, candidates in score_events.items():
        terminal = None
        previous_id = None
        expected_sequence = 0
        for candidate in candidates:
            event_id, _timestamp, _session_id, _unit_id, payload = candidate
            review_status = str(
                (payload.get("score_metadata") or {}).get("human_review_status")
                or "machine_confirmed"
            )
            correction_of = payload.get("correction_of_event_id")
            sequence = payload.get("correction_sequence")
            is_initial = previous_id is None and correction_of is None and sequence in {None, 0}
            is_correction = (
                previous_id is not None
                and correction_of == previous_id
                and sequence in {None, expected_sequence}
            )
            if not (is_initial or is_correction):
                continue
            previous_id = event_id
            expected_sequence += 1
            if review_status not in {"pending", "rejected"}:
                terminal = candidate
        if terminal is not None:
            scores[trial_id] = terminal
    result = []
    for trial_id, (event_id, timestamp, session_id, unit_id, score) in scores.items():
        outcome = str(score.get("outcome") or "")
        if outcome not in {"correct", "partial", "incorrect", "no_response"}:
            continue
        response = responses.get(trial_id, {})
        start = starts.get(trial_id, {})
        metadata = (
            score.get("score_metadata") if isinstance(score.get("score_metadata"), dict) else {}
        )
        hebrew = metadata.get("hebrew") if isinstance(metadata.get("hebrew"), dict) else {}
        word = str(response.get("response_normalized") or response.get("response_raw") or "")
        result.append(
            _observation(
                source="mlf_trial_score",
                source_ref=event_id,
                session_ref=session_id,
                item_ref=str(score.get("knowledge_item_id") or unit_id or trial_id),
                word=word,
                outcome="incorrect" if outcome == "no_response" else outcome,
                latency_ms=_float(score.get("latency_ms")),
                root=str(hebrew.get("root") or ""),
                binyan=str(hebrew.get("binyan") or ""),
                timestamp=timestamp or str(start.get("timestamp") or ""),
            )
        )
    return result


def _summaries(observations: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        value = str(observation.get(field) or "").strip()
        if value:
            groups[value].append(observation)
    summaries = []
    for value, rows in groups.items():
        sessions = {row["session_ref"] for row in rows}
        items = {row["item_ref"] for row in rows}
        correct = sum(row["outcome"] == "correct" for row in rows)
        summaries.append(
            {
                field: value,
                "eligible_observation_count": len(rows),
                "distinct_session_count": len(sessions),
                "distinct_item_count": len(items),
                "correct_count": correct,
                "success_ratio": _round(correct / len(rows) if rows else None),
                "median_latency_ms": _round(_median(row.get("latency_ms") for row in rows), 1),
                "evidence_status": _observation_status(len(rows), len(sessions), len(items)),
            }
        )
    return sorted(
        summaries, key=lambda item: (-item["eligible_observation_count"], str(item[field]))
    )


def _session_summaries(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        groups[str(observation.get("session_ref") or "unknown-session")].append(observation)
    summaries = []
    for session_ref, rows in groups.items():
        correct = sum(row["outcome"] == "correct" for row in rows)
        partial = sum(row["outcome"] == "partial" for row in rows)
        timestamps = sorted(str(row.get("timestamp") or "") for row in rows if row.get("timestamp"))
        sources = sorted({str(row.get("source") or "") for row in rows if row.get("source")})
        summaries.append(
            {
                "session_ref": session_ref,
                "last_observation_at": timestamps[-1] if timestamps else "",
                "eligible_observation_count": len(rows),
                "distinct_item_count": len({row["item_ref"] for row in rows}),
                "correct_count": correct,
                "partial_count": partial,
                "success_ratio": _round(correct / len(rows) if rows else None),
                "median_latency_ms": _round(_median(row.get("latency_ms") for row in rows), 1),
                "sources": sources,
            }
        )
    return sorted(
        summaries, key=lambda item: (item["last_observation_at"], item["session_ref"]), reverse=True
    )[:24]


def _input_mode_summaries(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        groups[str(observation.get("input_mode") or "unspecified")].append(observation)
    summaries = []
    for input_mode, rows in groups.items():
        correct = sum(row["outcome"] == "correct" for row in rows)
        summaries.append(
            {
                "input_mode": input_mode,
                "eligible_observation_count": len(rows),
                "distinct_session_count": len({row["session_ref"] for row in rows}),
                "success_ratio": _round(correct / len(rows) if rows else None),
                "median_latency_ms": _round(_median(row.get("latency_ms") for row in rows), 1),
                "median_transcription_confidence": _round(
                    _median(row.get("transcription_confidence") for row in rows)
                ),
                "median_speech_duration_ms": _round(
                    _median(row.get("speech_duration_ms") for row in rows), 1
                ),
                "transcription_providers": sorted(
                    {
                        str(row.get("transcription_provider"))
                        for row in rows
                        if row.get("transcription_provider")
                    }
                ),
            }
        )
    return sorted(
        summaries, key=lambda item: (-item["eligible_observation_count"], item["input_mode"])
    )


def _adaptive_candidates(
    memory: dict[str, Any], profile_status: str, norms: HeLPNorms
) -> list[dict[str, Any]]:
    if profile_status != "preliminary":
        return []
    now = time.time()
    frequency_values = []
    for item in memory.get("items", []):
        if not isinstance(item, dict):
            continue
        lexical = norms.item(item.get("raw_front") or item.get("term")).get("lexical") or {}
        frequency = _float(lexical.get("frequency"))
        if frequency is not None and frequency >= 0:
            frequency_values.append(math.log1p(frequency))
    max_log_frequency = max(frequency_values, default=0.0)
    candidates = []
    for item in memory.get("items", []):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        events = [event for event in item.get("events", []) if isinstance(event, dict)]
        misses = sum(event.get("result") == "miss" for event in events[-8:])
        partial = sum(event.get("result") == "partial" for event in events[-8:])
        due = float(item.get("next_due_at") or 0) <= now
        if not events:
            continue
        item_norms = norms.item(item.get("raw_front") or item.get("term"))
        frequency = _float((item_norms.get("lexical") or {}).get("frequency"))
        frequency_bonus = (
            math.log1p(max(0.0, frequency)) / max_log_frequency
            if frequency is not None and max_log_frequency > 0
            else 0.0
        )
        personal_priority = misses * 3 + partial * 1.5 + (1 if due else 0)
        priority = personal_priority + frequency_bonus
        if priority <= 0:
            continue
        reasons = ["personal_recall_history"]
        if frequency_bonus >= 0.6:
            reasons.append("high_frequency_norm")
        candidates.append(
            {
                "item_id": str(item.get("id")),
                "canonical_item_id": str(item.get("canonical_item_id") or ""),
                "priority": round(priority, 2),
                "priority_components": {
                    "personal_recall": round(personal_priority, 2),
                    "help_frequency": round(frequency_bonus, 3),
                },
                "reasons": reasons,
                "lexical_norms_matched": bool(item_norms.get("matched")),
            }
        )
    return sorted(candidates, key=lambda item: (-item["priority"], item["item_id"]))[:30]


def _recovery_candidates(
    observations: list[dict[str, Any]], profile_status: str
) -> list[dict[str, Any]]:
    if profile_status != "preliminary":
        return []
    recovery_rows = [
        row for row in observations if str(row.get("source") or "").startswith("hebrew_recovery_")
    ]
    overall_latency = _median(row.get("latency_ms") for row in recovery_rows) or 0.0
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in recovery_rows:
        grouped[str(row.get("item_ref") or "")].append(row)
    candidates = []
    for item_id, rows in grouped.items():
        if not item_id:
            continue
        misses = sum(not row.get("correct") for row in rows)
        median_latency = _median(row.get("latency_ms") for row in rows) or 0.0
        slow_bonus = 1.0 if overall_latency > 0 and median_latency > overall_latency else 0.0
        priority = misses * 3.0 + slow_bonus
        if priority <= 0:
            continue
        candidates.append(
            {
                "item_id": item_id,
                "canonical_item_id": "",
                "priority": round(priority, 2),
                "priority_components": {
                    "personal_recovery_errors": misses * 3.0,
                    "slow_retrieval": slow_bonus,
                },
                "reasons": [
                    reason
                    for reason, enabled in (
                        ("personal_recovery_error", misses > 0),
                        ("slow_retrieval", slow_bonus > 0),
                    )
                    if enabled
                ],
                "lexical_norms_matched": False,
            }
        )
    return sorted(candidates, key=lambda item: (-item["priority"], item["item_id"]))[:30]


def build_profile(
    *,
    norms: HeLPNorms,
    memory: dict[str, Any],
    eeg_sessions_dir: Path,
    shoresh_sessions_dir: Path,
    mlf_db_path: Path,
    learner_id: str,
    behavioral_events_dir: Path | None = None,
) -> dict[str, Any]:
    observations = (
        flashcard_observations(memory)
        + conjugation_observations(eeg_sessions_dir, behavioral_events_dir)
        + recovery_observations(eeg_sessions_dir, behavioral_events_dir)
        + shoresh_observations(shoresh_sessions_dir)
        + mlf_observations(mlf_db_path)
    )
    deduped = []
    seen = set()
    for row in observations:
        key = (row["source"], row["source_ref"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    observations = deduped
    sessions = {row["session_ref"] for row in observations}
    items = {row["item_ref"] for row in observations}
    correct = sum(row["outcome"] == "correct" for row in observations)
    partial = sum(row["outcome"] == "partial" for row in observations)
    status = _observation_status(len(observations), len(sessions), len(items))
    active_items = [item for item in memory.get("items", []) if isinstance(item, dict)]
    matched_active = sum(
        norms.item(item.get("raw_front") or item.get("term"))["matched"] for item in active_items
    )
    source_counts: dict[str, int] = defaultdict(int)
    for row in observations:
        source_counts[row["source"]] += 1
    return {
        "projection_schema_version": PROFILE_SCHEMA_VERSION,
        "profiler_id": "help_profiler",
        "profiler_model_version": PROFILER_MODEL_VERSION,
        "learner_id": learner_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "event_source_policy": "read_only_projection_from_behavioral_events",
        "lexical_norms_ref": norms.reference,
        "evidence": {
            "status": status,
            "eligible_observation_count": len(observations),
            "distinct_session_count": len(sessions),
            "distinct_item_count": len(items),
            "minimum_policy": {
                "observations": MIN_OBSERVATIONS,
                "sessions": MIN_SESSIONS,
                "items": MIN_ITEMS,
            },
            "source_counts": dict(sorted(source_counts.items())),
        },
        "performance": {
            "correct_count": correct,
            "partial_count": partial,
            "incorrect_count": len(observations) - correct - partial,
            "success_ratio": _round(correct / len(observations) if observations else None),
            "median_latency_ms": _round(_median(row.get("latency_ms") for row in observations), 1),
        },
        "coverage": {
            "lexical_archive_items": len(active_items),
            "lexical_archive_exact_help_match": matched_active,
            "lexical_archive_exact_help_match_ratio": _round(
                matched_active / len(active_items) if active_items else None
            ),
            # Historical aliases retained for stored profile consumers.
            "active_flashcards": len(active_items),
            "active_flashcards_exact_help_match": matched_active,
            "active_flashcards_exact_help_match_ratio": _round(
                matched_active / len(active_items) if active_items else None
            ),
        },
        "root_summaries": _summaries(observations, "root"),
        "binyan_summaries": _summaries(observations, "binyan"),
        "input_mode_summaries": _input_mode_summaries(observations),
        "session_summaries": _session_summaries(observations),
        "adaptive_candidates": sorted(
            _adaptive_candidates(memory, status, norms)
            + _recovery_candidates(observations, status),
            key=lambda item: (-item["priority"], item["item_id"]),
        )[:30],
        "notes": [
            "HeLP norms characterize lexical stimuli; they do not measure personal competence.",
            "Root/binyan summaries are preliminary hypotheses and must be validated against an item-only baseline before they influence scheduling.",
            "A missing exact HeLP match means only that the form is absent from this dataset.",
            "Conjugation observations are durable with or without EEG; EEG remains contextual evidence and never overrides performance.",
            "Speech recognition confidence measures transcription reliability, not Hebrew pronunciation quality.",
            "Fine-grained error categories are withheld until domain tasks emit reviewed error tags.",
            "Legacy flashcard observations remain archival evidence only and do not drive the active recovery curriculum.",
            "Recovery candidates are derived from immutable error and latency events; they do not alter linguistic truth or curriculum levels.",
        ],
    }
