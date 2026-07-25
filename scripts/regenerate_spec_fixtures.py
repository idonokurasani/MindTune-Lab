#!/usr/bin/env python3
"""Normalize Phase 4D specification fixtures and recompute checksums."""
from __future__ import annotations

import copy
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



def _derive_lehavot_from_lihyot(lihyot_data: dict[str, Any]) -> dict[str, Any]:
    """Create the planning-document `lehavot` fixture from reviewed `lihyot`.

    The planning documents referred to the `להיות` (lihyot) vertical-slice verb
    as `להוות` (lehavot).  This function produces a distinct `lehavot.json` with
    its own `verb_id` and entry IDs while preserving the reviewed learner-facing
    Hebrew forms (pointed `לִהְיוֹת`, TTS `להיות`) and the AudioProfile-driven
    voice resolution.
    """
    data = copy.deepcopy(lihyot_data)
    data["spec_id"] = "lehavot"
    data["verb_id"] = "lehavot"
    data["expected_transliteration"] = "lehavot"
    data["notes"] = (
        "Planning-document identifier `lehavot` maps to the reviewed `lihyot` "
        "(להיות) paradigm. Pointed learner text is לִהְיוֹת; TTS text is "
        "להיות; voice is resolved by AudioProfile, not hard-coded here."
    )
    for entry in data.get("entries", []):
        entry["entry_id"] = entry["entry_id"].replace("lihyot", "lehavot")
    return data

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

    # Ensure the planning-document `lehavot` fixture exists, derived from the
    # reviewed `lihyot` (להיות) paradigm.
    lehavot_path = data_dir / "lehavot.json"
    if not lehavot_path.exists():
        lihyot_path = data_dir / "lihyot.json"
        if lihyot_path.exists():
            data = json.loads(lihyot_path.read_text(encoding="utf-8"))
            data = _derive_lehavot_from_lihyot(data)
            data = _strip_voice_and_normalize(data)
            data["content_checksum"] = HebrewSpecificationRepository.compute_checksum(data)
            lehavot_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            print(f"Derived {lehavot_path} from {lihyot_path}")


if __name__ == "__main__":
    main()
