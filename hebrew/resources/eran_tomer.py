"""Ingest and index the Eran Tomer Vocalized Verb Dataset."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
from ..morphology import binyan_from_pattern, parse_morphology_tag


@dataclass
class EranTomerRecord:
    pattern: str
    table_number: int
    surface_vocalized: str
    morphology: str
    base_form_vocalized: str
    binyan: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_records(csv_path: Path) -> tuple[list[EranTomerRecord], list[dict[str, Any]]]:
    """Parse the extended CSV, returning accepted and rejected rows."""
    records: list[EranTomerRecord] = []
    rejected: list[dict[str, Any]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=2):
            try:
                pattern = (row.get("pattern") or "").strip()
                table_str = (row.get("table_number") or "").strip()
                surface = normalize_hebrew((row.get("vocalized_inflection") or "").strip())
                morph = (row.get("morphology") or "").strip()
                base = normalize_hebrew((row.get("base_form") or "").strip())

                if not all([pattern, table_str, surface, morph, base]):
                    rejected.append({"line": idx, "reason": "missing field", "row": row})
                    continue

                table_number = int(table_str)
                records.append(
                    EranTomerRecord(
                        pattern=pattern,
                        table_number=table_number,
                        surface_vocalized=surface,
                        morphology=morph,
                        base_form_vocalized=base,
                        binyan=binyan_from_pattern(pattern),
                    )
                )
            except Exception as exc:
                rejected.append({"line": idx, "reason": str(exc), "row": row})

    return records, rejected


def build_indexes(records: list[EranTomerRecord]) -> dict[str, Any]:
    """Build multiple lookup indexes."""
    by_surface_vocalized: dict[str, list[int]] = defaultdict(list)
    by_surface_plain: dict[str, list[int]] = defaultdict(list)
    by_base_vocalized: dict[str, list[int]] = defaultdict(list)
    by_base_plain: dict[str, list[int]] = defaultdict(list)
    by_pattern: dict[str, list[int]] = defaultdict(list)
    by_tense: dict[str, list[int]] = defaultdict(list)
    by_gender: dict[str, list[int]] = defaultdict(list)
    by_number: dict[str, list[int]] = defaultdict(list)

    for i, rec in enumerate(records):
        surf_plain = strip_niqqud(rec.surface_vocalized)
        base_plain = strip_niqqud(rec.base_form_vocalized)
        by_surface_vocalized[rec.surface_vocalized].append(i)
        by_surface_plain[surf_plain].append(i)
        by_base_vocalized[rec.base_form_vocalized].append(i)
        by_base_plain[base_plain].append(i)
        by_pattern[rec.pattern].append(i)

        features = parse_morphology_tag(rec.morphology, rec.pattern, rec.table_number)
        if features.tense:
            by_tense[features.tense].append(i)
        if features.gender:
            by_gender[features.gender].append(i)
        if features.number:
            by_number[features.number].append(i)

    return {
        "by_surface_vocalized": dict(by_surface_vocalized),
        "by_surface_plain": dict(by_surface_plain),
        "by_base_vocalized": dict(by_base_vocalized),
        "by_base_plain": dict(by_base_plain),
        "by_pattern": dict(by_pattern),
        "by_tense": dict(by_tense),
        "by_gender": dict(by_gender),
        "by_number": dict(by_number),
    }


def ingest(
    resource_dir: Path,
    output_dir: Path,
) -> Path:
    """Ingest Eran Tomer CSV, write normalized records, indexes and manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = resource_dir / "InflectedVerbsExtended.csv"
    records, rejected = load_records(csv_path)

    # Serialize records as plain dicts for JSON storage
    record_dicts = [r.as_dict() for r in records]
    indexes = build_indexes(records)

    (output_dir / "records.json").write_text(
        json.dumps(record_dicts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "indexes.json").write_text(
        json.dumps(indexes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "rejected.json").write_text(
        json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manifest = {
        "resource_name": "eran_tomer_vocalized_verbs",
        "upstream_url": "https://github.com/NLPH/NLPH_Resources/tree/master/linguistic_resources/word_lists/hebrew_verbs_eran_tomer",
        "version_or_commit": "unknown",
        "license": "CC BY 4.0",
        "import_date": datetime.now(timezone.utc).isoformat(),
        "file_hashes": {
            "InflectedVerbsExtended.csv": _sha256(csv_path),
            "TheVerbIndex.csv": _sha256(resource_dir / "TheVerbIndex.csv"),
        },
        "total_records": len(records) + len(rejected),
        "accepted_records": len(records),
        "rejected_records": len(rejected),
        "normalization_rules": [
            "NFC Unicode normalization",
            "strip maqaf",
            "collapse whitespace",
        ],
        "parser_version": "hebrew.resources.eran_tomer.v1",
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path
