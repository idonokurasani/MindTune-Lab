"""Redacted analysis-dataset exports for CLM-08."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from io import StringIO
from typing import Any

from mindtune_clm.validation.datasets import AnalysisDataset


def _is_mac(value: str) -> bool:
    return bool(re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", value))


def _is_path(value: str) -> bool:
    return bool(re.search(r"(?:^[A-Za-z]:[\\/]|[~]/|/[^/\s])", value))


def _redact_value(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: _redact_value(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v, key) for v in value]
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return value
        if key and key.lower() in {
            "name",
            "email",
            "phone",
            "dob",
            "address",
            "employer",
            "token",
            "api_key",
            "password",
            "secret",
            "authorization",
            "learner_id",
            "participant_id",
        }:
            return "[REDACTED]"
        if _is_mac(value):
            return "[REDACTED_MAC]"
        if _is_path(value):
            return "[REDACTED_PATH]"
    return value


def redact_dataset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a redacted copy of the dataset rows."""
    return [_redact_value(row) for row in rows]


def export_json(dataset: AnalysisDataset) -> str:
    rows = redact_dataset(dataset.as_dicts())
    return json.dumps({
        "study_id": dataset.study_id,
        "study_version": dataset.study_version,
        "population": dataset.population,
        "checksum": dataset.checksum,
        "rows": rows,
    }, sort_keys=True, separators=(",", ":"), default=str)


def export_csv(dataset: AnalysisDataset) -> str:
    rows = redact_dataset(dataset.as_dicts())
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return output.getvalue()


def export_checksum(rows: list[dict[str, Any]]) -> str:
    body = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
