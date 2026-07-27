"""Differential analysis between Eran Tomer and the Verb Inflector.

Both data sets are expected to be identical because the Eran Tomer CSV was
produced by the Verb Inflector. This module still detects and reports any
mismatches or derivation differences.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..normalization import normalize_hebrew
from .data_loader import Phase3DataLoader


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _verb_inflector_forms_path() -> Path:
    return (
        _repo_root()
        / "data"
        / "hebrew_resources"
        / "vendor"
        / "Hebrew-Resources"
        / "code"
        / "VerbInflector"
        / "resources"
        / "Inflected verbs Extended.txt"
    )


def _load_verb_inflector_forms() -> list[dict[str, str]]:
    """Load the Verb Inflector generated forms from its resource file."""
    path = _verb_inflector_forms_path()
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for cells in csv.reader(f):
            if len(cells) != 5:
                continue
            rows.append(
                {
                    "pattern": cells[0],
                    "table_number": cells[1],
                    "vocalized_inflection": cells[2],
                    "morphology": cells[3],
                    "base_form": cells[4],
                }
            )
    return rows


def _row_signature(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["pattern"],
        row["table_number"],
        normalize_hebrew(row["vocalized_inflection"]),
        row["morphology"],
        normalize_hebrew(row["base_form"]),
    )


def run_differential_analysis(loader: Phase3DataLoader) -> dict[str, Any]:
    """Compare every Eran Tomer row with the Verb Inflector output.

    Returns a report with agreement/disagreement counts and a sample list of
    mismatches. A disagreement means a (pattern, table, surface, morphology,
    base_form) signature appears in one source but not the other.
    """
    eran_rows = loader.eran_rows()
    inflector_rows = _load_verb_inflector_forms()

    eran_set = {_row_signature(r) for r in eran_rows}
    inflector_set = {_row_signature(r) for r in inflector_rows}

    agreement = eran_set & inflector_set
    only_in_eran = eran_set - inflector_set
    only_in_inflector = inflector_set - eran_set

    sample: list[dict[str, Any]] = []
    for sig in list(only_in_eran)[:5]:
        sample.append(
            {
                "side": "eran_only",
                "pattern": sig[0],
                "table_number": sig[1],
                "surface_vocalized": sig[2],
                "morphology": sig[3],
                "base_form": sig[4],
            }
        )
    for sig in list(only_in_inflector)[:5]:
        sample.append(
            {
                "side": "inflector_only",
                "pattern": sig[0],
                "table_number": sig[1],
                "surface_vocalized": sig[2],
                "morphology": sig[3],
                "base_form": sig[4],
            }
        )

    return {
        "eran_count": len(eran_set),
        "inflector_count": len(inflector_set),
        "agreement_count": len(agreement),
        "disagreement_count": len(only_in_eran) + len(only_in_inflector),
        "only_in_eran": len(only_in_eran),
        "only_in_inflector": len(only_in_inflector),
        "sample_disagreements": sample,
    }
