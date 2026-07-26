"""Provenance helpers for HeLP-derived evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import HeLPProvenance


def _file_version(path: Path | None) -> str:
    """Use mtime as a simple deterministic version when no explicit schema version exists."""
    if not path or not path.exists():
        return "unknown"
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime.strftime("%Y%m%d.%H%M%S")


def make_help_provenance(
    dataset_path: Path | None = None,
    source_row_id: str = "",
    original_lexical_form: str = "",
    normalized_lexical_form: str = "",
    lemma: str = "",
    root: str = "",
    morphological_analysis: str = "",
    measurement_name: str = "",
    measurement_value: str = "",
    units: str = "",
    missing_value: bool = False,
    transformation: str = "",
    explicit_version: str = "",
) -> HeLPProvenance:
    """Build a HeLP provenance record with an import timestamp."""
    import_ts = datetime.now(timezone.utc).isoformat()
    return HeLPProvenance(
        source_name="HeLP",
        dataset_version=explicit_version or _file_version(dataset_path),
        source_row_id=source_row_id,
        import_timestamp=import_ts,
        original_lexical_form=original_lexical_form,
        normalized_lexical_form=normalized_lexical_form,
        lemma=lemma,
        root=root,
        morphological_analysis=morphological_analysis,
        original_measurement_name=measurement_name,
        original_measurement_value=str(measurement_value) if measurement_value is not None else "",
        units=units,
        missing_value=missing_value,
        transformation=transformation,
    )


def provenance_from_record(
    record: dict[str, Any],
    dataset_path: Path | None = None,
    explicit_version: str = "",
) -> HeLPProvenance:
    """Create a provenance object from a raw HeLP record."""
    return make_help_provenance(
        dataset_path=dataset_path,
        source_row_id=str(record.get("verb_id", record.get("word_key", ""))),
        original_lexical_form=str(record.get("form", record.get("hebrew", ""))),
        normalized_lexical_form=str(record.get("word_key", record.get("form", ""))),
        lemma=str(record.get("italian", record.get("lemma", ""))),
        root=str(record.get("root", "")),
        morphological_analysis=f"slot={record.get('slot', '')}; binyan={record.get('binyan', '')}",
        measurement_name="record",
        measurement_value="",
        units="",
        missing_value=False,
        transformation="raw_import",
        explicit_version=explicit_version or str(record.get("schema_version", "")),
    )
