"""Lightweight schema validation for HeLP records."""

from __future__ import annotations

from typing import Any

from .models import HeLPFormEvidence, HeLPProvenance, HeLPVerbSummary

REQUIRED_FORM_FIELDS = ("verb_id", "root", "binyan", "slot", "form", "word_key")


def validate_form_record(record: dict[str, Any], row_number: int) -> tuple[bool, list[str]]:
    """Return (is_valid, errors) for a raw HeLP form row."""
    errors: list[str] = []
    for field in REQUIRED_FORM_FIELDS:
        if field not in record or str(record.get(field, "")).strip() == "":
            errors.append(f"row {row_number}: missing field '{field}'")
    # Hebrew-only surface forms should not be empty after normalization.
    form = str(record.get("form", "")).strip()
    if not form:
        errors.append(f"row {row_number}: empty form")
    return (not errors), errors


def validate_verb_summary_record(record: dict[str, Any], row_number: int) -> tuple[bool, list[str]]:
    """Return (is_valid, errors) for a raw HeLP verb-summary row."""
    errors: list[str] = []
    for field in ("verb_id", "root", "binyan", "forms_total"):
        if field not in record or str(record.get(field, "")).strip() == "":
            errors.append(f"row {row_number}: missing field '{field}'")
    total = record.get("forms_total")
    unique = record.get("forms_unique")
    matched = record.get("help_matched_unique")
    try:
        if total is not None and int(total) < 0:
            errors.append(f"row {row_number}: negative forms_total")
        if unique is not None and int(unique) < 0:
            errors.append(f"row {row_number}: negative forms_unique")
        if matched is not None and int(matched) < 0:
            errors.append(f"row {row_number}: negative help_matched_unique")
    except (TypeError, ValueError):
        errors.append(f"row {row_number}: numeric fields not parseable")
    return (not errors), errors


def coerce_float(value: Any) -> float | None:
    """Convert a raw scalar to float, returning None for empty/missing values."""
    if value is None or value == "":
        return None
    try:
        result = float(value)
        return None if result != result else result  # drop NaN
    except (TypeError, ValueError):
        return None


def make_form_evidence_from_row(row: dict[str, Any], provenance: HeLPProvenance) -> HeLPFormEvidence:
    """Convert a validated row dict into a typed HeLPFormEvidence."""
    return HeLPFormEvidence(
        verb_id=str(row["verb_id"]),
        root=str(row["root"]),
        binyan=str(row["binyan"]),
        italian_cue=str(row.get("italian", "")),
        slot=str(row["slot"]),
        prompt=str(row.get("prompt", row.get("slot", ""))),
        form=str(row["form"]),
        word_key=str(row["word_key"]),
        help_matched=str(row.get("help_match", "")).strip().lower() in {"true", "1", "yes"},
        frequency=coerce_float(row.get("frequency")),
        ld_mean_rt=coerce_float(row.get("ld_mean_rt")),
        ld_accuracy=coerce_float(row.get("ld_accuracy")),
        naming_mean_rt=coerce_float(row.get("naming_mean_rt")),
        naming_accuracy=coerce_float(row.get("naming_accuracy")),
        provenance=provenance,
    )


def make_verb_summary_from_row(row: dict[str, Any], provenance: HeLPProvenance) -> HeLPVerbSummary:
    """Convert a validated row dict into a typed HeLPVerbSummary."""
    return HeLPVerbSummary(
        verb_id=str(row["verb_id"]),
        root=str(row["root"]),
        binyan=str(row["binyan"]),
        italian_cue=str(row.get("italian", "")),
        forms_total=int(row.get("forms_total", 0) or 0),
        forms_unique=int(row.get("forms_unique", 0) or 0),
        help_matched_unique=int(row.get("help_matched_unique", 0) or 0),
        help_match_ratio=coerce_float(row.get("help_match_ratio")) or 0.0,
        median_frequency=coerce_float(row.get("median_frequency")),
        median_ld_mean_rt=coerce_float(row.get("median_ld_mean_rt")),
        median_ld_accuracy=coerce_float(row.get("median_ld_accuracy")),
        median_naming_mean_rt=coerce_float(row.get("median_naming_mean_rt")),
        median_naming_accuracy=coerce_float(row.get("median_naming_accuracy")),
        flags=tuple(str(f).strip() for f in row.get("flags", []) if str(f).strip()),
        matched_forms=tuple(str(f).strip() for f in row.get("matched_forms", []) if str(f).strip()),
        missing_from_help_forms=tuple(str(f).strip() for f in row.get("missing_from_help_forms", []) if str(f).strip()),
        provenance=provenance,
    )
