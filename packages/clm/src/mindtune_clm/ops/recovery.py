"""Crash recovery helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass
class CrashRecoveryResult:
    """Result of crash recovery."""

    recovered_sessions: list[str]
    interrupted: list[str]
    stale_locks_released: int
    pending_playback_terminated: bool
    events_valid: bool
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovered_sessions": self.recovered_sessions,
            "interrupted": self.interrupted,
            "stale_locks_released": self.stale_locks_released,
            "pending_playback_terminated": self.pending_playback_terminated,
            "events_valid": self.events_valid,
            "errors": self.errors,
        }


def _load_session_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return {}


def run_crash_recovery(
    sessions_dir: Path,
    locks_dir: Path,
    events_dir: Path,
) -> CrashRecoveryResult:
    """Perform startup crash recovery."""
    result = CrashRecoveryResult(
        recovered_sessions=[],
        interrupted=[],
        stale_locks_released=0,
        pending_playback_terminated=True,
        events_valid=True,
        errors=[],
    )

    if sessions_dir.exists():
        for session_file in sorted(sessions_dir.glob("*.json")):
            state = _load_session_state(session_file)
            if state.get("active"):
                session_id = session_file.stem
                result.recovered_sessions.append(session_id)
                result.interrupted.append(session_id)
                # mark interrupted, do not auto-resume adaptive playback
                session_file.write_text(
                    json.dumps({**state, "active": False, "interrupted": True}),
                    encoding="utf-8",
                )

    if locks_dir.exists():
        for lock_file in sorted(locks_dir.glob("*.lock")):
            try:
                lock_file.unlink()
                result.stale_locks_released += 1
            except OSError as exc:
                result.errors.append(f"lock {lock_file}: {exc}")

    if events_dir.exists():
        # simplistic event chain validation
        event_files = sorted(events_dir.glob("*.jsonl"))
        for event_file in event_files:
            try:
                last_seq = -1
                with open(event_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        obj = json.loads(line)
                        seq = obj.get("sequence", -1)
                        if seq <= last_seq:
                            result.events_valid = False
                            result.errors.append(f"sequence error in {event_file}")
                        last_seq = seq
            except Exception as exc:
                result.events_valid = False
                result.errors.append(f"event file {event_file}: {exc}")

    return result
