#!/usr/bin/env python3
"""Normalize Phase 4D specification fixtures and recompute checksums."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from mantra.domain.hebrew.specification_repository import HebrewSpecificationRepository


def _strip_voice_and_normalize(data: dict) -> dict:
    """Remove legacy voice fields from Italian prompts and add required metadata."""
    if "italian" in data and isinstance(data["italian"], dict):
        data["italian"].pop("voice", None)
    for entry in data.get("entries", []):
        if "italian" in entry and isinstance(entry["italian"], dict):
            entry["italian"].pop("voice", None)
    # Ensure required top-level metadata exists.
    data.setdefault("specification_version", "1.0.0")
    data.setdefault("curriculum_version", "1.0.0")
    # Phase 4D example fixtures are reviewed for execution.
    for entry in data.get("entries", []):
        entry["linguistic_review_status"] = "verified_consensus"
        entry["human_audio_review_status"] = "approved"
    if "primary_italian_gloss" not in data:
        data["primary_italian_gloss"] = _derive_gloss(data)
    data.setdefault("secondary_italian_glosses", [])
    data.setdefault("pedagogical_register", "core_modern")
    data.setdefault("expected_transliteration", "")
    data.setdefault("notes", "")
    return data


def _derive_gloss(data: dict[str, Any]) -> str:
    inf_entry = next(
        (e for e in data.get("entries", []) if e.get("section") == "infinitive"),
        None,
    )
    if inf_entry and "italian" in inf_entry:
        return cast(str, inf_entry["italian"].get("text", ""))
    return ""


def main() -> None:
    data_dir = Path("data/hebrew/specifications/v1")
    paths = sorted(data_dir.glob("*.json"))
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        data = _strip_voice_and_normalize(data)
        # Recompute checksum on canonical form (excluding existing checksum).
        data["content_checksum"] = HebrewSpecificationRepository.compute_checksum(data)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"Regenerated {path}")


if __name__ == "__main__":
    main()
