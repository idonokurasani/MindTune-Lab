"""HeLP record validation, duplicate detection and normalization checks."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import HeLPFormEvidence, HeLPImportReport, HeLPVerbSummary
from .provenance import provenance_from_record
from .schemas import (
    make_form_evidence_from_row,
    make_verb_summary_from_row,
    validate_form_record,
    validate_verb_summary_record,
)


def _parse_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize CSV row keys and strip whitespace."""
    return {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}


def _split_pipe_field(value: Any) -> list[str]:
    if value is None:
        return []
    return [piece.strip() for piece in str(value).split("|") if piece.strip()]


def load_validated_help_forms(
    forms_path: Path,
    dataset_version: str = "",
) -> tuple[list[HeLPFormEvidence], HeLPImportReport]:
    """Load and validate the HeLP forms CSV, returning typed evidence and a report."""
    if not forms_path.exists():
        return [], HeLPImportReport(
            input_rows=0,
            valid_rows=0,
            invalid_rows=0,
            duplicate_rows=0,
            normalized_rows=0,
            unmatched_rows=0,
            linked_records=0,
            manual_review_records=0,
            errors=[f"forms file not found: {forms_path}"],
        )

    rows: list[tuple[int, dict[str, Any]]] = []
    errors: list[str] = []
    with forms_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, raw in enumerate(reader, start=1):
            row = _parse_record(raw)
            is_valid, row_errors = validate_form_record(row, idx)
            if not is_valid:
                errors.extend(row_errors)
                continue
            # Normalize pipe-delimited matched/missing form lists if present.
            if "matched_forms" in row:
                row["matched_forms"] = _split_pipe_field(row["matched_forms"])
            if "missing_from_help_forms" in row:
                row["missing_from_help_forms"] = _split_pipe_field(row["missing_from_help_forms"])
            rows.append((idx, row))

    seen: set[tuple[str, str, str, str]] = set()
    duplicates = 0
    normalized = 0
    evidence: list[HeLPFormEvidence] = []
    for _idx, row in rows:
        key = (row["verb_id"], row["slot"], row["form"], row["word_key"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        # Surface form normalization check: word_key should equal stripped form.
        if row["word_key"] != row["form"].strip():
            normalized += 1
        provenance = provenance_from_record(row, forms_path, explicit_version=dataset_version)
        evidence.append(make_form_evidence_from_row(row, provenance))

    report = HeLPImportReport(
        input_rows=len(rows) + len(errors),
        valid_rows=len(evidence),
        invalid_rows=len(errors),
        duplicate_rows=duplicates,
        normalized_rows=normalized,
        unmatched_rows=sum(1 for e in evidence if not e.help_matched),
        linked_records=sum(1 for e in evidence if e.help_matched),
        manual_review_records=0,
        errors=errors,
    )
    return evidence, report


def load_validated_help_audit(
    audit_path: Path,
    dataset_version: str = "",
) -> tuple[list[HeLPVerbSummary], HeLPImportReport]:
    """Load and validate the HeLP audit CSV, returning typed verb summaries and a report."""
    if not audit_path.exists():
        return [], HeLPImportReport(
            input_rows=0,
            valid_rows=0,
            invalid_rows=0,
            duplicate_rows=0,
            normalized_rows=0,
            unmatched_rows=0,
            linked_records=0,
            manual_review_records=0,
            errors=[f"audit file not found: {audit_path}"],
        )

    rows: list[tuple[int, dict[str, Any]]] = []
    errors: list[str] = []
    with audit_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, raw in enumerate(reader, start=1):
            row = _parse_record(raw)
            is_valid, row_errors = validate_verb_summary_record(row, idx)
            if not is_valid:
                errors.extend(row_errors)
                continue
            row["matched_forms"] = _split_pipe_field(row.get("matched_forms"))
            row["missing_from_help_forms"] = _split_pipe_field(row.get("missing_from_help_forms"))
            rows.append((idx, row))

    seen: set[str] = set()
    duplicates = 0
    summaries: list[HeLPVerbSummary] = []
    for _idx, row in rows:
        key = row["verb_id"]
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        provenance = provenance_from_record(row, audit_path, explicit_version=dataset_version)
        summaries.append(make_verb_summary_from_row(row, provenance))

    report = HeLPImportReport(
        input_rows=len(rows) + len(errors),
        valid_rows=len(summaries),
        invalid_rows=len(errors),
        duplicate_rows=duplicates,
        normalized_rows=0,
        unmatched_rows=sum(1 for s in summaries if s.help_match_ratio == 0.0),
        linked_records=sum(1 for s in summaries if s.help_matched_unique > 0),
        manual_review_records=sum(1 for s in summaries if s.flags),
        errors=errors,
    )
    return summaries, report


def load_help_enrichment_json(
    enrichment_path: Path,
) -> dict[str, Any]:
    """Load the HeLP enrichment JSON, returning its top-level payload with a version note."""
    if not enrichment_path.exists():
        return {"schema_version": 0, "source": {}, "summary": {}, "verbs": []}
    with enrichment_path.open(encoding="utf-8") as f:
        payload = json.load(f)
        if isinstance(payload, dict):
            return payload
        return {}
