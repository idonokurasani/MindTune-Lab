#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import csv
import queue
import re
import shlex
import signal
import subprocess
import sys
import tarfile
import threading
import time
import unicodedata
import mimetypes
import statistics
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from uuid import UUID, NAMESPACE_DNS, uuid5

import oura_api
import help_profiler
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(os.environ.get("MINDTUNE_ROOT", Path(__file__).resolve().parents[1])).resolve()
APP = Path(os.environ.get("MINDTUNE_CONSOLE_APP", Path(__file__).resolve().parent)).resolve()
ENGINE_ROOT = Path(os.environ.get("MINDTUNE_ENGINE_ROOT", APP.parents[0])).resolve()
MLF_REPO = Path(os.environ.get("MINDTUNE_MLF_REPO", ROOT / "mindtune-learning-framework")).resolve()
if MLF_REPO.exists() and str(MLF_REPO) not in sys.path:
    sys.path.insert(0, str(MLF_REPO))
BRIDGE = ROOT / ".raspberry_bridge"
INBOX = BRIDGE / "inbox"
RUNNING = BRIDGE / "running"
DONE = BRIDGE / "done"
FAILED = BRIDGE / "failed"
LOGS = BRIDGE / "logs"
MAC_CAPTURE = Path(os.environ.get("MINDTUNE_MAC_CAPTURE", ROOT / "mindtune_capture")).resolve()
MAC_RECORDER = Path(os.environ.get("MINDTUNE_MAC_RECORDER", MAC_CAPTURE / "fc11_mac_capture.py")).resolve()
MAC_VENV_PY = Path(os.environ.get("MINDTUNE_MAC_PYTHON", MAC_CAPTURE / ".venv" / "bin" / "python")).absolute()
MAC_LOGS = MAC_CAPTURE / "logs"
MAC_SESSIONS = MAC_CAPTURE / "sessions"
MINDTUNE_SESSIONS = MAC_CAPTURE / "mindtune_sessions"
BEHAVIORAL_EVENTS = MINDTUNE_SESSIONS / "behavioral"
MAC_RUNTIME = MAC_CAPTURE / "runtime"
MAC_EXPORTS = MAC_CAPTURE / "exports"
MAC_PYTHONPATH = os.environ.get("MINDTUNE_MAC_PYTHONPATH", "")
LEGACY_MAC_CAPTURE = ROOT / ("focus" + "calm_mac_capture")
MAC_STATE = MAC_RUNTIME / "current_recording.json"
MAC_STATUS_FILE = MAC_RUNTIME / "current_recording_status.json"
MAC_BATTERY_FILE = MAC_RUNTIME / "battery.json"
MAC_START_SIGNAL = MAC_RUNTIME / "start_recording.signal"
MAC_STOP_SIGNAL = MAC_RUNTIME / "stop_recording.signal"
MAC_COMMAND_SIGNAL = MAC_RUNTIME / "command.signal"
MEMORY_FILE = MAC_CAPTURE / "memory_protocol.json"
HEBREW_VERB_CATALOG_FILE = APP / "data" / "hebrew_verbs_conjugated.json"
PEALIM_VERB_CATALOG_FILE = APP / "data" / "pealim_hebrew_verbs.json"
HELP_PROCESSED_DIR = Path(
    os.environ.get(
        "MINDTUNE_HELP_PROCESSED_DIR",
        ENGINE_ROOT / "mindtune_lab" / "tasks" / "shoresh_lab" / "data" / "help_processed",
    )
).resolve()
HELP_LEXICAL_METRICS_FILE = HELP_PROCESSED_DIR / "help_lexical_metrics.csv"
HELP_LD_SUMMARY_FILE = HELP_PROCESSED_DIR / "help_ld_summary.csv"
HELP_NAMING_SUMMARY_FILE = HELP_PROCESSED_DIR / "help_naming_summary.csv"
FLASHCARD_CATALOG_PATCH_FILE = MAC_CAPTURE / "flashcard_catalog_patches.json"
HEBREW_SOURCE_REGISTRY_FILE = APP / "data" / "hebrew_resources" / "source_registry.json"
HEBREW_WORDNET_DIR = APP / "data" / "hebrew_resources" / "vendor" / "HebrewWordnetShuly"
HEBREW_WORDNET_INDEX_FILE = APP / "data" / "hebrew_resources" / "derived" / "hebrew_wordnet_compact.json"
NNLP_VERB_INDEX_FILE = APP / "data" / "hebrew_resources" / "derived" / "nnlp_verb_index.json"
SHORESH_TASK = Path(os.environ.get("MINDTUNE_SHORESH_TASK", ENGINE_ROOT / "mindtune_lab" / "tasks" / "shoresh_lab")).resolve()
SHORESH_DATA_TASK = Path(os.environ.get("MINDTUNE_SHORESH_DATA_TASK", ROOT / "mindtune_lab" / "tasks" / "shoresh_lab")).resolve()
SHORESH_ITEMS_FILE = SHORESH_TASK / "stimuli" / "shoresh_items_v1.json"
SHORESH_SESSIONS = SHORESH_DATA_TASK / "data" / "sessions"
SHORESH_EXPORTS = SHORESH_DATA_TASK / "data" / "exports"
DEFAULT_RPI_HOST = "idonokurasani@raspberry-pi-andrea.local"
REMOTE_EXPORT_BASE = "/mnt/biohacking/home/mindtune/macbook_exports"
APP_VERSION = "3.22.0"
APP_BUILD = os.environ.get("MINDTUNE_APP_BUILD", "dev")
SERIOUS_DATA_START_TS = float(os.environ.get("MINDTUNE_SERIOUS_DATA_START_TS", "1782742800"))
ACTIVE_PHASES = {"scan", "connecting", "ble_link", "handshake_sent", "connected", "starting", "prep", "recording"}
TERMINAL_PHASES = {"done", "error", "interrupted"}
ACTIVE_STATUS_MAX_AGE_S = 12

MAX_BODY = 32_768
MAX_LOG_BYTES = 80_000
CONDITION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
PIECE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
HEBREW_MARKS_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
FLASHCARD_SOURCES = {
    "verified_tabular",
    "pdf_extracted_raw",
    "quizlet_export_raw",
}


_MLF_AVAILABLE = False
_MLF_IMPORT_ERROR = ""
try:
    from mlf.core import BrainLab, Response, Student
    from mlf.core import M0Scheduler, M0Transformation
    from mlf.infrastructure import RetestQueue, SQLiteEventStore
    from mlf.labs.hebrew import HebrewDomainAdapter, HebrewScorer, HEBREW_UNITS
    from mlf.labs.hebrew.corpus import (
        STATUS_DRAFT,
        STATUS_HUMAN_LINGUISTIC_APPROVED,
        STATUS_HUMAN_PEDAGOGICAL_APPROVED,
    )
    from mlf.runner_domains import get_domain_adapter_and_scorer

    _MLF_AVAILABLE = True
except Exception as exc:
    _MLF_IMPORT_ERROR = str(exc)
    _MLF_AVAILABLE = False


MLF_CAPTURE_ROOT = Path(os.environ.get("MINDTUNE_CAPTURE_ROOT", MAC_CAPTURE)).resolve()
HEBREW_MLF_DB_PATH = MLF_CAPTURE_ROOT / "mlf" / "hebrew_b2_7.sqlite"
HEBREW_MLF_DEFAULT_STUDENT = os.environ.get("MINDTUNE_MLF_STUDENT", "Andrea Amarante")


# In-memory mapping for active MLF Hebrew sessions.  Not persisted; a fresh
# BrainLab graph is used for replay tests.
_HEBREW_MLF_SESSIONS: dict[str, dict] = {}
_HEBREW_MLF_LOCK = threading.Lock()
_HEBREW_MLF_WORK_QUEUE: "queue.Queue[tuple[Any, threading.Event, dict]]" = queue.Queue()
_HEBREW_MLF_WORKER_STARTED = False
_HEBREW_MLF_WORKER_THREAD_ID: int | None = None
_HELP_NORMS_LOCK = threading.Lock()
_HELP_NORMS: help_profiler.HeLPNorms | None = None
_HELP_NORMS_SIGNATURE: tuple[tuple[str, int, int], ...] = ()


def _hebrew_mlf_worker() -> None:
    global _HEBREW_MLF_WORKER_THREAD_ID
    _HEBREW_MLF_WORKER_THREAD_ID = threading.get_ident()
    while True:
        func, done, box = _HEBREW_MLF_WORK_QUEUE.get()
        try:
            box["result"] = func()
        except Exception as exc:
            box["error"] = exc
        finally:
            done.set()
            _HEBREW_MLF_WORK_QUEUE.task_done()


def _run_hebrew_mlf_job(func: Any) -> Any:
    global _HEBREW_MLF_WORKER_STARTED
    if threading.get_ident() == _HEBREW_MLF_WORKER_THREAD_ID:
        return func()
    with _HEBREW_MLF_LOCK:
        if not _HEBREW_MLF_WORKER_STARTED:
            worker = threading.Thread(target=_hebrew_mlf_worker, name="MindTuneHebrewMLF", daemon=True)
            worker.start()
            _HEBREW_MLF_WORKER_STARTED = True
    done = threading.Event()
    box: dict[str, Any] = {}
    _HEBREW_MLF_WORK_QUEUE.put((func, done, box))
    if not done.wait(30):
        raise TimeoutError("Timeout MLF Hebrew")
    if "error" in box:
        raise box["error"]
    return box.get("result")


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path.resolve()
    return paths[0].resolve()


PROJECT_ROOT_FALLBACK = Path.home() / "Documents" / "Chatgpt" / "Biohacking"
SSH_KEY = first_existing_path(
    Path(os.environ["MINDTUNE_SSH_KEY"]) if os.environ.get("MINDTUNE_SSH_KEY") else ROOT / ".ssh_agent" / "codex_biohacking_ed25519",
    PROJECT_ROOT_FALLBACK / ".ssh_agent" / "codex_biohacking_ed25519",
)
REMOTE_MINDTUNE_INSTALLER = first_existing_path(
    Path(os.environ["MINDTUNE_REMOTE_INSTALLER"])
    if os.environ.get("MINDTUNE_REMOTE_INSTALLER")
    else ROOT / "tools" / "remote_install_mindtune_v2_brainlab.py",
    PROJECT_ROOT_FALLBACK / "tools" / "remote_install_mindtune_v2_brainlab.py",
)


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def text_response(handler: BaseHTTPRequestHandler, text: str, content_type: str) -> None:
    data = text.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length < 0 or length > MAX_BODY:
        raise ValueError("payload troppo grande")
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def tail_text(path: Path, max_bytes: int = MAX_LOG_BYTES) -> str:
    if not path.exists() or not path.is_file():
        return ""
    size = path.stat().st_size
    with path.open("rb") as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
            data = f.read()
            return "[...]\n" + data.decode("utf-8", errors="replace")
        return f.read().decode("utf-8", errors="replace")


def mac_python() -> Path:
    return MAC_VENV_PY if MAC_VENV_PY.exists() else Path("python3")


def mac_env() -> dict:
    env = os.environ.copy()
    if MAC_PYTHONPATH:
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = MAC_PYTHONPATH if not existing else f"{MAC_PYTHONPATH}{os.pathsep}{existing}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def read_mac_state() -> dict:
    if not MAC_STATE.exists():
        return {"running": False}
    try:
        state = json.loads(MAC_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"running": False}
    pid = int(state.get("pid") or 0)
    running = is_pid_running(pid)
    state["running"] = running
    if not running:
        if MAC_STATE.exists():
            try:
                MAC_STATE.unlink()
            except Exception:
                pass
        return {"running": False, "ended_label": "processo non attivo"}
    return state


def active_status_is_stale(status: dict) -> bool:
    if status.get("phase") not in ACTIVE_PHASES:
        return False
    try:
        updated_at = float(status.get("updated_at") or 0)
    except (TypeError, ValueError):
        updated_at = 0
    return updated_at <= 0 or (time.time() - updated_at) > ACTIVE_STATUS_MAX_AGE_S


def extract_battery_percent(candidate: dict | None) -> int | None:
    if not candidate:
        return None
    value = candidate.get("battery_percent")
    if isinstance(value, (int, float)) and 0 <= value <= 100:
        return int(round(value))
    return None


def read_cached_battery_percent(status: dict | None = None) -> int | None:
    candidates = []
    if status:
        candidates.append(status)
    if MAC_BATTERY_FILE.exists():
        try:
            candidates.append(json.loads(MAC_BATTERY_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    if MAC_STATUS_FILE.exists():
        try:
            candidates.append(json.loads(MAC_STATUS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    for session in list_mac_sessions():
        meta_name = session.get("meta")
        if not meta_name:
            continue
        meta_path = MAC_SESSIONS / str(meta_name)
        try:
            candidates.append(json.loads(meta_path.read_text(encoding="utf-8")))
        except Exception:
            pass
    for candidate in candidates:
        value = extract_battery_percent(candidate)
        if value is not None:
            return value
    return None


def mac_status() -> dict:
    state = read_mac_state()
    status = {}
    status_file = state.get("status_file") or str(MAC_STATUS_FILE)
    if status_file and Path(status_file).exists():
        try:
            status = json.loads(Path(status_file).read_text(encoding="utf-8"))
        except Exception:
            status = {}
    if status.get("phase") in TERMINAL_PHASES:
        state["running"] = False
    stale_active_status = active_status_is_stale(status)
    if (not state.get("running") or stale_active_status) and status.get("phase") in ACTIVE_PHASES:
        status = {}
        state["running"] = False
    battery_percent = extract_battery_percent(status) if state.get("running") else None
    if battery_percent is not None:
        status["battery_percent"] = battery_percent
    sessions = list_mac_sessions()
    latest = next(
        (
            session for session in sessions
            if session.get("source") != "task" and int(session.get("samples") or session.get("rows") or 0) > 0
        ),
        sessions[0] if sessions else None,
    )
    return {
        "running": bool(state.get("running")) and status.get("phase") not in TERMINAL_PHASES,
        "pid": state.get("pid"),
        "condition": state.get("condition"),
        "started_at": state.get("started_at"),
        "log": state.get("log"),
        "phase": status.get("phase"),
        "phase_started_at": status.get("phase_started_at"),
        "updated_at": status.get("updated_at"),
        "duration": status.get("duration") or state.get("duration"),
        "prep": status.get("prep") or state.get("prep"),
        "samples": status.get("samples"),
        "packets": status.get("packets"),
        "csv": status.get("csv"),
        "battery_percent": status.get("battery_percent"),
        "contact_state": status.get("contact_state"),
        "lead_off_center": status.get("lead_off_center"),
        "lead_off_side": status.get("lead_off_side"),
        "signal_quality_warning": status.get("signal_quality_warning"),
        "sleep_idle_time_sec": status.get("sleep_idle_time_sec"),
        "vibration_intensity": status.get("vibration_intensity"),
        "live_features": status.get("live_features"),
        "latest_session": latest,
    }


def wait_for_mac_phase(phases: set[str], timeout: float) -> dict:
    deadline = time.time() + timeout
    last_status: dict = {}
    while time.time() < deadline:
        last_status = mac_status()
        if last_status.get("phase") in phases:
            return last_status
        if not last_status.get("running") and last_status.get("phase") not in TERMINAL_PHASES:
            return last_status
        time.sleep(0.2)
    return last_status or mac_status()


def list_mac_sessions() -> list[dict]:
    if not MAC_SESSIONS.exists():
        eeg_items: list[dict] = []
    else:
        eeg_items = []
        for path in MAC_SESSIONS.glob("session_*.csv"):
            stat = path.stat()
            if stat.st_mtime < SERIOUS_DATA_START_TS:
                continue
            meta = path.with_suffix(".json")
            rows = None
            if path.stat().st_size > 0:
                try:
                    with path.open("rb") as handle:
                        rows = max(0, sum(1 for _ in handle) - 1)
                except Exception:
                    rows = None
            item = {
                "source": "eeg",
                "name": path.name,
                "mtime": stat.st_mtime,
                "mtime_label": time.strftime("%H:%M:%S", time.localtime(stat.st_mtime)),
                "size": stat.st_size,
                "rows": rows,
                "meta": meta.name if meta.exists() else None,
            }
            if meta.exists():
                try:
                    metadata = json.loads(meta.read_text(encoding="utf-8"))
                    item["samples"] = metadata.get("samples")
                    item["sample_rate_est_hz"] = metadata.get("sample_rate_est_hz")
                    item["packet_index_gaps"] = metadata.get("packet_index_gaps")
                except Exception:
                    pass
            flashcard_summary = path.with_suffix(".flashcards.json")
            if flashcard_summary.exists():
                try:
                    summary = json.loads(flashcard_summary.read_text(encoding="utf-8"))
                    item["flashcard_events"] = summary.get("events")
                    item["flashcard_score"] = summary.get("score")
                except Exception:
                    pass
            event_summary = path.with_suffix(".events.json")
            if event_summary.exists():
                try:
                    summary = json.loads(event_summary.read_text(encoding="utf-8"))
                    item["behavioral_events"] = summary.get("events")
                    item["behavioral_event_types"] = summary.get("event_types")
                    item["behavioral_score"] = summary.get("score")
                except Exception:
                    pass
            manifest_path = path.with_suffix(".manifest.json")
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    item["session_covariates"] = manifest.get("covariates")
                    item["study_context"] = manifest.get("study_context")
                except Exception:
                    pass
            eeg_items.append(item)
    task_items = list_mindtune_task_sessions()
    v2_legacy_names = {
        Path(str(item.get("legacy_csv_source") or "")).name
        for item in task_items
        if item.get("source") == "eeg_v2" and item.get("legacy_csv_source")
    }
    if v2_legacy_names:
        eeg_items = [item for item in eeg_items if item.get("name") not in v2_legacy_names]
    items = [*eeg_items, *task_items]
    items.sort(key=lambda item: item["mtime"], reverse=True)
    return items[:40]


def list_mindtune_task_sessions() -> list[dict]:
    if not MINDTUNE_SESSIONS.exists():
        return []
    items: list[dict] = []
    for path in MINDTUNE_SESSIONS.glob("*/session.json"):
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_mtime < SERIOUS_DATA_START_TS:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        has_eeg_payload = (path.parent / "samples.csv").exists() or (path.parent / "packets.csv").exists()
        if not has_eeg_payload and payload.get("eeg_linked"):
            continue
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        score = payload.get("score") if isinstance(payload.get("score"), dict) else {}
        covariates = payload.get("covariates") if isinstance(payload.get("covariates"), dict) else {}
        session_id = safe_memory_text(str(payload.get("session_id") or path.parent.name), 120)
        label = safe_memory_text(str(payload.get("label") or context.get("task_label") or payload.get("condition") or session_id), 160)
        samples = payload.get("sample_count")
        if samples is None and (path.parent / "samples.csv").exists():
            try:
                with (path.parent / "samples.csv").open("rb") as handle:
                    samples = max(0, sum(1 for _ in handle) - 1)
            except Exception:
                samples = 0
        events_count = payload.get("event_count")
        if events_count is None and (path.parent / "events.csv").exists():
            try:
                with (path.parent / "events.csv").open("rb") as handle:
                    events_count = max(0, sum(1 for _ in handle) - 1)
            except Exception:
                events_count = 0
        item = {
            "source": "eeg_v2" if has_eeg_payload else "task",
            "session_id": session_id,
            "session_dir": path.parent.name,
            "name": f"{label} · {session_id}",
            "mtime": stat.st_mtime,
            "mtime_label": time.strftime("%H:%M:%S", time.localtime(stat.st_mtime)),
            "size": stat.st_size,
            "samples": int(samples or 0) if has_eeg_payload else 0,
            "sample_rate_est_hz": payload.get("sample_rate_hz") if has_eeg_payload else None,
            "packet_index_gaps": None if has_eeg_payload else 0,
            "behavioral_events": events_count if events_count is not None else len(payload.get("events", [])),
            "behavioral_score": score,
            "session_covariates": covariates,
            "study_context": context or payload.get("study_context"),
            "task_label": label,
            "condition": payload.get("condition") or context.get("task_id"),
            "eeg_linked": bool(has_eeg_payload or payload.get("eeg_linked")),
            "legacy_csv_source": payload.get("legacy_csv_source"),
        }
        items.append(item)
    items.sort(key=lambda item: item["mtime"], reverse=True)
    return items


def delete_mac_session(params: dict) -> dict:
    name = str(params.get("name", ""))
    if not re.fullmatch(r"session_[A-Za-z0-9_.-]+\.csv", name):
        raise ValueError("nome sessione non valido")
    sessions_root = MAC_SESSIONS.resolve()
    csv_path = (MAC_SESSIONS / name).resolve()
    if sessions_root not in csv_path.parents:
        raise ValueError("sessione non valida")
    if not csv_path.exists():
        return {"deleted": [], "message": "sessione gia eliminata"}
    if not csv_path.is_file():
        raise ValueError("sessione non trovata")
    meta_path = csv_path.with_suffix(".json")
    manifest_path = csv_path.with_suffix(".manifest.json")
    flashcard_json = csv_path.with_suffix(".flashcards.json")
    flashcard_jsonl = csv_path.with_suffix(".flashcards.jsonl")
    events_json = csv_path.with_suffix(".events.json")
    events_jsonl = csv_path.with_suffix(".events.jsonl")
    deleted = []
    csv_path.unlink()
    deleted.append(csv_path.name)
    for path in (meta_path, manifest_path, flashcard_json, flashcard_jsonl, events_json, events_jsonl):
        if path.exists() and path.is_file():
            path.unlink()
            deleted.append(path.name)
    return {"deleted": deleted}


def delete_mindtune_task_session(params: dict) -> dict:
    session_id = safe_memory_text(str(params.get("session_id") or ""), 180)
    session_dir_name = safe_memory_text(str(params.get("session_dir") or ""), 220)
    lookup = session_dir_name or session_id
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", lookup):
        raise ValueError("sessione task non valida")
    sessions_root = MINDTUNE_SESSIONS.resolve()
    session_dir = (MINDTUNE_SESSIONS / lookup).resolve()
    if sessions_root not in session_dir.parents:
        raise ValueError("sessione task non valida")
    if not session_dir.exists():
        for candidate in MINDTUNE_SESSIONS.glob("*/session.json"):
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                continue
            if str(payload.get("session_id") or "") == session_id:
                session_dir = candidate.parent.resolve()
                break
        else:
            return {"deleted": [], "message": "sessione task gia eliminata"}
    deleted: list[str] = []
    for path in sorted(session_dir.glob("*")):
        if path.is_file():
            path.unlink()
            deleted.append(f"{session_dir.name}/{path.name}")
    try:
        session_dir.rmdir()
    except OSError:
        pass
    return {"deleted": deleted}


def delete_aborted_mac_sessions() -> dict:
    deleted: list[str] = []
    for session in list_mac_sessions():
        if session.get("source") == "task":
            events = int(session.get("behavioral_events") or 0)
            samples = int(session.get("samples") or 0)
            if events == 0 and samples == 0:
                result = delete_mindtune_task_session({
                    "session_id": session.get("session_id", ""),
                    "session_dir": session.get("session_dir", ""),
                })
                deleted.extend(result.get("deleted", []))
            continue
        if session.get("source") == "eeg_v2":
            samples = int(session.get("samples") or 0)
            if samples == 0:
                result = delete_mindtune_task_session({
                    "session_id": session.get("session_id", ""),
                    "session_dir": session.get("session_dir", ""),
                })
                deleted.extend(result.get("deleted", []))
            continue
        samples = session.get("samples")
        rows = session.get("rows")
        size = int(session.get("size") or 0)
        aborted = size == 0 or samples == 0 or rows == 0
        if not aborted:
            continue
        result = delete_mac_session({"name": session["name"]})
        deleted.extend(result.get("deleted", []))
    return {"deleted": deleted}


def memory_db() -> dict:
    ensure_mac_dirs()
    if not MEMORY_FILE.exists():
        return {"items": [], "events": [], "created_at": time.time(), "version": 1}
    try:
        payload = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    payload.setdefault("items", [])
    payload.setdefault("events", [])
    payload.setdefault("version", 1)
    return payload


def write_memory_db(payload: dict) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = MEMORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(MEMORY_FILE)


def catalog_patch_db() -> dict:
    ensure_mac_dirs()
    if not FLASHCARD_CATALOG_PATCH_FILE.exists():
        return {"version": 1, "updates": {}, "deleted": {}, "events": []}
    try:
        payload = json.loads(FLASHCARD_CATALOG_PATCH_FILE.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    payload.setdefault("version", 1)
    payload.setdefault("updates", {})
    payload.setdefault("deleted", {})
    payload.setdefault("events", [])
    return payload


def write_catalog_patch_db(payload: dict) -> None:
    FLASHCARD_CATALOG_PATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FLASHCARD_CATALOG_PATCH_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FLASHCARD_CATALOG_PATCH_FILE)


def _help_norms_signature() -> tuple[tuple[str, int, int], ...]:
    signature = []
    for path in (HELP_LEXICAL_METRICS_FILE, HELP_LD_SUMMARY_FILE, HELP_NAMING_SUMMARY_FILE):
        try:
            stat = path.stat()
            signature.append((path.name, stat.st_mtime_ns, stat.st_size))
        except OSError:
            signature.append((path.name, 0, 0))
    return tuple(signature)


def help_norms() -> help_profiler.HeLPNorms:
    global _HELP_NORMS, _HELP_NORMS_SIGNATURE
    signature = _help_norms_signature()
    if _HELP_NORMS is not None and signature == _HELP_NORMS_SIGNATURE:
        return _HELP_NORMS
    with _HELP_NORMS_LOCK:
        signature = _help_norms_signature()
        if _HELP_NORMS is None or signature != _HELP_NORMS_SIGNATURE:
            _HELP_NORMS = help_profiler.HeLPNorms(
                HELP_LEXICAL_METRICS_FILE,
                HELP_LD_SUMMARY_FILE,
                HELP_NAMING_SUMMARY_FILE,
            )
            _HELP_NORMS_SIGNATURE = signature
    return _HELP_NORMS


def help_item_state(params: dict | None = None) -> dict:
    params = params or {}
    hebrew = raw_flashcard_text(strip_hebrew_niqqud(str(params.get("hebrew") or "")), 500)
    item_id = safe_memory_text(str(params.get("item_id") or ""), 120)
    memory = memory_db()
    item = next((candidate for candidate in memory.get("items", []) if str(candidate.get("id") or "") == item_id), None)
    if item and not hebrew:
        hebrew = raw_flashcard_text(str(item.get("raw_front") or item.get("term") or ""), 500)
    personal_events = [event for event in (item or {}).get("events", []) if isinstance(event, dict)]
    result_counts = {"correct": 0, "partial": 0, "miss": 0}
    latencies = []
    for event in personal_events:
        result = str(event.get("result") or "")
        if result in result_counts:
            result_counts[result] += 1
        try:
            latencies.append(float(event.get("latency_s")) * 1000)
        except (TypeError, ValueError):
            pass
    norms = help_norms().item(hebrew)
    return {
        "ok": True,
        "item_id": item_id,
        "canonical_item_id": str((item or {}).get("canonical_item_id") or ""),
        "hebrew": hebrew,
        "norms": norms,
        "personal": {
            "observation_count": len(personal_events),
            "result_counts": result_counts,
            "median_recall_latency_ms": round(statistics.median(latencies), 1) if latencies else None,
            "last_result": (item or {}).get("last_result"),
            "next_due_at": (item or {}).get("next_due_at"),
        },
    }


def help_profile_state() -> dict:
    memory = memory_db()
    active_items = [
        item for item in memory.get("items", [])
        if isinstance(item, dict) and is_study_ready_flashcard(item)
    ]
    active_item_ids = {str(item.get("id") or "") for item in active_items}
    profile_memory = dict(memory)
    profile_memory["items"] = active_items
    profile_memory["events"] = [
        event for event in memory.get("events", [])
        if isinstance(event, dict) and str(event.get("item_id") or "") in active_item_ids
    ]
    profile = help_profiler.build_profile(
        norms=help_norms(),
        memory=profile_memory,
        eeg_sessions_dir=MAC_SESSIONS,
        behavioral_events_dir=BEHAVIORAL_EVENTS,
        shoresh_sessions_dir=SHORESH_SESSIONS,
        mlf_db_path=HEBREW_MLF_DB_PATH,
        learner_id=HEBREW_MLF_DEFAULT_STUDENT,
    )
    return {"ok": True, "profile": profile}


def conjugation_catalog_state() -> dict:
    pealim_catalog = {}
    if PEALIM_VERB_CATALOG_FILE.exists():
        try:
            pealim_catalog = json.loads(PEALIM_VERB_CATALOG_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            pealim_catalog = {"error": str(exc), "verbs": []}
    pealim_practice_verbs = [
        verb for verb in pealim_catalog.get("verbs", [])
        if verb.get("source") == "pealim" and isinstance(verb.get("present"), list) and isinstance(verb.get("targets"), dict)
    ]
    return {
        "pealim_catalog_path": str(PEALIM_VERB_CATALOG_FILE),
        "pealim_catalog_count": len(pealim_practice_verbs),
        "pealim_catalog_generated_at": pealim_catalog.get("generated_at", ""),
        "pealim_catalog_error": pealim_catalog.get("error", ""),
        "pealim_practice_verbs": pealim_practice_verbs,
    }


def hebrew_source_registry_state() -> dict:
    """Report source readiness without turning external resources into dependencies."""
    try:
        registry = json.loads(HEBREW_SOURCE_REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "sources": [], "ready_count": 0, "total_count": 0}

    operational_source_ids = {
        "academy_hebrew_language",
        "pealim",
        "help_lexicon",
        "hebrew_wordnet_shuly",
    }
    support_source_ids = {"nnlp_hebrew_resources"}
    checks = {
        "academy_hebrew_language": lambda: True,
        "pealim": lambda: PEALIM_VERB_CATALOG_FILE.exists(),
        "help_lexicon": lambda: all(path.exists() for path in (HELP_LEXICAL_METRICS_FILE, HELP_LD_SUMMARY_FILE, HELP_NAMING_SUMMARY_FILE)),
        "hebrew_wordnet_shuly": lambda: HEBREW_WORDNET_INDEX_FILE.exists(),
        "nnlp_hebrew_resources": lambda: NNLP_VERB_INDEX_FILE.exists(),
    }
    sources = []
    for raw in registry.get("sources", []):
        if not isinstance(raw, dict):
            continue
        source = dict(raw)
        source_id = str(source.get("source_id") or "")
        if source_id in operational_source_ids:
            source_category = "operational"
        elif source_id in support_source_ids:
            source_category = "support"
        elif source_id in checks:
            source_category = "external_reference"
        else:
            # Unknown or legacy sources are silently dropped.
            continue
        available = bool(checks.get(source_id, lambda: False)())
        source["available"] = available
        source["source_category"] = source_category
        source["active_for_recovery"] = available and source_category == "operational"
        sources.append(source)
    operational_sources = [source for source in sources if source.get("source_category") == "operational"]
    support_sources = [source for source in sources if source.get("source_category") == "support"]
    operational_ready = sum(bool(source.get("available")) for source in operational_sources)
    support_ready = sum(bool(source.get("available")) for source in support_sources)
    source_summary_label = (
        f"{operational_ready}/{len(operational_sources)} fonti operative"
        f" · {support_ready}/{len(support_sources)} supporto locale"
    )
    return {
        "ok": True,
        "schema_version": registry.get("schema_version"),
        "policy": registry.get("policy"),
        "sources": sources,
        "ready_count": operational_ready,
        "total_count": len(sources),
        "operational_ready_count": operational_ready,
        "operational_total_count": len(operational_sources),
        "support_ready_count": support_ready,
        "support_total_count": len(support_sources),
        "source_summary_label": source_summary_label,
    }


def hebrew_recovery_plan_state(minutes: int = 30, readiness: float | None = None, sleep_h: float | None = None) -> dict:
    """Build a domain-level recovery plan without promoting any source to curriculum truth."""
    duration = max(15, min(90, int(minutes or 30)))
    profile = help_profile_state().get("profile") or {}
    evidence = profile.get("evidence") if isinstance(profile.get("evidence"), dict) else {}
    performance = profile.get("performance") if isinstance(profile.get("performance"), dict) else {}
    source_counts = evidence.get("source_counts") if isinstance(evidence.get("source_counts"), dict) else {}
    low_recovery_context = (readiness is not None and readiness < 70) or (sleep_h is not None and sleep_h < 6.5)
    insufficient_personal_data = evidence.get("status") != "preliminary"
    if low_recovery_context:
        weights = [0.14, 0.23, 0.25, 0.20, 0.18]
        dose_mode = "conservative_start"
    elif insufficient_personal_data:
        weights = [0.12, 0.24, 0.30, 0.21, 0.13]
        dose_mode = "calibration"
    else:
        weights = [0.10, 0.18, 0.36, 0.23, 0.13]
        dose_mode = "progressive"
    phase_minutes = [max(1, round(duration * weight)) for weight in weights]
    phase_minutes[2] += duration - sum(phase_minutes)
    phases = [
        {"id": "activation", "label": "Prima · controllo", "purpose": "controllo attentivo breve, senza allenare uno score", "minutes": phase_minutes[0], "source": "behavioral_warmup"},
        {"id": "lexical_access", "label": "Prima · lessico", "purpose": "accesso lessicale caratterizzato con le norme HeLP quando disponibili", "minutes": phase_minutes[1], "source": "help_norms"},
        {"id": "morphological_production", "label": "Domino produttivo", "purpose": "persona, tempo e recupero generativo su verbi Pealim", "minutes": phase_minutes[2], "source": "pealim"},
        {"id": "live_comprehension", "label": "Comprensione", "purpose": "riconoscimento di forme flesse arricchite dalle norme HeLP", "minutes": phase_minutes[3], "source": "pealim_context+help_norms"},
        {"id": "reentry", "label": "Dopo · re-entry", "purpose": "nuova prova sugli elementi fragili o più lenti osservati oggi", "minutes": phase_minutes[4], "source": "personal_event_stream"},
    ]
    resource_state = hebrew_source_registry_state()
    return {
        "ok": True,
        "plan": {
            "schema_version": "mindtune.hebrew_recovery_plan/1.0.0",
            "status_label": "Profilo preliminare" if evidence.get("status") == "preliminary" else "Calibrazione attiva",
            "duration_minutes": duration,
            "rationale": "Le prestazioni osservabili guidano la dose; Oura regola soltanto la partenza, HeLP caratterizza gli stimoli e Pealim alimenta la produzione.",
            "dose": {
                "mode": dose_mode,
                "readiness_score": readiness,
                "sleep_h": sleep_h,
                "behavioral_warmup_may_override": True,
            },
            "evidence": {
                "status": evidence.get("status", "insufficient_data"),
                "observations": int(evidence.get("eligible_observation_count") or 0),
                "sessions": int(evidence.get("distinct_session_count") or 0),
                "items": int(evidence.get("distinct_item_count") or 0),
                "success_ratio": performance.get("success_ratio"),
                "source_counts": source_counts,
                "resources_ready": resource_state.get("operational_ready_count", resource_state.get("ready_count", 0)),
                "resources_total": resource_state.get("operational_total_count", resource_state.get("total_count", 0)),
                "resources_label": resource_state.get("source_summary_label", ""),
            },
            "phases": phases,
            "active_increment": "morphological_production",
            "source_policy": {
                "help": "stimulus_norms_and_read_only_profiler",
                "pealim": "verb_paradigm_source",
            },
        },
    }


SHORESH_COLUMNS = [
    "session_id",
    "timestamp",
    "item_id",
    "task_type",
    "level",
    "root",
    "answer",
    "correct_answer",
    "is_correct",
    "reaction_time_ms",
    "timeout",
    "semantic_transparency",
    "help_frequency_mean",
    "help_ld_rt_mean",
    "help_ld_accuracy_mean",
    "self_lucidity_pre",
    "self_fatigue_pre",
    "self_hebrew_familiarity_pre",
    "self_effort_post",
    "self_frustration_post",
    "self_focus_post",
]


def shoresh_catalog_state() -> dict:
    if not SHORESH_ITEMS_FILE.exists():
        return {
            "ok": False,
            "error": "shoresh_items_v1.json non generato",
            "items": [],
            "coverage_report": {},
            "session_blueprint": {},
        }
    try:
        payload = json.loads(SHORESH_ITEMS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "items": [], "coverage_report": {}, "session_blueprint": {}}
    payload.setdefault("items", [])
    return {
        "ok": True,
        "protocol_name": payload.get("protocol_name", "shoresh_lab_v1"),
        "schema": payload.get("schema", "shoresh_items_v1"),
        "items": payload.get("items", []),
        "coverage_report": payload.get("coverage_report", {}),
        "session_blueprint": payload.get("session_blueprint", {}),
        "source_file": str(SHORESH_ITEMS_FILE),
        "mode_policy": {
            "test": "misura senza feedback",
            "training": "puo mostrare feedback e riproporre errori; escluso dai trend principali",
        },
    }


def shoresh_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def shoresh_mean(values: list[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 4)


def shoresh_help_mean(item: dict, key_fragment: str) -> float | None:
    metrics = item.get("help_metrics") if isinstance(item.get("help_metrics"), dict) else {}
    values = [shoresh_float(value) for key, value in metrics.items() if key_fragment in key]
    return shoresh_mean(values)


def shoresh_bool(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "si", "sì"}


def shoresh_median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def shoresh_percentile(values: list[float], pct: float) -> float | None:
    clean = sorted(values)
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    pos = (len(clean) - 1) * pct
    low = int(pos)
    high = min(len(clean) - 1, low + 1)
    return clean[low] + (clean[high] - clean[low]) * (pos - low)


def shoresh_accuracy(rows: list[dict]) -> float:
    return sum(1 for row in rows if shoresh_bool(row.get("is_correct"))) / len(rows) if rows else 0.0


def shoresh_rt_values(rows: list[dict], correct_only: bool = False) -> list[float]:
    values = []
    for row in rows:
        if correct_only and not shoresh_bool(row.get("is_correct")):
            continue
        if shoresh_bool(row.get("timeout")):
            continue
        value = shoresh_float(row.get("reaction_time_ms"))
        if value and value > 0:
            values.append(value)
    return values


def shoresh_score_rows(rows: list[dict], session_meta: dict) -> dict:
    total = len(rows)
    rts = shoresh_rt_values(rows)
    first = rows[: max(1, total // 3)] if rows else []
    last = rows[-max(1, total // 3):] if rows else []
    timeout_rate = sum(1 for row in rows if shoresh_bool(row.get("timeout"))) / total if total else 0.0
    accuracy_total = shoresh_accuracy(rows)
    median_rt = shoresh_median(rts) or 0
    p90_rt = shoresh_percentile(rts, 0.90) or 0
    fatigue_slope_rt = (shoresh_median(shoresh_rt_values(last)) or 0) - (shoresh_median(shoresh_rt_values(first)) or 0) if rows else None
    fatigue_slope_accuracy = shoresh_accuracy(first) - shoresh_accuracy(last) if rows else None
    correct_rts = shoresh_rt_values(rows, correct_only=True)
    p75_correct = shoresh_percentile(correct_rts, 0.75)
    hesitation_index = None
    if p75_correct is not None and correct_rts:
        hesitation_index = sum(1 for value in correct_rts if value > p75_correct) / len(correct_rts)
    def grouped(key: str) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for row in rows:
            out.setdefault(str(row.get(key) or ""), []).append(row)
        return out
    by_task = grouped("task_type")
    by_level = grouped("level")
    flags = []
    if timeout_rate > 0.25:
        flags.append("too_many_timeouts")
    if total and sum(1 for value in rts if value < 250) / total > 0.10:
        flags.append("too_fast_responses")
    if total < 40:
        flags.append("low_item_count")
    missing_help = sum(1 for row in rows if not row.get("help_frequency_mean") and not row.get("help_ld_rt_mean"))
    if total and missing_help / total > 0.50:
        flags.append("missing_help_metrics")
    if session_meta.get("interrupted"):
        flags.append("interrupted_session")
    speed_factor = max(0.4, min(1.1, 1 - ((median_rt - 1200) / 4000)))
    stability_factor = max(0.5, min(1.0, 1 - timeout_rate - max(0, fatigue_slope_accuracy or 0)))
    return {
        "session_id": session_meta.get("session_id"),
        "started_at": session_meta.get("started_at"),
        "ended_at": session_meta.get("ended_at"),
        "protocol_name": "shoresh_lab_v1",
        "mode": session_meta.get("mode", "test"),
        "items_total": total,
        "accuracy_total": round(accuracy_total, 4),
        "median_rt_ms": round(median_rt, 1),
        "p90_rt_ms": round(p90_rt, 1),
        "accuracy_by_task_type": {key: round(shoresh_accuracy(value), 4) for key, value in by_task.items()},
        "median_rt_by_task_type": {key: round(shoresh_median(shoresh_rt_values(value)) or 0, 1) for key, value in by_task.items()},
        "accuracy_by_level": {key: round(shoresh_accuracy(value), 4) for key, value in by_level.items()},
        "median_rt_by_level": {key: round(shoresh_median(shoresh_rt_values(value)) or 0, 1) for key, value in by_level.items()},
        "fatigue_slope_rt": None if fatigue_slope_rt is None else round(fatigue_slope_rt, 1),
        "fatigue_slope_accuracy": None if fatigue_slope_accuracy is None else round(fatigue_slope_accuracy, 4),
        "timeout_rate": round(timeout_rate, 4),
        "hesitation_index": None if hesitation_index is None else round(hesitation_index, 4),
        "root_skill_score": round(100 * accuracy_total * speed_factor * stability_factor, 1),
        "data_quality_flags": flags,
        "score_note": "Indice interno personale, non diagnostico e non medico.",
    }


def shoresh_save_session(params: dict) -> dict:
    items_by_id = {
        str(item.get("item_id")): item
        for item in shoresh_catalog_state().get("items", [])
        if item.get("item_id")
    }
    raw_events = params.get("events") if isinstance(params.get("events"), list) else []
    if not raw_events:
        raise ValueError("nessuna risposta Shoresh da salvare")
    now_label = time.strftime("%Y%m%d_%H%M%S")
    session_id = safe_memory_text(str(params.get("session_id") or f"shoresh_{now_label}"), 120)
    mode = str(params.get("mode") or "test")
    if mode not in {"test", "training"}:
        mode = "test"
    pre = params.get("pre") if isinstance(params.get("pre"), dict) else {}
    post = params.get("post") if isinstance(params.get("post"), dict) else {}
    rows = []
    for event in raw_events:
        if not isinstance(event, dict):
            continue
        item_id = str(event.get("item_id") or "")
        item = items_by_id.get(item_id, {})
        timestamp = safe_memory_text(str(event.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%S%z")), 80)
        is_correct = bool(event.get("is_correct"))
        timeout = bool(event.get("timeout"))
        rows.append({
            "session_id": session_id,
            "timestamp": timestamp,
            "item_id": item_id,
            "task_type": item.get("task_type", event.get("task_type", "")),
            "level": item.get("level", event.get("level", "")),
            "root": item.get("root", event.get("root", "")),
            "answer": raw_flashcard_text(str(event.get("answer", "")), 400),
            "correct_answer": raw_flashcard_text(str(item.get("correct_answer", event.get("correct_answer", ""))), 400),
            "is_correct": "true" if is_correct else "false",
            "reaction_time_ms": int(float(event.get("reaction_time_ms") or 0)),
            "timeout": "true" if timeout else "false",
            "semantic_transparency": item.get("semantic_transparency", ""),
            "help_frequency_mean": shoresh_help_mean(item, "frequency"),
            "help_ld_rt_mean": shoresh_help_mean(item, "ld_mean_rt"),
            "help_ld_accuracy_mean": shoresh_help_mean(item, "ld_accuracy"),
            "self_lucidity_pre": as_int(pre.get("lucidity"), 0, 0, 7),
            "self_fatigue_pre": as_int(pre.get("fatigue"), 0, 0, 7),
            "self_hebrew_familiarity_pre": as_int(pre.get("hebrew_familiarity"), 0, 0, 7),
            "self_effort_post": as_int(post.get("effort"), 0, 0, 7),
            "self_frustration_post": as_int(post.get("frustration"), 0, 0, 7),
            "self_focus_post": as_int(post.get("focus"), 0, 0, 7),
        })
    if not rows:
        raise ValueError("nessuna risposta Shoresh valida")
    SHORESH_SESSIONS.mkdir(parents=True, exist_ok=True)
    csv_path = SHORESH_SESSIONS / f"{session_id}.csv"
    json_path = SHORESH_SESSIONS / f"{session_id}.summary.json"
    meta = {
        "session_id": session_id,
        "protocol_name": "shoresh_lab_v1",
        "mode": mode,
        "started_at": safe_memory_text(str(params.get("started_at") or rows[0]["timestamp"]), 80),
        "ended_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "device": "MacBook",
        "data_quality_flags": [],
        "export_paths": {"csv": str(csv_path), "summary_json": str(json_path)},
        "pre": pre,
        "post": post,
        "training_policy": "training excluded from primary test trend" if mode == "training" else "primary behavioral test",
    }
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHORESH_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    summary = shoresh_score_rows(rows, meta)
    meta["data_quality_flags"] = summary.get("data_quality_flags", [])
    summary.update({key: meta[key] for key in ("device", "export_paths", "pre", "post")})
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"session_id": session_id, "csv": str(csv_path), "summary_json": str(json_path), "summary": summary}


def hebrew_verb_catalog() -> dict:
    if not HEBREW_VERB_CATALOG_FILE.exists():
        return {"count": 0, "verbs": []}
    try:
        payload = json.loads(HEBREW_VERB_CATALOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"count": 0, "verbs": []}
    payload.setdefault("verbs", [])
    payload["count"] = len(payload["verbs"])
    payload["catalog_file"] = str(HEBREW_VERB_CATALOG_FILE)
    return payload


def catalog_patch_key(item: dict) -> str:
    seed_id = str(item.get("seed_id") or item.get("id") or "").strip()
    if seed_id:
        return f"seed_id:{seed_id}"
    seed_index = str(item.get("seed_index") or "").strip()
    if seed_index:
        return f"seed_index:{seed_index}"
    return f"item_id:{item.get('id', '')}"


def memory_catalog_patch_key(item: dict) -> str:
    seed_id = str(item.get("seed_id") or "").strip()
    if seed_id:
        return f"seed_id:{seed_id}"
    seed_index = str(item.get("seed_index") or "").strip()
    if seed_index:
        return f"seed_index:{seed_index}"
    item_id = str(item.get("id") or "").strip()
    if item_id.startswith("seed_"):
        digits = re.sub(r"\D", "", item_id.split("_", 2)[1] if "_" in item_id else "")
        if digits:
            return f"seed_index:{int(digits)}"
    return f"item_id:{item_id}"


def patched_seed_item(seed_item: dict) -> dict | None:
    patches = catalog_patch_db()
    key = catalog_patch_key(seed_item)
    if key in patches.get("deleted", {}):
        return None
    patched = dict(seed_item)
    update = patches.get("updates", {}).get(key)
    if update:
        patched["raw_front"] = update.get("raw_front", patched.get("raw_front", ""))
        patched["raw_back"] = update.get("raw_back", patched.get("raw_back", ""))
        patched["term"] = patched["raw_front"]
        patched["meaning"] = patched["raw_back"]
        patched["manual_review"] = True
        patched["semantic_review"] = "manual"
    return patched


def record_catalog_update(item: dict, raw_front: str, raw_back: str, before: dict) -> dict | None:
    key = memory_catalog_patch_key(item)
    if not key or key == "item_id:":
        return None
    now = time.time()
    patch = catalog_patch_db()
    event = {
        "at": now,
        "label": time.strftime("%Y-%m-%d %H:%M"),
        "type": "catalog_flashcard_update",
        "patch_key": key,
        "item_id": item.get("id"),
        "deck": item.get("deck"),
        "before": before,
        "after": {"raw_front": raw_front, "raw_back": raw_back},
    }
    patch.setdefault("updates", {})[key] = {
        "raw_front": raw_front,
        "raw_back": raw_back,
        "deck": item.get("deck"),
        "updated_at": now,
        "updated_label": event["label"],
        "item_id": item.get("id"),
    }
    patch.setdefault("deleted", {}).pop(key, None)
    patch.setdefault("events", []).append(event)
    write_catalog_patch_db(patch)
    return event


def record_catalog_delete(item: dict) -> dict | None:
    key = memory_catalog_patch_key(item)
    if not key or key == "item_id:":
        return None
    now = time.time()
    patch = catalog_patch_db()
    event = {
        "at": now,
        "label": time.strftime("%Y-%m-%d %H:%M"),
        "type": "catalog_flashcard_delete",
        "patch_key": key,
        "item_id": item.get("id"),
        "deck": item.get("deck"),
        "raw_front": item.get("raw_front", item.get("term", "")),
        "raw_back": item.get("raw_back", item.get("meaning", "")),
    }
    patch.setdefault("updates", {}).pop(key, None)
    patch.setdefault("deleted", {})[key] = event
    patch.setdefault("events", []).append(event)
    write_catalog_patch_db(patch)
    return event


def memory_slug(term: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")[:36]
    return base or "item"


def next_memory_id(items: list[dict], term: str) -> str:
    base = f"mem_{time.strftime('%Y%m%d')}_{memory_slug(term)}"
    existing = {str(item.get("id")) for item in items}
    if base not in existing:
        return base
    counter = 2
    while f"{base}_{counter}" in existing:
        counter += 1
    return f"{base}_{counter}"


def strip_hebrew_niqqud(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_hebrew_marks = HEBREW_MARKS_RE.sub("", decomposed)
    without_combining = "".join(
        ch for ch in without_hebrew_marks if not (unicodedata.combining(ch) and "\u0590" <= ch <= "\u05ff")
    )
    return unicodedata.normalize("NFC", without_combining)


def memory_sort_key(item: dict) -> tuple[float, int, str, int, str]:
    deck = str(item.get("deck") or item.get("context") or "")
    try:
        source_row = int(item.get("source_row") or 0)
    except (TypeError, ValueError):
        source_row = 0
    return (
        float(item.get("next_due_at") or 0),
        int(item.get("study_position") or 999999),
        deck.lower(),
        source_row,
        str(item.get("term") or item.get("raw_front") or ""),
    )


def parse_quizlet_export(raw_text: str) -> list[dict]:
    rows: list[dict] = []
    for raw_line in (raw_text or "").splitlines():
        line = raw_line.strip("\r\n")
        if not line.strip():
            continue
        if "\t" in line:
            front, back = line.split("\t", 1)
            delimiter = "tab"
        elif ";" in line:
            front, back = line.split(";", 1)
            delimiter = "semicolon"
        elif "," in line:
            front, back = line.split(",", 1)
            delimiter = "comma"
        else:
            front, back = line, ""
            delimiter = "single"
        rows.append(
            {
                "raw_line": raw_flashcard_text(line, 8000),
                "raw_front_original": raw_flashcard_text(front, 1000),
                "raw_back_original": raw_flashcard_text(back, 3000),
                "raw_front": raw_flashcard_text(strip_hebrew_niqqud(front), 1000),
                "raw_back": raw_flashcard_text(strip_hebrew_niqqud(back), 3000),
                "delimiter": delimiter,
            }
        )
    return rows


def memory_item_score(item: dict) -> float:
    events = item.get("events") or []
    if not events:
        return float(item.get("depth_score") or 8)
    recent = events[-6:]
    points = 10.0
    correct = sum(1 for event in recent if event.get("result") == "correct")
    partial = sum(1 for event in recent if event.get("result") == "partial")
    misses = sum(1 for event in recent if event.get("result") == "miss")
    avg_confidence = sum(float(event.get("confidence") or 0) for event in recent) / len(recent)
    avg_effort = sum(float(event.get("effort") or 0) for event in recent) / len(recent)
    avg_latency = sum(float(event.get("latency_s") or 0) for event in recent) / len(recent)
    interval_days = float(item.get("interval_days") or 0)
    points += correct * 14 + partial * 7 - misses * 10
    points += avg_confidence * 4.0
    points -= avg_effort * 2.2
    points -= min(avg_latency, 30) * 0.45
    points += min(interval_days, 30) * 1.1
    points += min(int(item.get("recall_count") or 0), 12) * 2.0
    return round(max(0, min(100, points)), 1)


def memory_next_due_label(next_due_at: float | int | None) -> str:
    if not next_due_at:
        return "oggi"
    delta = float(next_due_at) - time.time()
    if delta <= 0:
        return "oggi"
    hours = delta / 3600
    if hours < 24:
        return f"tra {max(1, round(hours))}h"
    return f"tra {max(1, round(hours / 24))}g"


def normalize_memory_item(item: dict) -> dict:
    item["depth_score"] = memory_item_score(item)
    item["next_due_label"] = memory_next_due_label(item.get("next_due_at"))
    return item


FLASHCARD_BLOCKING_QUALITY_FLAGS = {
    "empty_back",
    "empty_front",
    "back_contains_hebrew",
    "mojibake_or_extraction_symbol",
    "suspicious_translation_payload",
    "back_too_short",
    "front_contains_latin",
}


def is_study_ready_flashcard(item: dict) -> bool:
    if item.get("study_ready", True) is False:
        return False
    flags = item.get("quality_flags") or []
    if isinstance(flags, str):
        flags = [flag.strip() for flag in flags.split("|") if flag.strip()]
    if FLASHCARD_BLOCKING_QUALITY_FLAGS.intersection(set(flags)):
        return False
    front = str(item.get("raw_front") or item.get("term") or "")
    back = str(item.get("raw_back") or item.get("meaning") or "")
    if "�" in front or "�" in back or "₪" in front or "₪" in back:
        return False
    return True


def memory_state() -> dict:
    payload = memory_db()
    items = [
        normalize_memory_item(dict(item))
        for item in payload.get("items", [])
        if is_study_ready_flashcard(item)
    ]
    now = time.time()
    items.sort(key=memory_sort_key)
    due = [item for item in items if float(item.get("next_due_at") or 0) <= now]
    decks = sorted(
        {str(item.get("deck") or item.get("context") or "").strip() for item in items if str(item.get("deck") or item.get("context") or "").strip()},
        key=lambda deck: deck.lower(),
    )
    return {
        "total": len(items),
        "due": due,
        "items": items,
        "decks": decks,
        "events": len(payload.get("events", [])),
    }


def memory_save_item(params: dict) -> dict:
    term = safe_memory_text(str(params.get("term", "")), 120)
    if not term:
        raise ValueError("inserisci una parola o un concetto")
    meaning = safe_memory_text(str(params.get("meaning", "")), 180)
    context = safe_memory_text(str(params.get("context", "")), 220)
    payload = memory_db()
    items = payload["items"]
    item_id = safe_memory_text(str(params.get("item_id", "")), 80)
    item = None
    if item_id:
        item = next((candidate for candidate in items if candidate.get("id") == item_id), None)
    if item is None:
        folded = term.casefold()
        item = next((candidate for candidate in items if str(candidate.get("term", "")).casefold() == folded), None)
    now = time.time()
    if item is None:
        item = {
            "id": next_memory_id(items, term),
            "term": term,
            "meaning": meaning,
            "context": context,
            "created_at": now,
            "created_label": time.strftime("%Y-%m-%d %H:%M"),
            "next_due_at": now + 24 * 3600,
            "interval_days": 1.0,
            "recall_count": 0,
            "events": [],
        }
        items.append(item)
    else:
        item["term"] = term
        item["meaning"] = meaning
        item["context"] = context
        item["updated_at"] = now
    item = normalize_memory_item(item)
    write_memory_db(payload)
    return {"item": item, "memory": memory_state()}


def memory_update_item(params: dict) -> dict:
    item_id = safe_memory_text(str(params.get("item_id", "")), 100)
    if not item_id:
        raise ValueError("item memoria non indicato")
    raw_front = raw_flashcard_text(strip_hebrew_niqqud(str(params.get("raw_front", ""))), 2000)
    raw_back = raw_flashcard_text(str(params.get("raw_back", "")), 5000)
    if not raw_front or not raw_back:
        raise ValueError("fronte e retro non possono essere vuoti")
    payload = memory_db()
    item = next((candidate for candidate in payload["items"] if candidate.get("id") == item_id), None)
    if item is None:
        raise ValueError("item memoria non trovato")
    now = time.time()
    before = {
        "raw_front": item.get("raw_front", item.get("term", "")),
        "raw_back": item.get("raw_back", item.get("meaning", "")),
    }
    item["term"] = raw_front
    item["meaning"] = raw_back
    item["raw_front"] = raw_front
    item["raw_back"] = raw_back
    item.setdefault("raw_front_original", before["raw_front"])
    item.setdefault("raw_back_original", before["raw_back"])
    item["updated_at"] = now
    item["updated_label"] = time.strftime("%Y-%m-%d %H:%M")
    item["manual_review"] = True
    item["semantic_review"] = "manual"
    catalog_event = record_catalog_update(item, raw_front, raw_back, before)
    event = {
        "at": now,
        "label": item["updated_label"],
        "type": "manual_flashcard_update",
        "item_id": item_id,
        "before": before,
        "after": {"raw_front": raw_front, "raw_back": raw_back},
        "catalog_patch": catalog_event,
    }
    payload.setdefault("events", []).append(event)
    item.setdefault("edit_events", []).append(event)
    item = normalize_memory_item(item)
    write_memory_db(payload)
    return {"item": item, "event": event, "memory": memory_state()}


def memory_delete_item(params: dict) -> dict:
    item_id = safe_memory_text(str(params.get("item_id", "")), 100)
    if not item_id:
        raise ValueError("item memoria non indicato")
    payload = memory_db()
    items = payload.get("items", [])
    item = next((candidate for candidate in items if candidate.get("id") == item_id), None)
    if item is None:
        raise ValueError("item memoria non trovato")
    payload["items"] = [candidate for candidate in items if candidate.get("id") != item_id]
    now = time.time()
    event = {
        "at": now,
        "label": time.strftime("%Y-%m-%d %H:%M"),
        "type": "manual_flashcard_delete",
        "item_id": item_id,
        "deck": item.get("deck"),
        "raw_front": item.get("raw_front", item.get("term", "")),
        "raw_back": item.get("raw_back", item.get("meaning", "")),
    }
    catalog_event = record_catalog_delete(item)
    event["catalog_patch"] = catalog_event
    payload.setdefault("events", []).append(event)
    payload.setdefault("deleted_items", []).append(event)
    write_memory_db(payload)
    return {"deleted": item_id, "event": event, "memory": memory_state()}


def memory_add_flashcard(params: dict) -> dict:
    deck = raw_flashcard_text(str(params.get("deck", "")), 220)
    raw_front = raw_flashcard_text(strip_hebrew_niqqud(str(params.get("raw_front", ""))), 2000)
    raw_back = raw_flashcard_text(str(params.get("raw_back", "")), 5000)
    if not deck:
        raise ValueError("seleziona un solo mazzo")
    if not raw_front or not raw_back:
        raise ValueError("ebraico e traduzione non possono essere vuoti")
    payload = memory_db()
    items = payload["items"]
    duplicate = next(
        (
            item for item in items
            if str(item.get("deck") or item.get("context") or "") == deck
            and str(item.get("raw_front") or item.get("term") or "") == raw_front
        ),
        None,
    )
    if duplicate is not None:
        raise ValueError("questa carta esiste gia nel mazzo")
    max_position = max(
        [int(item.get("study_position") or 0) for item in items if str(item.get("deck") or item.get("context") or "") == deck] or [0]
    )
    now = time.time()
    item = {
        "id": next_memory_id(items, raw_front),
        "deck": deck,
        "term": raw_front,
        "meaning": raw_back,
        "context": deck,
        "raw_front": raw_front,
        "raw_back": raw_back,
        "raw_front_original": raw_front,
        "raw_back_original": raw_back,
        "source": "manual_flashcard",
        "study_position": max_position + 1,
        "manual_review": True,
        "semantic_review": "manual",
        "created_at": now,
        "created_label": time.strftime("%Y-%m-%d %H:%M"),
        "next_due_at": now,
        "interval_days": 0.0,
        "recall_count": 0,
        "events": [],
    }
    items.append(item)
    event = {
        "at": now,
        "label": item["created_label"],
        "type": "manual_flashcard_add",
        "item_id": item["id"],
        "deck": deck,
        "raw_front": raw_front,
        "raw_back": raw_back,
    }
    item["events"].append(event)
    payload.setdefault("events", []).append(event)
    item = normalize_memory_item(item)
    write_memory_db(payload)
    return {"item": item, "event": event, "memory": memory_state()}


def memory_import_flashcards(params: dict) -> dict:
    deck = raw_flashcard_text(str(params.get("deck", "")), 180) or "Ebraico moderno"
    raw_text = str(params.get("raw_text", "") or "")
    rows = parse_quizlet_export(raw_text)
    if not rows:
        raise ValueError("nessuna flashcard importabile")
    payload = memory_db()
    items = payload["items"]
    existing = {
        (
            str(item.get("deck", "")),
            str(item.get("raw_front", item.get("term", ""))),
            str(item.get("raw_back", item.get("meaning", ""))),
        )
        for item in items
    }
    imported = []
    skipped = 0
    now = time.time()
    for row in rows:
        key = (deck, row["raw_front"], row["raw_back"])
        if key in existing:
            skipped += 1
            continue
        term = row["raw_front"]
        item = {
            "id": next_memory_id(items, term or deck),
            "deck": deck,
            "term": term,
            "meaning": row["raw_back"],
            "context": deck,
            "raw_front": row["raw_front"],
            "raw_back": row["raw_back"],
            "raw_front_original": row.get("raw_front_original", row["raw_front"]),
            "raw_back_original": row.get("raw_back_original", row["raw_back"]),
            "raw_line": row["raw_line"],
            "raw_delimiter": row["delimiter"],
            "source": "quizlet_export_raw",
            "created_at": now,
            "created_label": time.strftime("%Y-%m-%d %H:%M"),
            "next_due_at": now,
            "interval_days": 0.0,
            "recall_count": 0,
            "events": [],
        }
        items.append(item)
        existing.add(key)
        imported.append(normalize_memory_item(item))
    payload.setdefault("imports", []).append(
        {
            "at": now,
            "label": time.strftime("%Y-%m-%d %H:%M"),
            "deck": deck,
            "rows": len(rows),
            "imported": len(imported),
            "skipped": skipped,
            "source": "quizlet_export_raw",
        }
    )
    write_memory_db(payload)
    return {"imported": len(imported), "skipped": skipped, "deck": deck, "items": imported[:20], "memory": memory_state()}


def seed_catalog() -> dict:
    """Return an empty catalog: bundled commercial-course seed files have been removed."""
    return {"colors": [], "decks": [], "total_cards": 0, "source_counts": {}}


def memory_auto_import_seed(only_if_empty: bool = True, params: dict | None = None) -> dict:
    """Bundled seed import is disabled; only manual flashcards and imports are supported."""
    payload = memory_db()
    if only_if_empty and payload.get("items"):
        return {"imported": 0, "skipped": len(payload.get("items", [])), "reason": "memory_not_empty"}
    return {"imported": 0, "skipped": 0, "reason": "bundled_seed_removed"}


def append_flashcard_eeg_event(event: dict) -> dict | None:
    status = mac_status()
    phase = str(status.get("phase") or "")
    csv = str(status.get("csv") or "")
    if phase not in {"prep", "recording"} or not csv:
        return None
    csv_path = Path(csv).resolve()
    sessions_root = MAC_SESSIONS.resolve()
    if sessions_root not in csv_path.parents or not csv_path.name.startswith("session_"):
        return None
    sidecar = csv_path.with_suffix(".flashcards.jsonl")
    summary = csv_path.with_suffix(".flashcards.json")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "type": "flashcard_recall",
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "eeg_phase": phase,
        "condition": status.get("condition"),
        "csv": csv_path.name,
        **event,
    }
    with sidecar.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    counts = {"correct": 0, "partial": 0, "miss": 0}
    selected_decks: set[str] = set()
    events = 0
    try:
        for line in sidecar.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events += 1
            payload = json.loads(line)
            result = str(payload.get("result") or "")
            if result in counts:
                counts[result] += 1
            for deck in payload.get("selected_decks") or []:
                if deck:
                    selected_decks.add(str(deck))
    except Exception:
        pass
    summary.write_text(
        json.dumps(
            {
                "type": "flashcard_eeg_annotations",
                "csv": csv_path.name,
                "events": events,
                "score": counts,
                "selected_decks": sorted(selected_decks),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"jsonl": sidecar.name, "summary": summary.name, "phase": phase}


def session_covariates_from_state() -> dict:
    state = read_mac_state()
    return state.get("session_covariates") if isinstance(state.get("session_covariates"), dict) else {}


def write_session_manifest(csv_path: Path, study_context: dict | None = None) -> Path | None:
    manifest_path = csv_path.with_suffix(".manifest.json")
    if manifest_path.exists():
        return manifest_path
    covariates = session_covariates_from_state()
    session_id = csv_path.stem
    manifest = {
        "schema_version": "mindtune_session_manifest_v2",
        "session_id": session_id,
        "csv": csv_path.name,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "principle": "Outcome first. State contextualizes. Biomarkers qualify confidence but never override observed performance.",
        "covariates": covariates,
        "study_context": study_context or {},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def append_task_eeg_event(params: dict) -> dict:
    status = mac_status()
    phase = str(status.get("phase") or "")
    csv = str(status.get("csv") or "")
    if phase not in {"prep", "recording"} or not csv:
        return {"recorded": False, "reason": "nessuna registrazione EEG attiva"}
    csv_path = Path(csv).resolve()
    sessions_root = MAC_SESSIONS.resolve()
    if sessions_root not in csv_path.parents or not csv_path.name.startswith("session_"):
        return {"recorded": False, "reason": "sessione EEG non valida"}

    write_session_manifest(csv_path, params.get("study_context") if isinstance(params.get("study_context"), dict) else {})

    sidecar = csv_path.with_suffix(".events.jsonl")
    summary = csv_path.with_suffix(".events.json")
    annotation_type = str(params.get("annotation_type") or "task_event")[:80]
    event = params.get("event") if isinstance(params.get("event"), dict) else {}
    study_context = params.get("study_context") if isinstance(params.get("study_context"), dict) else {}
    event_id = task_event_id(params)
    behavioral_session_id = safe_behavioral_session_id(params)
    if jsonl_contains_event(sidecar, event_id):
        return {
            "recorded": True,
            "deduplicated": True,
            "event_id": event_id,
            "jsonl": sidecar.name,
            "summary": summary.name,
            "phase": phase,
            "storage": "eeg_sidecar",
        }
    row = {
        "schema_version": "mindtune_behavioral_event_v1",
        "behavioral_event_id": event_id,
        "behavioral_session_id": behavioral_session_id,
        "type": annotation_type,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "eeg_phase": phase,
        "condition": status.get("condition"),
        "csv": csv_path.name,
        "event": event,
        "study_context": study_context,
    }
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with sidecar.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    counts: dict[str, int] = {}
    score = {"ok": 0, "miss": 0, "timeout": 0}
    events = 0
    try:
        for line in sidecar.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            events += 1
            item_type = str(payload.get("type") or "task_event")
            counts[item_type] = counts.get(item_type, 0) + 1
            payload_event = payload.get("event") if isinstance(payload.get("event"), dict) else {}
            if payload_event.get("timeout"):
                score["timeout"] += 1
            correct = payload_event.get("correct")
            if correct is None:
                correct = payload_event.get("is_correct")
            if correct is True or payload_event.get("ok") is True:
                score["ok"] += 1
            elif correct is False or payload_event.get("ok") is False:
                score["miss"] += 1
    except Exception:
        pass
    summary.write_text(
        json.dumps(
            {
                "type": "mindtune_behavioral_eeg_annotations",
                "csv": csv_path.name,
                "events": events,
                "event_types": counts,
                "score": score,
                "condition": status.get("condition"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "recorded": True,
        "deduplicated": False,
        "event_id": event_id,
        "jsonl": sidecar.name,
        "summary": summary.name,
        "phase": phase,
        "storage": "eeg_sidecar",
    }


def safe_behavioral_session_id(params: dict) -> str:
    raw = str(params.get("behavioral_session_id") or "").strip()
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)[:140].strip("._-")
    if value:
        return value
    return f"behavioral_{time.strftime('%Y%m%d_%H%M%S')}"


def task_event_id(params: dict) -> str:
    event = params.get("event") if isinstance(params.get("event"), dict) else {}
    supplied = str(event.get("event_id") or params.get("event_id") or "").strip()
    if supplied:
        return supplied[:160]
    identity = {
        "session": safe_behavioral_session_id(params),
        "type": str(params.get("annotation_type") or "task_event"),
        "event": event,
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(uuid5(NAMESPACE_DNS, f"mindtune-lab:behavioral-event:{encoded}"))


def jsonl_contains_event(path: Path, event_id: str) -> bool:
    if not event_id or not path.exists():
        return False
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row_event = row.get("event") if isinstance(row.get("event"), dict) else {}
            if str(row.get("behavioral_event_id") or row_event.get("event_id") or "") == event_id:
                return True
    except (OSError, json.JSONDecodeError, TypeError):
        return False
    return False


def append_local_behavioral_event(params: dict, eeg_reason: str = "") -> dict:
    session_id = safe_behavioral_session_id(params)
    event_id = task_event_id(params)
    BEHAVIORAL_EVENTS.mkdir(parents=True, exist_ok=True)
    sidecar = BEHAVIORAL_EVENTS / f"{session_id}.events.jsonl"
    if jsonl_contains_event(sidecar, event_id):
        return {
            "recorded": True,
            "deduplicated": True,
            "event_id": event_id,
            "jsonl": sidecar.name,
            "phase": "behavioral_only",
            "storage": "local_behavioral",
        }
    event = params.get("event") if isinstance(params.get("event"), dict) else {}
    row = {
        "schema_version": "mindtune_behavioral_event_v1",
        "behavioral_event_id": event_id,
        "behavioral_session_id": session_id,
        "type": str(params.get("annotation_type") or "task_event")[:80],
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "capture_mode": "behavioral_only",
        "eeg_phase": "none",
        "eeg_unavailable_reason": str(eeg_reason or "nessuna registrazione EEG attiva")[:160],
        "event": event,
        "study_context": params.get("study_context") if isinstance(params.get("study_context"), dict) else {},
    }
    with sidecar.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "recorded": True,
        "deduplicated": False,
        "event_id": event_id,
        "jsonl": sidecar.name,
        "phase": "behavioral_only",
        "storage": "local_behavioral",
    }


def append_task_event(params: dict) -> dict:
    eeg_result = append_task_eeg_event(params)
    if eeg_result.get("recorded"):
        return eeg_result
    if params.get("persist_without_eeg") is True:
        return append_local_behavioral_event(params, str(eeg_result.get("reason") or ""))
    return eeg_result


def save_training_session(params: dict) -> dict:
    ensure_mac_dirs()
    raw_session_id = str(params.get("session_id") or f"task_{time.strftime('%Y%m%d_%H%M%S')}")
    session_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw_session_id)[:140].strip("._-")
    if not session_id:
        session_id = f"task_{time.strftime('%Y%m%d_%H%M%S')}"
    session_dir = (MINDTUNE_SESSIONS / session_id).resolve()
    sessions_root = MINDTUNE_SESSIONS.resolve()
    if sessions_root not in session_dir.parents:
        raise ValueError("sessione training non valida")
    session_dir.mkdir(parents=True, exist_ok=True)

    events = params.get("events") if isinstance(params.get("events"), list) else []
    safe_events = []
    for event in events[:5000]:
        if isinstance(event, dict):
            safe_events.append(event)

    score = params.get("score") if isinstance(params.get("score"), dict) else {}
    context = params.get("context") if isinstance(params.get("context"), dict) else {}
    covariates = params.get("covariates") if isinstance(params.get("covariates"), dict) else {}
    started_ms = float(params.get("started_at_ms") or 0)
    ended_ms = float(params.get("ended_at_ms") or int(time.time() * 1000))
    duration_s = max(0.0, (ended_ms - started_ms) / 1000.0) if started_ms else 0.0
    correct = int(score.get("ok") or 0)
    miss = int(score.get("miss") or 0)
    false_start = int(score.get("falseStart") or score.get("false_start") or 0)
    total_scored = correct + miss + false_start
    accuracy = correct / total_scored if total_scored else None

    payload = {
        "schema_version": "mindtune_training_session_v1",
        "session_id": session_id,
        "session_type": "training_lab",
        "reason": safe_memory_text(str(params.get("reason") or "stop"), 80),
        "label": safe_memory_text(str(params.get("label") or context.get("task_label") or "Training Lab"), 160),
        "condition": safe_memory_text(str(params.get("condition") or context.get("task_id") or "training_lab"), 160),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "started_at_ms": started_ms,
        "ended_at_ms": ended_ms,
        "duration_s": round(duration_s, 3),
        "eeg_linked": bool(params.get("eeg_linked")),
        "score": score,
        "accuracy": None if accuracy is None else round(accuracy, 4),
        "event_count": len(safe_events),
        "context": context,
        "covariates": covariates,
        "events": safe_events,
        "export_paths": {
            "session_json": str(session_dir / "session.json"),
            "events_jsonl": str(session_dir / "events.jsonl"),
        },
    }

    (session_dir / "session.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with (session_dir / "events.jsonl").open("w", encoding="utf-8") as handle:
        for event in safe_events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "session_id": session_id,
        "saved": True,
        "path": str(session_dir / "session.json"),
        "event_count": len(safe_events),
        "accuracy": payload["accuracy"],
    }


def memory_log_recall(params: dict) -> dict:
    item_id = safe_memory_text(str(params.get("item_id", "")), 100)
    term = safe_memory_text(str(params.get("term", "")), 120)
    if not item_id and term:
        saved = memory_save_item(params)
        item_id = saved["item"]["id"]
    payload = memory_db()
    item = next((candidate for candidate in payload["items"] if candidate.get("id") == item_id), None)
    if item is None:
        raise ValueError("item memoria non trovato")
    result = str(params.get("result", "correct"))
    if result not in {"correct", "partial", "miss"}:
        raise ValueError("esito recall non valido")
    confidence = as_int(params.get("confidence"), 5, 0, 10)
    effort = as_int(params.get("effort"), 5, 0, 10)
    latency_s = as_float(params.get("latency_s"), 0.0, 0.0, 120.0)
    review_s = as_float(params.get("review_s"), 0.0, 0.0, 600.0)
    selected_decks = [
        raw_flashcard_text(str(value), 220)
        for value in (params.get("selected_decks") or [])
        if raw_flashcard_text(str(value), 220)
    ][:24]
    study_context = params.get("study_context") if isinstance(params.get("study_context"), dict) else {}
    help_evidence = params.get("help_evidence") if isinstance(params.get("help_evidence"), dict) else None
    now = time.time()
    previous_interval = float(item.get("interval_days") or 1.0)
    if result == "correct":
        interval = min(30.0, max(1.0, previous_interval * (1.75 if confidence >= 7 and effort <= 5 else 1.35)))
    elif result == "partial":
        interval = max(1.0, previous_interval * 0.75)
    else:
        interval = 0.25
    event = {
        "at": now,
        "label": time.strftime("%Y-%m-%d %H:%M"),
        "item_id": item["id"],
        "term": item.get("term"),
        "result": result,
        "confidence": confidence,
        "effort": effort,
        "latency_s": latency_s,
        "review_s": review_s,
        "deck": item.get("deck") or item.get("context") or raw_flashcard_text(str(params.get("deck", "")), 220),
        "selected_decks": selected_decks,
        "front": raw_flashcard_text(str(params.get("front") or item.get("raw_front") or item.get("term") or ""), 2000),
        "back": raw_flashcard_text(str(params.get("back") or item.get("raw_back") or item.get("meaning") or ""), 5000),
        "study_context": study_context,
        "help_evidence": help_evidence,
        "interval_before_days": previous_interval,
        "interval_after_days": round(interval, 2),
    }
    eeg_annotation = append_flashcard_eeg_event(event)
    if eeg_annotation:
        event["eeg_annotation"] = eeg_annotation
    item.setdefault("events", []).append(event)
    item["last_result"] = result
    item["last_recall_at"] = now
    item["last_recall_label"] = event["label"]
    item["interval_days"] = round(interval, 2)
    item["next_due_at"] = now + interval * 86400
    item["recall_count"] = int(item.get("recall_count") or 0) + 1
    item = normalize_memory_item(item)
    payload.setdefault("events", []).append(event)
    write_memory_db(payload)
    return {"item": item, "event": event, "memory": memory_state()}


def list_jobs() -> list[dict]:
    items: list[dict] = []
    for status, directory in (
        ("queued", INBOX),
        ("running", RUNNING),
        ("done", DONE),
        ("failed", FAILED),
    ):
        if not directory.exists():
            continue
        for path in directory.glob("*.sh"):
            stat = path.stat()
            log_name = path.with_suffix(".log").name
            log_path = LOGS / log_name
            items.append(
                {
                    "name": path.name,
                    "status": status,
                    "mtime": stat.st_mtime,
                    "mtime_label": time.strftime("%H:%M:%S", time.localtime(stat.st_mtime)),
                    "log": log_name if log_path.exists() else None,
                }
            )
    items.sort(key=lambda item: item["mtime"], reverse=True)
    return items[:80]


def list_logs() -> list[dict]:
    items = []
    for source, directory in (("mac", MAC_LOGS), ("raspberry", LOGS)):
        if not directory.exists():
            continue
        for path in directory.glob("*.log"):
            stat = path.stat()
            items.append(
                {
                    "id": f"{source}/{path.name}",
                    "name": path.name,
                    "source": source,
                    "mtime": stat.st_mtime,
                    "mtime_label": time.strftime("%H:%M:%S", time.localtime(stat.st_mtime)),
                    "size": stat.st_size,
                }
            )
    items.sort(key=lambda item: item["mtime"], reverse=True)
    return items[:80]


def log_path_from_id(log_id: str) -> Path | None:
    log_id = (log_id or "").strip()
    if "/" not in log_id:
        candidate = Path(log_id).name
        for directory in (MAC_LOGS, LOGS):
            path = directory / candidate
            if path.exists():
                return path
        return None
    source, name = log_id.split("/", 1)
    name = Path(name).name
    if source == "mac":
        return MAC_LOGS / name
    if source == "raspberry":
        return LOGS / name
    return None


def bridge_running() -> dict:
    try:
        result = subprocess.run(
            ["pgrep", "-af", "raspberry_command_bridge.sh"],
            text=True,
            capture_output=True,
            timeout=2,
        )
    except Exception as exc:
        return {"running": False, "detail": repr(exc)}
    lines = [line for line in result.stdout.splitlines() if "pgrep" not in line]
    return {"running": bool(lines), "detail": "\n".join(lines[:5])}


def as_int(value, default: int, lo: int, hi: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(lo, min(hi, number))


def validate_condition(value: str) -> str:
    value = (value or "").strip()
    if not CONDITION_RE.match(value):
        raise ValueError("condizione non valida")
    return value


def optional_piece_id(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if not PIECE_RE.match(value):
        raise ValueError("piece_id non valido")
    return value


def safe_note(value: str, max_len: int = 180) -> str:
    value = " ".join((value or "").strip().split())
    return value[:max_len]


def safe_memory_text(value: str, max_len: int = 240) -> str:
    value = " ".join((value or "").strip().split())
    return value[:max_len]


def raw_flashcard_text(value: str, max_len: int = 4000) -> str:
    value = (value or "").replace("\x00", "").strip("\r\n")
    return value[:max_len]


def as_float(value, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def quote(value: str | int) -> str:
    return shlex.quote(str(value))


def job_script(action: str, params: dict) -> str:
    header = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'echo "== MindTune console: {action} =="',
        'date -Is',
        "",
    ]

    if action == "ble_preflight":
        scan = as_int(params.get("scan_seconds"), 10, 1, 60)
        smoke = as_int(params.get("smoke_seconds"), 12, 0, 60)
        body = [
            "/mnt/biohacking/home/mindtune/bin/mindtune_ble_preflight \\",
            f"  --scan-seconds {scan} \\",
            f"  --smoke-seconds {smoke}",
        ]
    elif action == "brainlab_preflight":
        condition = str(params.get("condition", ""))
        protocol = (
            "/mnt/biohacking/home/brainlab/brainlab/protocols/piano_lab_20min.json"
            if condition == "piano_lab_20min"
            else "/mnt/biohacking/home/brainlab/brainlab/protocols/standard_mindtune_10min.json"
        )
        body = [
            "cd /mnt/biohacking/home/brainlab",
            "/home/idonokurasani/mindtune/bin/python -m brainlab.cli preflight \\",
            "  --db /mnt/biohacking/sqlite/brainlab.db \\",
            "  --health-db /mnt/biohacking/sqlite/health_data.db \\",
            f"  --protocol {quote(protocol)} \\",
            "  --output /mnt/biohacking/home/brainlab/output",
        ]
    elif action == "start_recording":
        condition = validate_condition(str(params.get("condition", "eyes_open")))
        duration = as_int(params.get("duration"), 120, 5, 7200)
        prep = as_int(params.get("prep"), 20, 0, 600)
        guided = bool(params.get("guided", True))
        piece_id = optional_piece_id(str(params.get("piece_id", "")))
        difficulty = as_int(params.get("difficulty"), 0, 0, 10)
        session_note = safe_note(str(params.get("session_note", "")))
        session_covariates = params.get("session_covariates") if isinstance(params.get("session_covariates"), dict) else {}
        command = [
            "/mnt/biohacking/home/mindtune/bin/mindtune_record_start",
            "--condition",
            quote(condition),
            "--duration",
            str(duration),
            "--prep",
            str(prep),
        ]
        if guided:
            command.append("--guided")
        body = [
            'echo "== session metadata =="',
            f'echo "condition={quote(condition)}"',
            f'echo "piece_id={quote(piece_id)}"',
            f'echo "difficulty={difficulty}"',
            f'echo "session_note={quote(session_note)}"',
            f'echo "session_covariates={quote(json.dumps(session_covariates, ensure_ascii=False))}"',
            "",
            " ".join(command),
        ]
    elif action == "record_status":
        body = ["/mnt/biohacking/home/mindtune/bin/mindtune_record_status"]
    elif action == "record_tail":
        lines = as_int(params.get("lines"), 120, 20, 500)
        body = [f"/mnt/biohacking/home/mindtune/bin/mindtune_record_tail {lines}"]
    elif action == "record_stop":
        body = ["/mnt/biohacking/home/mindtune/bin/mindtune_record_stop"]
    elif action == "latest_csv":
        body = [
            'echo "== latest calibration CSV =="',
            "find /mnt/biohacking/home/mindtune/calibration -maxdepth 1 -type f -name 'session_*.csv' "
            "-printf '%TY-%Tm-%Td %TH:%TM:%TS %10s %p\\n' 2>/dev/null | sort -r | head -20",
        ]
    elif action == "raspberry_ping":
        body = [
            "hostname",
            "test -d /mnt/biohacking && echo MOUNT_OK",
            "test -x /mnt/biohacking/home/mindtune/bin/mindtune_ble_preflight && echo MINDTUNE_TOOLS_OK",
        ]
    elif action == "dry_run_readiness":
        body = [
            'echo "== mount =="',
            "test -d /mnt/biohacking && echo MOUNT_OK",
            "df -h /mnt/biohacking | tail -1",
            "",
            'echo "== MindTune tools =="',
            "test -x /mnt/biohacking/home/mindtune/bin/mindtune_ble_preflight && echo BLE_PREFLIGHT_OK",
            "test -x /mnt/biohacking/home/mindtune/bin/mindtune_record_start && echo RECORD_START_OK",
            "test -x /mnt/biohacking/home/mindtune/bin/mindtune_record_status && echo RECORD_STATUS_OK",
            "test -f /mnt/biohacking/home/mindtune/scripts/active/fc11_record_session.py && echo RECORDER_OK",
            "test -f /mnt/biohacking/home/mindtune/scripts/active/fc11_record_session_guided.py && echo GUIDED_RECORDER_OK",
            "",
            'echo "== active recording =="',
            "/mnt/biohacking/home/mindtune/bin/mindtune_record_status || true",
            "",
            'echo "== Python imports =="',
            "/home/idonokurasani/mindtune/bin/python - <<'PY'",
            "import importlib",
            "for name in ('bleak', 'numpy', 'pandas'):",
            "    try:",
            "        importlib.import_module(name)",
            "        print(f'{name}: OK')",
            "    except Exception as exc:",
            "        print(f'{name}: FAIL {exc!r}')",
            "PY",
            "",
            'echo "== MindTune analytics preflight quick =="',
            "cd /mnt/biohacking/home/brainlab",
            "/home/idonokurasani/mindtune/bin/python -m brainlab.cli preflight \\",
            "  --db /mnt/biohacking/sqlite/brainlab.db \\",
            "  --health-db /mnt/biohacking/sqlite/health_data.db \\",
            "  --protocol /mnt/biohacking/home/brainlab/brainlab/protocols/standard_mindtune_10min.json \\",
            "  --output /mnt/biohacking/home/brainlab/output",
        ]
    else:
        raise ValueError("azione non riconosciuta")

    return "\n".join(header + body + [""])


def enqueue_job(action: str, params: dict) -> dict:
    for directory in (INBOX, RUNNING, DONE, FAILED, LOGS):
        directory.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe_action = re.sub(r"[^A-Za-z0-9_-]+", "_", action)[:48]
    base = f"ui_{stamp}_{safe_action}.sh"
    path = INBOX / base
    counter = 2
    while path.exists():
        base = f"ui_{stamp}_{safe_action}_{counter}.sh"
        path = INBOX / base
        counter += 1
    tmp = path.with_suffix(".tmp")
    tmp.write_text(job_script(action, params), encoding="utf-8")
    os.chmod(tmp, 0o644)
    tmp.replace(path)
    return {"job": base, "log": path.with_suffix(".log").name}


def start_bridge() -> dict:
    current = bridge_running()
    if current["running"]:
        return {"started": False, "message": "bridge gia attivo"}

    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / "local_bridge_from_console.log"
    script = ROOT / "tools" / "raspberry_command_bridge.sh"
    if not script.exists():
        raise ValueError("bridge script non trovato")

    with log_path.open("ab", buffering=0) as log:
        subprocess.Popen(
            [str(script)],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    time.sleep(0.5)
    return {"started": True, "message": "bridge avviato", "log": log_path.name}


def ensure_mac_dirs() -> None:
    migrate_legacy_capture_data()
    MAC_LOGS.mkdir(parents=True, exist_ok=True)
    MAC_SESSIONS.mkdir(parents=True, exist_ok=True)
    MINDTUNE_SESSIONS.mkdir(parents=True, exist_ok=True)
    MAC_RUNTIME.mkdir(parents=True, exist_ok=True)
    MAC_EXPORTS.mkdir(parents=True, exist_ok=True)
    ensure_serious_marker()


def migrate_legacy_capture_data() -> None:
    if not LEGACY_MAC_CAPTURE.exists() or LEGACY_MAC_CAPTURE.resolve() == MAC_CAPTURE:
        return
    for subdir in ("sessions", "mindtune_sessions", "logs", "runtime", "exports"):
        source = LEGACY_MAC_CAPTURE / subdir
        if not source.exists() or not source.is_dir():
            continue
        destination = MAC_CAPTURE / subdir
        destination.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            target = destination / item.name
            if target.exists():
                continue
            try:
                item.replace(target)
            except OSError:
                pass
    for path in sorted(LEGACY_MAC_CAPTURE.glob("**/*"), reverse=True):
        try:
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
        except OSError:
            pass
    try:
        if LEGACY_MAC_CAPTURE.is_dir() and not any(LEGACY_MAC_CAPTURE.iterdir()):
            LEGACY_MAC_CAPTURE.rmdir()
    except OSError:
        pass


def startup_housekeeping() -> None:
    ensure_mac_dirs()
    marker = MAC_RUNTIME / "startup_cleanup_20260629_1650.marker"
    if marker.exists():
        return

    archive_candidates = []
    archive_candidates.extend(sorted(MAC_LOGS.glob("*.log")))
    archive_candidates.extend(sorted(MAC_RUNTIME.glob("handshake_dump_*.jsonl")))
    archive_candidates.extend(sorted(MAC_RUNTIME.glob("mindtune_export_*.sh")))

    if archive_candidates:
        archive = MAC_EXPORTS / f"diagnostic_history_{time.strftime('%Y%m%d_%H%M%S')}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for path in archive_candidates:
                if path.exists() and path.is_file():
                    tar.add(path, arcname=str(path.relative_to(MAC_CAPTURE)))
        for path in archive_candidates:
            try:
                path.unlink()
            except OSError:
                pass

    for path in [MAC_STATE, MAC_STATUS_FILE, MAC_BATTERY_FILE, MAC_START_SIGNAL, MAC_STOP_SIGNAL]:
        try:
            path.unlink()
        except OSError:
            pass

    marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%S%z"), encoding="utf-8")


def one_shot_minisession_cleanup() -> None:
    ensure_mac_dirs()
    marker = MAC_RUNTIME / "cleanup_minisession_20260629_165925.marker"
    if marker.exists():
        return
    targets = [
        MAC_SESSIONS / "session_eyes_open_20260629_165925.csv",
        MAC_SESSIONS / "session_eyes_open_20260629_165925.json",
        MAC_LOGS / "mac_20260629_170031_export_raspberry.log",
        MAC_LOGS / "mac_20260629_170034_export_raspberry.log",
        MAC_RUNTIME / "mindtune_export_20260629_170031.sh",
        MAC_RUNTIME / "mindtune_export_20260629_170034.sh",
    ]
    removed = []
    for path in targets:
        try:
            if path.exists():
                path.unlink()
                removed.append(str(path))
        except OSError:
            pass
    marker.write_text(json.dumps({"removed": removed, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, indent=2), encoding="utf-8")


def ensure_serious_marker() -> Path:
    MAC_RUNTIME.mkdir(parents=True, exist_ok=True)
    marker = MAC_RUNTIME / "serious_data_start.marker"
    if not marker.exists():
        marker.write_text("MindTune Lab serious data start\n", encoding="utf-8")
    try:
        os.utime(marker, (SERIOUS_DATA_START_TS, SERIOUS_DATA_START_TS))
    except OSError:
        pass
    return marker


def mac_export_sessions() -> dict:
    ensure_mac_dirs()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = MAC_LOGS / f"mac_{stamp}_export_raspberry.log"
    script_path = MAC_RUNTIME / f"mindtune_export_{stamp}.sh"
    list_path = MAC_RUNTIME / f"mindtune_export_{stamp}.files"
    bundle_name = f"mindtune_mac_sessions_{stamp}.tar.gz"
    manifest_name = f"mindtune_mac_sessions_{stamp}.manifest.sha256"
    receipt_name = f"mindtune_mac_sessions_{stamp}.receipt.json"
    bundle = MAC_EXPORTS / bundle_name
    manifest = MAC_EXPORTS / manifest_name
    receipt = MAC_EXPORTS / receipt_name
    serious_marker = ensure_serious_marker()
    remote_dir = f"{REMOTE_EXPORT_BASE}/{stamp}"

    script = f"""#!/usr/bin/env bash
set -euo pipefail

ROOT={quote(ROOT)}
CAPTURE={quote(MAC_CAPTURE)}
EXPORTS={quote(MAC_EXPORTS)}
SERIOUS_MARKER={quote(serious_marker)}
BUNDLE={quote(bundle)}
MANIFEST={quote(manifest)}
LIST_FILE={quote(list_path)}
RECEIPT={quote(receipt)}
PYTHON={quote(mac_python())}
BUNDLE_NAME={quote(bundle_name)}
MANIFEST_NAME={quote(manifest_name)}
RECEIPT_NAME={quote(receipt_name)}
HOST="${{MINDTUNE_RPI_HOST:-{DEFAULT_RPI_HOST}}}"
KEY={quote(SSH_KEY)}
REMOTE_DIR={quote(remote_dir)}
REMOTE_INSTALLER={quote(REMOTE_MINDTUNE_INSTALLER)}

echo "== MindTune Mac export -> Raspberry =="
date "+%Y-%m-%dT%H:%M:%S%z"
echo "host=$HOST"
echo "remote_dir=$REMOTE_DIR"
echo

if [ ! -f "$KEY" ]; then
  echo "ERRORE: chiave SSH non trovata: $KEY"
  exit 2
fi

mkdir -p "$EXPORTS"

echo "== registrazioni EEG locali =="
find "$CAPTURE/sessions" "$CAPTURE/mindtune_sessions" -type f -newer "$SERIOUS_MARKER" \\( -path '*/sessions/session_*.csv' -o -path '*/sessions/session_*.json' -o -path '*/sessions/session_*.manifest.json' -o -path '*/sessions/session_*.flashcards.jsonl' -o -path '*/sessions/session_*.events.jsonl' -o -path '*/sessions/session_*.events.json' -o -path '*/mindtune_sessions/*/*' \\) -print 2>/dev/null | sort
echo

(
  cd "$CAPTURE"
  : > "$LIST_FILE"
  find sessions -type f -newer "$SERIOUS_MARKER" \\( -path 'sessions/session_*.csv' -o -path 'sessions/session_*.json' -o -path 'sessions/session_*.manifest.json' -o -path 'sessions/session_*.flashcards.jsonl' -o -path 'sessions/session_*.events.jsonl' -o -path 'sessions/session_*.events.json' \\) -print 2>/dev/null >> "$LIST_FILE" || true
  if [ -d mindtune_sessions ]; then
    find mindtune_sessions -mindepth 1 -maxdepth 1 -type d | while IFS= read -r dir; do
      if [ -f "$dir/samples.csv" ] || [ -f "$dir/packets.csv" ]; then
        find "$dir" -type f -newer "$SERIOUS_MARKER" -print 2>/dev/null
      fi
    done >> "$LIST_FILE"
  fi
  sort -u -o "$LIST_FILE" "$LIST_FILE"
)

session_count="$(grep -c '^sessions/.*\\.csv$' "$LIST_FILE" || true)"
session_count="$(printf "%s" "$session_count" | tr -d ' ')"
v2_count="$(grep -c '^mindtune_sessions/.*/session\\.json$' "$LIST_FILE" || true)"
v2_count="$(printf "%s" "$v2_count" | tr -d ' ')"
if [ "$session_count" = "0" ] && [ "$v2_count" = "0" ]; then
  echo "ERRORE: nessuna registrazione EEG MindTune da esportare"
  echo "Le sessioni gioco/test senza EEG restano sul Mac e non vengono inviate al Raspberry."
  exit 3
fi

echo "== manifesto sha256 =="
(
  cd "$CAPTURE"
  while IFS= read -r file; do
    shasum -a 256 "$file"
  done < "$LIST_FILE"
) > "$MANIFEST"
cat "$MANIFEST"
echo

echo "== creo pacchetto =="
(
  cd "$CAPTURE"
  tar -czf "$BUNDLE" -T "$LIST_FILE"
)
local_size="$(wc -c < "$BUNDLE" | tr -d ' ')"
echo "bundle=$BUNDLE"
echo "local_size=$local_size"
echo

echo "== ricevuta locale preliminare =="
"$PYTHON" - "$RECEIPT" "$REMOTE_DIR" "$BUNDLE_NAME" "$MANIFEST_NAME" "$session_count" "$v2_count" "$local_size" "$LIST_FILE" <<'PY'
import json
import sys
import time
from pathlib import Path

receipt, remote_dir, bundle_name, manifest_name, session_count, v2_count, local_size, list_file = sys.argv[1:]
files = Path(list_file).read_text(encoding="utf-8").splitlines()
payload = {{
    "status": "local_bundle_created_remote_pending",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "remote_dir": remote_dir,
    "bundle": bundle_name,
    "manifest": manifest_name,
    "session_csv_count": int(session_count),
    "mindtune_session_v2_count": int(v2_count),
    "bundle_size_bytes": int(local_size),
    "files": files,
    "local_data_preserved": True,
}}
Path(receipt).write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(Path(receipt))
PY
echo

echo "== verifico raggiungibilita Raspberry =="
if ! ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "$HOST" "echo RPI_REACHABLE"; then
  echo "ERRORE: Raspberry non raggiungibile via SSH o nome .local non risolto."
  echo "Dati locali preservati. Pacchetto pronto per nuovo tentativo:"
  echo "BUNDLE=$BUNDLE"
  echo "MANIFEST=$MANIFEST"
  echo "RECEIPT=$RECEIPT"
  exit 7
fi
echo

echo "== preparo Raspberry =="
ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$HOST" \\
  "mkdir -p '$REMOTE_DIR'"

echo "== aggiorno importatore MindTune Lab =="
if [ -f "$REMOTE_INSTALLER" ]; then
  scp -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new \\
    "$REMOTE_INSTALLER" "$HOST:/tmp/remote_install_mindtune_v2_brainlab.py"
  ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$HOST" \\
    "python3 /tmp/remote_install_mindtune_v2_brainlab.py"
else
  echo "ERRORE: installer MindTune Lab non trovato: $REMOTE_INSTALLER"
  exit 6
fi

echo "== copio pacchetto =="
scp -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new \\
  "$BUNDLE" "$MANIFEST" "$HOST:$REMOTE_DIR/"

remote_size="$(ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$HOST" \\
  "wc -c < '$REMOTE_DIR/$BUNDLE_NAME' | tr -d ' '")"
echo "remote_size=$remote_size"

if [ "$local_size" != "$remote_size" ]; then
  echo "ERRORE: dimensione remota diversa da quella locale"
  exit 4
fi

echo "== estraggo e verifico su Raspberry =="
ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$HOST" \\
  "cd '$REMOTE_DIR' && tar -xzf '$BUNDLE_NAME' && echo REMOTE_EXTRACT_OK && if command -v sha256sum >/dev/null 2>&1; then sha256sum -c '$MANIFEST_NAME'; else shasum -a 256 -c '$MANIFEST_NAME'; fi && remote_csv_count=\\$(find sessions -maxdepth 1 -type f -name 'session_*.csv' 2>/dev/null | wc -l | tr -d ' ') && remote_v2_count=\\$(find mindtune_sessions -mindepth 2 -maxdepth 2 -type f -name 'session.json' 2>/dev/null | wc -l | tr -d ' ') && test \\\"\\$remote_csv_count\\\" = '$session_count' && test \\\"\\$remote_v2_count\\\" = '$v2_count' && echo REMOTE_VERIFY_OK"

echo "== importo in MindTune analytics =="
ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$HOST" \\
  "/mnt/biohacking/home/brainlab/bin/import_mindtune_v2_export.py --latest"

echo "== ricevuta locale =="
"$PYTHON" - "$RECEIPT" "$REMOTE_DIR" "$BUNDLE_NAME" "$MANIFEST_NAME" "$session_count" "$v2_count" "$local_size" "$LIST_FILE" <<'PY'
import json
import sys
import time
from pathlib import Path

receipt, remote_dir, bundle_name, manifest_name, session_count, v2_count, local_size, list_file = sys.argv[1:]
files = Path(list_file).read_text(encoding="utf-8").splitlines()
payload = {{
    "status": "remote_verified",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "remote_dir": remote_dir,
    "bundle": bundle_name,
    "manifest": manifest_name,
    "session_csv_count": int(session_count),
    "mindtune_session_v2_count": int(v2_count),
    "bundle_size_bytes": int(local_size),
    "files": files,
}}
Path(receipt).write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(Path(receipt))
PY

echo "== cancellazione locale post-verifica =="
(
  cd "$CAPTURE"
  while IFS= read -r file; do
    case "$file" in
      sessions/session_*.csv|sessions/session_*.json|sessions/session_*.manifest.json|sessions/session_*.flashcards.jsonl|sessions/session_*.events.jsonl|sessions/session_*.events.json)
        rm -f -- "$file"
        echo "LOCAL_DELETED $file"
        ;;
      mindtune_sessions/*/*)
        rm -f -- "$file"
        echo "LOCAL_DELETED $file"
        ;;
      *)
        echo "SKIP_DELETE $file"
        exit 5
        ;;
    esac
  done < "$LIST_FILE"
)
find "$CAPTURE/mindtune_sessions" -mindepth 1 -type d -empty -delete 2>/dev/null || true
rm -f -- "$BUNDLE"
echo "LOCAL_BUNDLE_DELETED $BUNDLE"

"$PYTHON" - "$RECEIPT" <<'PY'
import json
import sys
import time
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["status"] = "remote_verified_local_deleted"
payload["local_deleted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

echo
echo "EXPORT_OK"
echo "REMOTE_DIR=$REMOTE_DIR"
echo "RECEIPT=$RECEIPT"
"""

    script_path.write_text(script, encoding="utf-8")
    os.chmod(script_path, 0o755)
    log = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [str(script_path)],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )
    return {"started": True, "pid": process.pid, "log": f"mac/{log_path.name}"}


def run_mac_once(label: str, args: list[str], timeout: int = 90) -> dict:
    ensure_mac_dirs()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = MAC_LOGS / f"mac_{stamp}_{label}.log"
    command = [str(mac_python()), str(MAC_RECORDER), *args]
    started = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"== MindTune Mac: {label} ==\n")
        log.write(time.strftime("%Y-%m-%dT%H:%M:%S%z") + "\n")
        log.write(" ".join(command) + "\n\n")
        log.flush()
        try:
            result = subprocess.run(
                command,
                cwd=str(ROOT),
                env=mac_env(),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                text=True,
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            log.write(f"\nTIMEOUT dopo {timeout}s\n")
            code = 124
    return {
        "ok": code == 0,
        "code": code,
        "log": f"mac/{log_path.name}",
        "elapsed_s": round(time.time() - started, 1),
    }


def mac_scan(params: dict) -> dict:
    seconds = as_int(params.get("scan_seconds"), 10, 1, 60)
    return run_mac_once("scan", ["scan", "--seconds", str(seconds)], timeout=seconds + 20)


def mac_smoke(params: dict) -> dict:
    scan = as_int(params.get("scan_seconds"), 10, 1, 60)
    seconds = as_int(params.get("smoke_seconds"), 12, 3, 60)
    return run_mac_once(
        "smoke",
        ["smoke", "--seconds", str(seconds), "--scan-seconds", str(scan)],
        timeout=scan + seconds + 35,
    )


def mac_handshake_dump(params: dict) -> dict:
    scan = as_int(params.get("scan_seconds"), 12, 1, 60)
    after_pair = as_int(params.get("after_pair"), 1, 0, 10)
    after_validate = as_int(params.get("after_validate"), 2, 0, 20)
    args = [
        "handshake-dump",
        "--scan-seconds",
        str(scan),
        "--after-pair",
        str(after_pair),
        "--after-validate",
        str(after_validate),
    ]
    if params.get("start"):
        args.append("--start")
    if params.get("skip_pair"):
        args.append("--skip-pair")
    if params.get("skip_validate"):
        args.append("--skip-validate")
    return run_mac_once("handshake_dump", args, timeout=scan + after_pair + after_validate + 35)


def mac_battery(params: dict) -> dict:
    ensure_mac_dirs()
    scan = as_int(params.get("scan_seconds"), 8, 1, 60)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = MAC_LOGS / f"mac_{stamp}_battery.log"
    command = [
        str(mac_python()),
        str(MAC_RECORDER),
        "battery",
        "--scan-seconds",
        str(scan),
    ]
    with log_path.open("w", encoding="utf-8") as log:
        log.write("== MindTune Mac: battery ==\n")
        log.write(time.strftime("%Y-%m-%dT%H:%M:%S%z") + "\n")
        log.write(" ".join(command) + "\n\n")
        log.flush()
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            env=mac_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=scan + 25,
            text=True,
        )
        log.write(result.stdout)

    payload = {"battery_percent": None, "updated_at": time.time(), "ok": False}
    match = re.search(r"\{.*\}", result.stdout, re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            payload.update(parsed)
            payload["updated_at"] = time.time()
        except Exception:
            pass
    MAC_BATTERY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "battery_ok": bool(payload.get("ok")),
        "battery_percent": payload.get("battery_percent"),
        "battery_message": payload.get("message"),
        "log": f"mac/{log_path.name}",
    }


def recording_command(
    condition: str,
    duration: int,
    prep: int,
    scan: int,
    start_signal: Path | None = None,
    stop_signal: Path | None = None,
    command_signal: Path | None = None,
) -> list[str]:
    command = [
        str(mac_python()),
        str(MAC_RECORDER),
        "record",
        "--condition",
        condition,
        "--duration",
        str(duration),
        "--prep",
        str(prep),
        "--scan-seconds",
        str(scan),
        "--status-file",
        str(MAC_STATUS_FILE),
        "--sleep-idle-seconds",
        "1800",
        "--enable-imu",
        "--skip-pair",
    ]
    if start_signal is not None:
        command.extend(["--start-signal-file", str(start_signal)])
    if stop_signal is not None:
        command.extend(["--stop-signal-file", str(stop_signal)])
    if command_signal is not None:
        command.extend(["--command-signal-file", str(command_signal)])
    return command


def stop_process(pid: int | None) -> None:
    if not pid:
        return
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError:
        pass


def mac_connect_recording(params: dict) -> dict:
    ensure_mac_dirs()
    current = read_mac_state()
    if current.get("running"):
        status = mac_status()
        phase = status.get("phase")
        if phase in {"connected", "ble_link", "handshake_sent", "prep", "recording", "starting"}:
            return {
                "connected": True,
                "pid": current.get("pid"),
                "log": current.get("log"),
                "phase": phase,
                "battery_percent": status.get("battery_percent"),
                "message": "casco gia collegato" if phase == "connected" else "sessione gia in corso",
            }
        stop_process(current.get("pid"))
        try:
            MAC_STATE.unlink()
        except OSError:
            pass
        return {
            "connected": False,
            "pid": current.get("pid"),
            "log": current.get("log"),
            "message": "Ho chiuso una sessione precedente rimasta appesa. Premi di nuovo Connetti.",
        }

    scan = as_int(params.get("scan_seconds"), 8, 1, 60)
    condition = validate_condition(str(params.get("condition", "eyes_open")))
    duration = as_int(params.get("duration"), 120, 5, 7200)
    prep = as_int(params.get("prep"), 20, 0, 600)
    study_context = params.get("study_context") if isinstance(params.get("study_context"), dict) else {}

    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = MAC_LOGS / f"mac_{stamp}_arm_{condition}.log"
    if MAC_STATUS_FILE.exists():
        MAC_STATUS_FILE.unlink()
    if MAC_START_SIGNAL.exists():
        MAC_START_SIGNAL.unlink()
    if MAC_STOP_SIGNAL.exists():
        MAC_STOP_SIGNAL.unlink()
    if MAC_COMMAND_SIGNAL.exists():
        MAC_COMMAND_SIGNAL.unlink()
    command = recording_command(condition, duration, prep, scan, MAC_START_SIGNAL, MAC_STOP_SIGNAL, MAC_COMMAND_SIGNAL)
    log = log_path.open("w", encoding="utf-8")
    log.write("== MindTune Mac: auto connect and wait ==\n")
    log.write(time.strftime("%Y-%m-%dT%H:%M:%S%z") + "\n")
    log.write(" ".join(command) + "\n\n")
    log.flush()
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=mac_env(),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )
    current = {
        "pid": process.pid,
        "condition": condition,
        "duration": duration,
        "prep": prep,
        "started_at": time.time(),
        "started_label": time.strftime("%H:%M:%S"),
        "log": f"mac/{log_path.name}",
        "status_file": str(MAC_STATUS_FILE),
        "armed": True,
        "running": True,
        "study_context": study_context,
    }
    MAC_STATE.write_text(json.dumps(current, indent=2), encoding="utf-8")

    connected = wait_for_mac_phase({"connected", "error"}, timeout=scan + 10)
    if connected.get("phase") == "connected":
        return {
            "connected": True,
            "pid": process.pid,
            "log": current.get("log"),
            "phase": "connected",
            "battery_percent": connected.get("battery_percent"),
            "message": "Connessione stabilita. Start e pronto.",
        }
    if connected.get("phase") == "error":
        return {
            "connected": False,
            "pid": process.pid,
            "log": current.get("log"),
            "battery_percent": connected.get("battery_percent"),
            "message": connected.get("error") or "collegamento non riuscito",
        }
    if not connected.get("running"):
        return {
            "connected": False,
            "pid": process.pid,
            "log": current.get("log"),
            "message": "Casco non rilevato.",
        }
    return {
        "connected": False,
        "pid": process.pid,
        "log": current.get("log"),
        "battery_percent": connected.get("battery_percent"),
        "message": "Sto ancora tentando il collegamento.",
    }


def mac_start_recording(params: dict) -> dict:
    ensure_mac_dirs()
    current = read_mac_state()
    if current.get("running"):
        status = mac_status()
        if status.get("phase") in {"prep", "recording"}:
            return {"started": True, "pid": current.get("pid"), "log": current.get("log"), "phase": status.get("phase")}
        if status.get("phase") in {"connected", "done"} and current.get("armed"):
            condition = validate_condition(str(params.get("condition", current.get("condition") or "eyes_open")))
            duration = as_int(params.get("duration"), int(current.get("duration") or 120), 5, 7200)
            prep = as_int(params.get("prep"), int(current.get("prep") or 20), 0, 600)
            study_context = params.get("study_context") if isinstance(params.get("study_context"), dict) else current.get("study_context", {})
            session_covariates = params.get("session_covariates") if isinstance(params.get("session_covariates"), dict) else current.get("session_covariates", {})
            current.update({"condition": condition, "duration": duration, "prep": prep, "study_context": study_context, "session_covariates": session_covariates})
            MAC_STATE.write_text(json.dumps(current, indent=2), encoding="utf-8")
            MAC_START_SIGNAL.write_text(
                json.dumps(
                    {
                        "started_at": time.time(),
                        "condition": condition,
                        "duration": duration,
                        "prep": prep,
                        "study_context": study_context,
                        "session_covariates": session_covariates,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            started = wait_for_mac_phase({"prep", "recording", "error"}, timeout=12)
            if started.get("phase") in {"prep", "recording"}:
                return {"started": True, "pid": current.get("pid"), "log": current.get("log"), "phase": started.get("phase")}
            return {
                "started": False,
                "pid": current.get("pid"),
                "log": current.get("log"),
                "message": started.get("error") or "Start inviato, ma la registrazione non e partita.",
            }
        if status.get("phase") in {"scan", "connecting", "ble_link", "handshake_sent", "starting"}:
            return {
                "started": False,
                "pid": current.get("pid"),
                "log": current.get("log"),
                "message": "Attendi la connessione del casco.",
            }
        stop_process(current.get("pid"))
        try:
            MAC_STATE.unlink()
        except OSError:
            pass

    if not params.get("force"):
        return {
            "started": False,
            "message": "Casco non ancora collegato. Accendilo e attendi che Start si attivi.",
        }

    condition = validate_condition(str(params.get("condition", "eyes_open")))
    duration = as_int(params.get("duration"), 120, 5, 7200)
    prep = as_int(params.get("prep"), 20, 0, 600)
    scan = as_int(params.get("scan_seconds"), 12, 1, 60)
    study_context = params.get("study_context") if isinstance(params.get("study_context"), dict) else {}
    session_covariates = params.get("session_covariates") if isinstance(params.get("session_covariates"), dict) else {}

    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = MAC_LOGS / f"mac_{stamp}_record_{condition}.log"
    if MAC_STATUS_FILE.exists():
        MAC_STATUS_FILE.unlink()
    if MAC_START_SIGNAL.exists():
        MAC_START_SIGNAL.unlink()
    if MAC_STOP_SIGNAL.exists():
        MAC_STOP_SIGNAL.unlink()
    command = recording_command(condition, duration, prep, scan, None, None)
    log = log_path.open("w", encoding="utf-8")
    log.write("== MindTune Mac: record immediate ==\n")
    log.write(time.strftime("%Y-%m-%dT%H:%M:%S%z") + "\n")
    log.write(" ".join(command) + "\n\n")
    log.flush()
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=mac_env(),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )
    current = {
        "pid": process.pid,
        "condition": condition,
        "duration": duration,
        "prep": prep,
        "started_at": time.time(),
        "started_label": time.strftime("%H:%M:%S"),
        "log": f"mac/{log_path.name}",
        "status_file": str(MAC_STATUS_FILE),
        "armed": False,
        "running": True,
        "study_context": study_context,
        "session_covariates": session_covariates,
    }
    MAC_STATE.write_text(json.dumps(current, indent=2), encoding="utf-8")

    started = wait_for_mac_phase({"prep", "recording", "error"}, timeout=scan + 18)
    if started.get("phase") in {"prep", "recording"}:
        return {"started": True, "pid": process.pid, "log": current.get("log"), "phase": started.get("phase")}
    if started.get("phase") == "error":
        return {
            "started": False,
            "pid": process.pid,
            "log": current.get("log"),
            "message": started.get("error") or "errore dopo Start",
        }
    if not started.get("running"):
        return {"started": False, "pid": process.pid, "log": current.get("log"), "message": "il recorder si e fermato dopo Start"}
    stop_process(process.pid)
    message = "Start inviato, ma il casco non ha aperto lo streaming EEG."
    MAC_STATUS_FILE.write_text(
        json.dumps(
            {
                "phase": "error",
                "phase_started_at": time.time(),
                "updated_at": time.time(),
                "condition": current.get("condition"),
                "duration": current.get("duration"),
                "prep": current.get("prep"),
                "battery_percent": read_cached_battery_percent(started),
                "error": message,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    try:
        MAC_STATE.unlink()
    except OSError:
        pass
    return {"started": False, "pid": current.get("pid"), "log": current.get("log"), "message": message}


def mac_stop_recording() -> dict:
    state = read_mac_state()
    pid = int(state.get("pid") or 0)
    if not state.get("running"):
        return {"stopped": False, "message": "nessuna registrazione Mac attiva", "log": state.get("log")}
    status = mac_status()
    phase = status.get("phase")
    if phase == "connected":
        return {"stopped": False, "message": "casco gia collegato e in attesa", "log": state.get("log")}
    if phase in {"prep", "recording"}:
        MAC_STOP_SIGNAL.write_text(str(time.time()), encoding="utf-8")
        stopped = wait_for_mac_phase({"connected", "done", "error"}, timeout=8)
        if stopped.get("phase") in {"connected", "done"}:
            return {
                "stopped": True,
                "message": "sessione fermata, casco ancora collegato",
                "log": state.get("log"),
                "phase": stopped.get("phase"),
            }
        return {
            "stopped": True,
            "message": "stop sessione inviato",
            "log": state.get("log"),
            "phase": stopped.get("phase"),
        }

    MAC_STATUS_FILE.write_text(
        json.dumps(
            {
                "phase": "interrupted",
                "phase_started_at": time.time(),
                "updated_at": time.time(),
                "condition": state.get("condition"),
                "duration": state.get("duration"),
                "prep": state.get("prep"),
                "error": "interrotto dall'utente",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    try:
        os.killpg(pid, signal.SIGINT)
    except ProcessLookupError:
        return {"stopped": False, "message": "processo gia terminato", "log": state.get("log")}
    except Exception:
        os.kill(pid, signal.SIGTERM)
    time.sleep(0.5)
    try:
        MAC_START_SIGNAL.unlink()
    except OSError:
        pass
    try:
        MAC_STOP_SIGNAL.unlink()
    except OSError:
        pass
    try:
        MAC_COMMAND_SIGNAL.unlink()
    except OSError:
        pass
    try:
        MAC_STATE.unlink()
    except OSError:
        pass
    return {"stopped": True, "message": "stop inviato", "log": state.get("log")}


def mac_send_hardware_command(params: dict) -> dict:
    state = read_mac_state()
    if not state.get("running"):
        return {"ok": False, "message": "nessuna registrazione Mac attiva"}
    status = mac_status()
    phase = status.get("phase")
    if phase not in {"prep", "recording", "connected"}:
        return {"ok": False, "message": f"fase non compatibile: {phase}"}
    cmd_type = str(params.get("type", ""))
    if cmd_type not in {"led_color", "vibration"}:
        return {"ok": False, "message": "tipo comando non supportato"}
    payload = {"type": cmd_type}
    if cmd_type == "led_color":
        payload.update({
            "r": max(0, min(255, int(params.get("r", 0)))),
            "g": max(0, min(255, int(params.get("g", 0)))),
            "b": max(0, min(255, int(params.get("b", 0)))),
            "encoding": str(params.get("encoding", "varint")),
        })
    elif cmd_type == "vibration":
        payload["intensity"] = max(0, min(100, int(params.get("intensity", 50))))
    MAC_COMMAND_SIGNAL.write_text(json.dumps(payload), encoding="utf-8")
    return {"ok": True, "command": payload, "phase": phase}


OURA_DAILY_SQL = """
SELECT
  json_object(
    'day', s.day,
    'sleep_score', s.score,
    'sleep_duration_s', s.total_sleep_duration,
    'sleep_duration_h', round(cast(s.total_sleep_duration AS REAL) / 3600, 2),
    'deep_h', round(cast(s.deep_sleep_duration AS REAL) / 3600, 2),
    'rem_h', round(cast(s.rem_sleep_duration AS REAL) / 3600, 2),
    'light_h', round(cast(s.light_sleep_duration AS REAL) / 3600, 2),
    'awake_h', round(cast(s.awake_time AS REAL) / 3600, 2),
    'latency_s', s.latency,
    'restlessness', s.restlessness,
    'hr_average', s.hr_average,
    'hr_lowest', s.hr_lowest,
    'readiness_score', r.score,
    'cognitive_energy', r.score,
    'resting_hr', r.resting_heart_rate,
    'hrv_balance', r.hrv_balance,
    'recovery_index', r.recovery_index,
    'temperature_delta', r.temperature_delta
  ) AS payload
FROM oura_daily_sleep s
LEFT JOIN oura_daily_readiness r ON r.day = s.day
WHERE s.day = '{day}'
LIMIT 1;
"""


def ssh_remote(command: str, timeout: int = 20) -> tuple[bool, str]:
    host = os.environ.get("MINDTUNE_RPI_HOST", DEFAULT_RPI_HOST)
    key = str(SSH_KEY) if SSH_KEY.exists() else None
    args = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=8"]
    if key:
        args.extend(["-i", key])
    args.append(host)
    args.append(command)
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, result.stdout.strip()
    except Exception as exc:
        return False, str(exc)


def query_oura_daily(requested_day: str = "") -> dict:
    today = time.strftime("%Y-%m-%d")
    day = requested_day or today
    candidates = [day]
    if not requested_day:
        candidates.append(time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400)))
    for candidate in candidates:
        sql = OURA_DAILY_SQL.replace("{day}", candidate)
        command = f"sqlite3 /mnt/biohacking/sqlite/health_data.db '{sql}'"
        ok, output = ssh_remote(command, timeout=15)
        if not ok:
            return {"ok": False, "day": candidate, "error": output}
        if output:
            try:
                rows = [json.loads(line) for line in output.splitlines() if line.strip()]
                if rows:
                    return {"ok": True, "day": candidate, "data": rows[0]}
            except Exception as exc:
                return {"ok": False, "day": candidate, "error": f"parse: {exc}", "raw": output}
    return {"ok": False, "day": candidates[0], "error": "dati Oura non trovati per oggi/ieri"}


# ---------------------------------------------------------------------------
# MLF B2.7 Hebrew vertical-slice backend
# ---------------------------------------------------------------------------

def _mlf_error(message: str, code: int = 400) -> dict:
    payload = {"ok": False, "error": message, "mlf_available": _MLF_AVAILABLE}
    if _MLF_IMPORT_ERROR:
        payload["diagnostic"] = _MLF_IMPORT_ERROR
    return payload


def _hebrew_mlf_student(student_name: str | None = None) -> Any:
    name = str(student_name or HEBREW_MLF_DEFAULT_STUDENT).strip() or HEBREW_MLF_DEFAULT_STUDENT
    normalized_name = re.sub(r"\s+", " ", name).strip()
    stable_key = normalized_name.casefold()
    return Student(
        student_id=uuid5(NAMESPACE_DNS, f"mindtune-lab:hebrew-mlf:{stable_key}"),
        name=normalized_name,
        preferences={
            "platform": "mindtune_lab",
            "domain": "hebrew_modern",
            "identity_scope": "local_single_user",
        },
    )


def _hebrew_mlf_units() -> list[dict]:
    if not _MLF_AVAILABLE:
        return []
    adapter = HebrewDomainAdapter()
    units = []
    for unit in adapter.list_units():
        meta = unit.metadata or {}
        review_status = meta.get("review_status", STATUS_DRAFT)
        status = meta.get("status", STATUS_DRAFT)
        units.append(
            {
                "unit_id": str(unit.unit_id),
                "canonical": unit.canonical,
                "italian": meta.get("italian", ""),
                "review_status": review_status,
                "status": status,
                "display_status": "draft_unverified" if status == STATUS_DRAFT else status,
                "linguistically_approved": review_status == STATUS_HUMAN_LINGUISTIC_APPROVED,
                "pedagogically_approved": review_status == STATUS_HUMAN_PEDAGOGICAL_APPROVED,
                "allowed_trial_types": list(unit.allowed_trial_types),
            }
        )
    return units


def _hebrew_mlf_brainlab() -> Optional[Any]:
    if not _MLF_AVAILABLE:
        return None
    HEBREW_MLF_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    store = SQLiteEventStore(HEBREW_MLF_DB_PATH)
    adapter, scorer = get_domain_adapter_and_scorer("hebrew")
    return BrainLab(
        store=store,
        transformation=M0Transformation(),
        scheduler=M0Scheduler(),
        domain_adapter=adapter,
        scorer=scorer,
    )


def _close_hebrew_mlf_brainlab(brainlab: Any) -> None:
    store = getattr(brainlab, "store", None)
    close = getattr(store, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def _hebrew_mlf_state(brainlab: Any, student_id: Any, unit_id: Any) -> dict:
    state = brainlab.get_state(student_id, unit_id)
    snapshot = state.snapshot()
    return {
        "competence": snapshot.get("values", {}).get("competence"),
        "count": snapshot.get("values", {}).get("count"),
        "model_id": snapshot.get("metadata", {}).get("model_id"),
        "model_version": snapshot.get("metadata", {}).get("model_version"),
    }


def _hebrew_mlf_active_retests(store: Any, student_id: Any) -> list[dict]:
    queue = RetestQueue(store)
    retests = queue.list_retests(student_id=student_id)
    return [
        {
            "retest_id": str(r.retest_id) if r.retest_id else None,
            "unit_id": str(r.unit_id) if r.unit_id else None,
            "horizon": r.horizon,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
            "window_start": r.window_start.isoformat() if r.window_start else None,
            "window_end": r.window_end.isoformat() if r.window_end else None,
            "state": r.state,
        }
        for r in retests
    ]


def hebrew_mlf_units_state() -> dict:
    return {"ok": True, "mlf_available": _MLF_AVAILABLE, "units": _hebrew_mlf_units()}


def hebrew_mlf_start(params: dict) -> dict:
    if threading.get_ident() != _HEBREW_MLF_WORKER_THREAD_ID:
        try:
            return _run_hebrew_mlf_job(lambda: hebrew_mlf_start(params))
        except Exception as exc:
            return _mlf_error(str(exc))

    if not _MLF_AVAILABLE:
        return _mlf_error("mindtune-learning-framework non installato")

    unit_id = str(params.get("unit_id", "")).strip()
    trial_type = str(params.get("trial_type", "")).strip()
    student_name = str(params.get("student_name", HEBREW_MLF_DEFAULT_STUDENT)).strip() or HEBREW_MLF_DEFAULT_STUDENT

    if not unit_id or not trial_type:
        return _mlf_error("unit_id e trial_type sono obbligatori")

    brainlab = _hebrew_mlf_brainlab()
    if brainlab is None:
        return _mlf_error("impossibile inizializzare BrainLab")

    try:
        adapter = brainlab.domain_adapter
        try:
            unit = adapter.get_unit(unit_id)
        except (KeyError, ValueError):
            return _mlf_error(f"unit {unit_id} non trovata")

        if trial_type not in unit.allowed_trial_types:
            return _mlf_error(f"trial_type {trial_type} non supportato per questa unit")

        student = _hebrew_mlf_student(student_name)
        session = brainlab.start_session(student, protocol_id="pilot-a", condition="hebrew_mlf_b2_7")
        trial = brainlab.start_trial(session, unit, trial_type, process_target="retrieval")

        with _HEBREW_MLF_LOCK:
            _HEBREW_MLF_SESSIONS[str(session.session_id)] = {
                "brainlab": brainlab,
                "session": session,
                "trial": trial,
                "student": student,
                "unit": unit,
                "trial_type": trial_type,
            }

        prompt = trial.stimulus
        if not prompt:
            prompt = adapter.generate_prompt(unit, trial_type, process_target="retrieval")

        return {
            "ok": True,
            "mlf_available": True,
            "session_id": str(session.session_id),
            "student_id": str(student.student_id),
            "trial_id": str(trial.trial_id),
            "unit_id": str(unit.unit_id),
            "trial_type": trial_type,
            "prompt": prompt,
            "display_status": "technical_preview",
            "linguistically_approved": False,
            "pedagogically_approved": False,
        }
    except Exception:
        _close_hebrew_mlf_brainlab(brainlab)
        raise


def hebrew_mlf_respond(params: dict) -> dict:
    if threading.get_ident() != _HEBREW_MLF_WORKER_THREAD_ID:
        try:
            return _run_hebrew_mlf_job(lambda: hebrew_mlf_respond(params))
        except Exception as exc:
            return _mlf_error(str(exc))

    if not _MLF_AVAILABLE:
        return _mlf_error("mindtune-learning-framework non installato")

    session_id = str(params.get("session_id", "")).strip()
    raw_response = str(params.get("response", ""))

    if not session_id:
        return _mlf_error("session_id obbligatorio")

    with _HEBREW_MLF_LOCK:
        record = _HEBREW_MLF_SESSIONS.get(session_id)

    if record is None:
        return _mlf_error("sessione non trovata o scaduta")

    brainlab = record["brainlab"]
    session = record["session"]
    trial = record["trial"]
    student = record["student"]
    unit = record["unit"]
    trial_type = record["trial_type"]

    try:
        adapter = brainlab.domain_adapter
        normalized_response = adapter.normalize_response(raw_response, unit, trial_type)
        response = Response(raw=raw_response, normalized=normalized_response)
        trial = brainlab.submit_response(session, trial, response, monotonic_response_ns=0)
        trial = brainlab.score_trial(session, trial)
        score = trial.score

        feedback_key = "correct" if score and score.outcome == "correct" else "root_hint"
        feedback_text = unit.metadata.get("feedback", {}).get(feedback_key, score.outcome if score else "")
        brainlab.give_feedback(session, trial, "outcome", feedback_text)

        retest_warning = ""
        try:
            brainlab.trigger_retest(session, trial, horizon="24h")
        except Exception as exc:
            retest_warning = str(exc)

        brainlab.close_session(session, end_of_session={"reason": "completed"})

        state_summary = _hebrew_mlf_state(brainlab, student.student_id, unit.unit_id)
        retests = _hebrew_mlf_active_retests(brainlab.store, student.student_id)

        with _HEBREW_MLF_LOCK:
            _HEBREW_MLF_SESSIONS.pop(session_id, None)

        normalized = response.normalized
        if not normalized and hasattr(trial.response, "normalized"):
            normalized = trial.response.normalized
        if not normalized:
            normalized = adapter.normalize_response(raw_response, unit, trial_type)

        return {
            "ok": True,
            "mlf_available": True,
            "session_id": session_id,
            "student_id": str(student.student_id),
            "trial_id": str(trial.trial_id),
            "unit_id": str(unit.unit_id),
            "raw_response": raw_response,
            "normalized_response": normalized,
            "outcome": score.outcome if score else "unknown",
            "feedback": feedback_text,
            "m0_state": state_summary,
            "retests": retests,
            "warnings": {"retest": retest_warning} if retest_warning else {},
            "display_status": "technical_preview",
            "linguistically_approved": False,
            "pedagogically_approved": False,
        }
    finally:
        _close_hebrew_mlf_brainlab(brainlab)


def hebrew_mlf_retests(params: dict | None = None) -> dict:
    if not _MLF_AVAILABLE:
        return _mlf_error("mindtune-learning-framework non installato")

    student_id_param = str((params or {}).get("student_id", "")).strip()
    if not student_id_param:
        return {"ok": True, "mlf_available": True, "retests": []}

    try:
        student_id = UUID(student_id_param)
    except ValueError:
        return _mlf_error("student_id non valido")

    store = SQLiteEventStore(HEBREW_MLF_DB_PATH)
    try:
        return {
            "ok": True,
            "mlf_available": True,
            "retests": _hebrew_mlf_active_retests(store, student_id),
        }
    finally:
        close = getattr(store, "close", None)
        if callable(close):
            close()


class Handler(BaseHTTPRequestHandler):
    server_version = "MindTuneConsole/0.1"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return text_response(self, (APP / "index.html").read_text(encoding="utf-8"), "text/html; charset=utf-8")
        if parsed.path == "/styles.css":
            return text_response(self, (APP / "styles.css").read_text(encoding="utf-8"), "text/css; charset=utf-8")
        if parsed.path == "/app.js":
            return text_response(self, (APP / "app.js").read_text(encoding="utf-8"), "application/javascript; charset=utf-8")
        if parsed.path.startswith("/assets/"):
            name = Path(parsed.path).name
            asset = (APP / "assets" / name).resolve()
            assets_root = (APP / "assets").resolve()
            if assets_root in asset.parents and asset.exists() and asset.is_file():
                data = asset.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(asset.name)[0] or "application/octet-stream")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404)
            return
        if parsed.path == "/api/state":
            query = parse_qs(parsed.query)
            logs = list_logs()
            selected = query.get("log", [logs[0]["id"] if logs else ""])[0]
            selected_path = log_path_from_id(selected)
            selected_log = tail_text(selected_path) if selected_path else ""
            return json_response(
                self,
                {
                    "bridge": bridge_running(),
                    "mac": mac_status(),
                    "memory": memory_state(),
                    "sessions": list_mac_sessions(),
                    "jobs": list_jobs(),
                    "logs": logs,
                    "selected_log": selected,
                    "selected_log_text": selected_log,
                    "time": time.strftime("%H:%M:%S"),
                    "app_version": APP_VERSION,
                    "app_build": APP_BUILD,
                },
            )
        if parsed.path == "/api/oura_daily":
            query = parse_qs(parsed.query)
            day = (query.get("day") or [""])[0]
            return json_response(self, oura_api.fetch_oura_daily(day))
        if parsed.path == "/api/oura_auth":
            return json_response(self, oura_api.start_oauth_flow())
        if parsed.path == "/api/oura_auth_url":
            result, auth_url = oura_api.get_auth_url()
            oura_api.ensure_callback_server()
            return json_response(self, {**result, "auth_url": auth_url})
        if parsed.path == "/api/flashcard_catalog":
            return json_response(self, seed_catalog())
        if parsed.path == "/api/help/item":
            query = parse_qs(parsed.query)
            return json_response(
                self,
                help_item_state(
                    {
                        "item_id": (query.get("item_id") or [""])[0],
                        "hebrew": (query.get("hebrew") or [""])[0],
                    }
                ),
            )
        if parsed.path == "/api/help/profile":
            return json_response(self, help_profile_state())
        if parsed.path == "/api/hebrew/recovery_plan":
            query = parse_qs(parsed.query)
            readiness = as_float((query.get("readiness") or [""])[0], -1, -1, 100)
            sleep_h = as_float((query.get("sleep_h") or [""])[0], -1, -1, 24)
            return json_response(
                self,
                hebrew_recovery_plan_state(
                    as_int((query.get("minutes") or ["30"])[0], 30, 15, 90),
                    None if readiness < 0 else readiness,
                    None if sleep_h < 0 else sleep_h,
                ),
            )
        if parsed.path == "/api/hebrew/sources":
            return json_response(self, hebrew_source_registry_state())
        if parsed.path == "/api/conjugation_catalog":
            return json_response(self, conjugation_catalog_state())
        if parsed.path == "/api/shoresh_catalog":
            return json_response(self, shoresh_catalog_state())
        if parsed.path == "/api/mlf/hebrew/units":
            return json_response(self, hebrew_mlf_units_state())
        if parsed.path == "/api/mlf/hebrew/retests":
            query = parse_qs(parsed.query)
            params = {"student_id": (query.get("student_id") or [""])[0]}
            return json_response(self, hebrew_mlf_retests(params))
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/oura_token":
            try:
                payload = read_json(self)
                token = str(payload.get("token", "")).strip()
                if not token:
                    return json_response(self, {"ok": False, "error": "token mancante"}, status=400)
                oura_api.save_token({"access_token": token, "token_type": "Bearer", "obtained_at": time.time()})
                return json_response(self, {"ok": True})
            except Exception as exc:
                return json_response(self, {"ok": False, "error": str(exc)}, status=400)
        if parsed.path == "/api/memory":
            try:
                payload = read_json(self)
                action = str(payload.get("action", ""))
                params = payload.get("params", {}) or {}
                if action == "save_item":
                    result = memory_save_item(params)
                elif action == "add_flashcard":
                    result = memory_add_flashcard(params)
                elif action == "update_item":
                    result = memory_update_item(params)
                elif action == "delete_item":
                    result = memory_delete_item(params)
                elif action == "import_flashcards":
                    result = memory_import_flashcards(params)
                elif action == "import_seed":
                    result = memory_auto_import_seed(only_if_empty=False, params=params)
                elif action == "log_recall":
                    result = memory_log_recall(params)
                elif action == "save_shoresh_session":
                    result = shoresh_save_session(params)
                else:
                    raise ValueError("azione memoria non riconosciuta")
            except Exception as exc:
                return json_response(self, {"ok": False, "error": str(exc)}, status=400)
            return json_response(self, {"ok": True, **result})

        if parsed.path == "/api/mlf/hebrew/session/start":
            try:
                payload = read_json(self)
                return json_response(self, hebrew_mlf_start(payload))
            except Exception as exc:
                return json_response(self, {"ok": False, "error": str(exc)}, status=400)
        if parsed.path == "/api/mlf/hebrew/session/respond":
            try:
                payload = read_json(self)
                return json_response(self, hebrew_mlf_respond(payload))
            except Exception as exc:
                return json_response(self, {"ok": False, "error": str(exc)}, status=400)
        if parsed.path != "/api/job":
            self.send_error(404)
            return
        try:
            payload = read_json(self)
            action = str(payload.get("action", ""))
            params = payload.get("params", {}) or {}
            if action == "start_bridge":
                result = start_bridge()
            elif action == "mac_scan":
                result = mac_scan(params)
            elif action == "mac_smoke":
                result = mac_smoke(params)
            elif action == "mac_handshake_dump":
                result = mac_handshake_dump(params)
            elif action == "mac_battery":
                result = mac_battery(params)
            elif action == "mac_connect_recording":
                result = mac_connect_recording(params)
            elif action == "mac_start_recording":
                result = mac_start_recording(params)
            elif action == "mac_stop_recording":
                result = mac_stop_recording()
            elif action == "mac_status":
                result = {"mac": mac_status(), "sessions": list_mac_sessions()}
            elif action == "mac_log_task_event":
                result = append_task_event(params)
            elif action == "save_training_session":
                result = save_training_session(params)
            elif action == "mac_export_sessions":
                result = mac_export_sessions()
            elif action == "mac_delete_session":
                result = delete_mac_session(params)
            elif action == "delete_training_session":
                result = delete_mindtune_task_session(params)
            elif action == "mac_delete_aborted_sessions":
                result = delete_aborted_mac_sessions()
            elif action == "mac_send_hardware_command":
                result = mac_send_hardware_command(params)
            else:
                result = enqueue_job(action, params)
        except Exception as exc:
            return json_response(self, {"ok": False, "error": str(exc)}, status=400)
        return json_response(self, {"ok": True, **result})


def main() -> None:
    host = "127.0.0.1"
    port = int(os.environ.get("MINDTUNE_CONSOLE_PORT", "8787"))
    startup_housekeeping()
    one_shot_minisession_cleanup()
    httpd = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"MindTune console: {url}")
    root_path = str(ROOT)
    is_native_app = "Application Support" in root_path and "MindTune" in root_path
    if os.environ.get("MINDTUNE_AUTO_OPEN_BROWSER", "" if is_native_app else "1") == "1":
        threading.Timer(1.0, lambda: webbrowser.open(url, new=2)).start()
    httpd.serve_forever()


if __name__ == "__main__":
    main()
