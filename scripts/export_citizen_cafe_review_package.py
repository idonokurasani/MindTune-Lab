#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "mindtune_console" / "data" / "citizen_cafe_all_courses"
EXPORTS = ROOT / "exports"
OUT = EXPORTS / "citizen_cafe_all_courses_review_current"

SEED = DATA / "quizlet_hebrew_seed.canonical.json"
CANONICAL = DATA / "CITIZEN_CAFE_ALL_COURSES_CANONICAL_MODEL_DRAFT_v1.1.json"
SOURCE_MAP = DATA / "CITIZEN_CAFE_ALL_COURSES_SOURCE_MAP_v1.1.json"
REVIEW = DATA / "CITIZEN_CAFE_ALL_COURSES_REVIEW_MODEL_DRAFT_v1.1.json"
COMPLETENESS = DATA / "CITIZEN_CAFE_ALL_COURSES_COMPLETENESS_REPORT_v1.1.md"
STREETWISE_PLAN = DATA / "STREETWISE_HEBREW_ENRICHMENT_PLAN_v0.1.md"

COLOR_ORDER = [
    "Red",
    "Orange",
    "Pink",
    "Yellow",
    "Light Blue",
    "Blue",
    "Lime",
    "Green",
    "Dark Green",
    "Turquoise",
    "Indigo",
    "Purple",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def deck_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    deck = str(row.get("deck") or "")
    try:
        level = COLOR_ORDER.index(deck)
    except ValueError:
        level = 999
    try:
        position = int(row.get("study_position") or 0)
    except ValueError:
        position = 0
    return level, position, str(row.get("id") or "")


def compact_row(item: dict[str, Any]) -> dict[str, Any]:
    flags = item.get("quality_flags") or []
    if isinstance(flags, list):
        flags_text = "|".join(str(flag) for flag in flags)
    else:
        flags_text = str(flags or "")
    return {
        "id": item.get("id", ""),
        "canonical_item_id": item.get("canonical_item_id", ""),
        "deck": item.get("deck", ""),
        "citizen_color": item.get("citizen_color", ""),
        "citizen_level": item.get("citizen_level", ""),
        "study_position": item.get("study_position", ""),
        "front_hebrew": item.get("raw_front") or item.get("term") or "",
        "back_italian": item.get("raw_back") or item.get("meaning") or "",
        "front_original": item.get("raw_front_original", ""),
        "back_original": item.get("raw_back_original", ""),
        "source": item.get("source", ""),
        "source_file": item.get("source_file", ""),
        "source_row": item.get("source_row", ""),
        "source_map_ref": item.get("source_map_ref", ""),
        "study_ready": "true" if item.get("study_ready") is not False else "false",
        "quality_flags": flags_text,
    }


def main() -> None:
    if not SEED.exists():
        raise SystemExit(f"missing seed: {SEED}")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    seed = read_json(SEED)
    items = sorted((compact_row(item) for item in seed.get("items", [])), key=deck_sort_key)
    ready = [row for row in items if row["study_ready"] == "true"]
    blocked = [row for row in items if row["study_ready"] == "false"]

    compact_fields = [
        "id",
        "canonical_item_id",
        "deck",
        "citizen_color",
        "citizen_level",
        "study_position",
        "front_hebrew",
        "back_italian",
        "front_original",
        "back_original",
        "source",
        "source_file",
        "source_row",
        "source_map_ref",
        "study_ready",
        "quality_flags",
    ]
    z_fields = ["deck", "front_hebrew", "back_italian", "study_ready", "quality_flags", "id", "source_file", "source_row"]

    write_csv(OUT / "citizen_cafe_all_courses_compact.csv", items, compact_fields)
    write_csv(OUT / "citizen_cafe_all_courses_study_ready_only.csv", ready, compact_fields)
    write_csv(OUT / "citizen_cafe_all_courses_blocked_review.csv", blocked, compact_fields)
    write_csv(OUT / "citizen_cafe_all_courses_for_zai.csv", items, z_fields)
    write_tsv(OUT / "citizen_cafe_all_courses_for_zai.tsv", items, z_fields)
    write_jsonl(OUT / "citizen_cafe_all_courses_blocked_review.jsonl", blocked)

    per_deck = OUT / "per_color_tsv"
    for deck in COLOR_ORDER:
        deck_rows = [row for row in items if row["deck"] == deck]
        if not deck_rows:
            continue
        filename = deck.lower().replace(" ", "_") + ".tsv"
        write_tsv(per_deck / filename, deck_rows, z_fields)

    source_files = [
        CANONICAL,
        SOURCE_MAP,
        REVIEW,
        COMPLETENESS,
        STREETWISE_PLAN,
    ]
    for path in source_files:
        if path.exists():
            shutil.copy2(path, OUT / path.name)

    ready_counts = Counter(row["deck"] for row in ready)
    blocked_counts = Counter(row["deck"] for row in blocked)
    manifest = {
        "generated_at": timestamp,
        "source_seed": str(SEED),
        "seed_schema": seed.get("schema"),
        "total_cards": len(items),
        "study_ready_cards": len(ready),
        "blocked_review_cards": len(blocked),
        "ready_by_deck": {deck: ready_counts.get(deck, 0) for deck in COLOR_ORDER},
        "blocked_by_deck": {deck: blocked_counts.get(deck, 0) for deck in COLOR_ORDER if blocked_counts.get(deck, 0)},
        "notes": [
            "UTF-8/UTF-8-SIG exports preserve Hebrew logical order.",
            "Do not edit canonical seed directly; use blocked_review files or source_map refs for corrections.",
            "Streetwise Hebrew is an enrichment source, not a canonical translation source.",
            "MLF Core is not touched by this package.",
        ],
        "files": sorted(path.name for path in OUT.iterdir() if path.is_file()),
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = [
        "# Citizen Cafe All Courses Review Package",
        "",
        f"Generated: `{timestamp}`",
        "",
        f"- Total cards: **{len(items)}**",
        f"- Study-ready cards: **{len(ready)}**",
        f"- Blocked for human review: **{len(blocked)}**",
        "",
        "## For z.ai / external review",
        "",
        "- `citizen_cafe_all_courses_for_zai.csv`",
        "- `citizen_cafe_all_courses_for_zai.tsv`",
        "- `per_color_tsv/*.tsv`",
        "",
        "## Do Not Treat As Approved Curriculum",
        "",
        "This package is structurally normalized and suitable for linguistic review. It is not a curriculum freeze.",
        "",
        "## Streetwise Hebrew",
        "",
        "`STREETWISE_HEBREW_ENRICHMENT_PLAN_v0.1.md` defines Streetwise as contextual enrichment only.",
    ]
    (OUT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    zip_path = EXPORTS / "citizen_cafe_all_courses_review_current.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(OUT.parent))

    print(f"out={OUT}")
    print(f"zip={zip_path}")
    print(f"total={len(items)} ready={len(ready)} blocked={len(blocked)}")


if __name__ == "__main__":
    main()
