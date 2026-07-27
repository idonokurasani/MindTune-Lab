"""Deterministic data-quality gate for CLM-08 analysis datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mindtune_clm.validation.designs import StudyDefinition


@dataclass(frozen=True)
class QualityReport:
    analysis_ready: bool
    blocking_errors: list[str]
    warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "analysis_ready": self.analysis_ready,
            "blocking_errors": list(self.blocking_errors),
            "warnings": list(self.warnings),
        }


def _required_timepoints() -> list[str]:
    return ["immediate", "within_session", "next_session"]


def evaluate_dataset_quality(rows: list[dict[str, Any]], study: StudyDefinition | None = None) -> QualityReport:  # noqa: C901
    """Check an analysis dataset for blocking errors and warnings."""
    errors: list[str] = []
    warnings: list[str] = []

    if not rows:
        errors.append("empty_dataset")
        return QualityReport(False, errors, warnings)

    required = {
        "study_id",
        "participant_id",
        "session_id",
        "condition",
        "trial_id",
        "item_id",
        "response",
        "correct",
        "response_time_ms",
    }
    missing_cols = required - set(rows[0].keys())
    if missing_cols:
        errors.append(f"missing_columns:{','.join(sorted(missing_cols))}")

    seen_trials: set[tuple[Any, Any]] = set()
    dup_trials: set[str] = set()
    for row in rows:
        key = (row.get("session_id"), row.get("trial_id"))
        if key in seen_trials:
            dup_trials.add(str(key))
        seen_trials.add(key)
    if dup_trials:
        errors.append(f"duplicate_responses:{len(dup_trials)}")

    session_first_ts: dict[str, float] = {}
    session_last_ts: dict[str, float] = {}
    for row in rows:
        sid = row.get("session_id")
        ts = row.get("timestamp")
        if sid and isinstance(ts, (int, float)):
            session_first_ts[sid] = min(session_first_ts.get(sid, ts), ts)
            session_last_ts[sid] = max(session_last_ts.get(sid, 0.0), ts)
    for sid, last in session_last_ts.items():
        first = session_first_ts.get(sid, 0.0)
        if last < first:
            errors.append(f"invalid_timestamps:{sid}")

    impossible_rts = 0
    for row in rows:
        rt = row.get("response_time_ms")
        if rt is not None and (not isinstance(rt, (int, float)) or rt < 0 or rt > 600000):
            impossible_rts += 1
    if impossible_rts:
        errors.append(f"impossible_response_times:{impossible_rts}")

    missing_condition = sum(1 for r in rows if not r.get("condition"))
    if missing_condition:
        errors.append(f"missing_condition_assignment:{missing_condition}")

    if study is not None:
        condition_ids = {c.condition_id for c in study.conditions}
        wrong_cond = sum(1 for r in rows if r.get("condition") and r["condition"] not in condition_ids)
        if wrong_cond:
            errors.append(f"wrong_condition:{wrong_cond}")

        wrong_curriculum = sum(
            1
            for r in rows
            if r.get("curriculum_version") and r["curriculum_version"] != study.curriculum_version
        )
        if wrong_curriculum:
            errors.append(f"wrong_curriculum_version:{wrong_curriculum}")

        wrong_protocol = sum(
            1
            for r in rows
            if r.get("protocol_version") and r["protocol_version"] != study.protocol_version
        )
        if wrong_protocol:
            errors.append(f"wrong_protocol_version:{wrong_protocol}")

        profile_mismatch = sum(
            1
            for r in rows
            if r.get("calibration_profile") and study.calibration_requirement not in {"none", ""}
            and r.get("calibration_profile") != study.calibration_requirement
        )
        if profile_mismatch:
            warnings.append(f"incompatible_calibration_profile:{profile_mismatch}")

    missing_playback = sum(1 for r in rows if not r.get("playback_receipt"))
    if missing_playback:
        errors.append(f"missing_playback_receipts:{missing_playback}")

    missing_outcomes = sum(1 for r in rows if r.get("correct") is None)
    if missing_outcomes:
        errors.append(f"incomplete_outcomes:{missing_outcomes}")

    missing_sensor = sum(1 for r in rows if not r.get("sensor_quality_summary"))
    if missing_sensor:
        warnings.append(f"missing_sensor_summary:{missing_sensor}")

    for row in rows:
        if row.get("deviation_flags"):
            warnings.append(f"deviation_in_row:{row.get('trial_id')}")

    chain_statuses = {r.get("session_id") for r in rows if r.get("event_chain_corrupted")}
    if chain_statuses:
        errors.append(f"event_chain_corrupted:{len(chain_statuses)}")

    return QualityReport(
        analysis_ready=len(errors) == 0,
        blocking_errors=errors,
        warnings=warnings,
    )


def validate_event_chain(events: list[dict[str, Any]]) -> list[str]:
    """Check a raw event list for broken causal links."""
    errors: list[str] = []
    types = {e.get("event_type") for e in events}
    if "session_created" not in types:
        errors.append("missing_session_created")
    if "session_completed" not in types:
        errors.append("missing_session_completed")
    ids = {e.get("event_id") for e in events if e.get("event_id")}
    for e in events:
        for prov in e.get("provenance", []):
            if prov not in ids:
                errors.append(f"missing_provenance:{prov}")
    return errors
