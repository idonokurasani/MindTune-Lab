"""Property-based round-trip tests for morphology tags and surface forms.

For a sample of Eran Tomer rows, parse the morphology tag into
MorphologicalFeatures, convert it to a form key, and check whether the Verb
Inflector can reconstruct the expected surface for that form key. Because a
single form key can map to multiple orthographic variants, a round-trip succeeds
when the expected surface appears in the generated set.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..morphology import binyan_from_pattern, morphology_features_to_form_key, parse_morphology_tag
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


def _build_generated_surface_map() -> dict[tuple[str, str, str, str], set[str]]:
    """Map (pattern, table, base_form, form_key) to the set of generated surfaces."""
    generated: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    path = _verb_inflector_forms_path()
    with path.open("r", encoding="utf-8", newline="") as f:
        for cells in csv.reader(f):
            if len(cells) != 5:
                continue
            pattern, table_str, surface, morph, base_form = cells
            try:
                table_number = int(table_str)
            except ValueError:
                continue
            features = parse_morphology_tag(morph, pattern, table_number)
            form_key = morphology_features_to_form_key(features)
            generated[(pattern, table_str, base_form, form_key)].add(normalize_hebrew(surface))
    return generated


def run_round_trip_tests(loader: Phase3DataLoader, sample_size: int = 1000) -> dict[str, Any]:
    """Run round-trip tests on a sample of Eran Tomer rows.

    Returns a report with total successes/failures and per-binyan/per-form-key
    breakdowns. Each breakdown includes success and failure counts and a few
    examples of each.
    """
    eran_rows = loader.eran_rows()
    generated = _build_generated_surface_map()

    n = min(sample_size, len(eran_rows))
    rng = random.Random(0)
    sample = rng.sample(eran_rows, n) if n < len(eran_rows) else eran_rows

    successes = 0
    failures = 0
    by_binyan: dict[str, Any] = defaultdict(
        lambda: {"success": 0, "failure": 0, "success_examples": [], "failure_examples": []}
    )
    by_form_key: dict[str, Any] = defaultdict(
        lambda: {"success": 0, "failure": 0, "success_examples": [], "failure_examples": []}
    )

    for row in sample:
        pattern = row["pattern"]
        table_str = row["table_number"]
        try:
            table_number = int(table_str)
        except ValueError:
            continue
        base_form = row["base_form"]
        expected = normalize_hebrew(row["vocalized_inflection"])
        morph = row["morphology"]

        features = parse_morphology_tag(morph, pattern, table_number)
        form_key = morphology_features_to_form_key(features)
        binyan = binyan_from_pattern(pattern)

        generated_surfaces = generated.get((pattern, table_str, base_form, form_key), set())
        success = expected in generated_surfaces

        if success:
            successes += 1
            target = "success"
        else:
            failures += 1
            target = "failure"

        entry_b = by_binyan[binyan]
        entry_b[target] += 1
        if len(entry_b[f"{target}_examples"]) < 3:
            entry_b[f"{target}_examples"].append(
                {
                    "surface_vocalized": expected,
                    "morphology": morph,
                    "form_key": form_key,
                    "generated_surfaces": sorted(generated_surfaces)[:10] if not success else [],
                }
            )

        entry_f = by_form_key[form_key]
        entry_f[target] += 1
        if len(entry_f[f"{target}_examples"]) < 3:
            entry_f[f"{target}_examples"].append(
                {
                    "surface_vocalized": expected,
                    "morphology": morph,
                    "binyan": binyan,
                    "generated_surfaces": sorted(generated_surfaces)[:10] if not success else [],
                }
            )

    return {
        "total_available": len(eran_rows),
        "sample_size": n,
        "successes": successes,
        "failures": failures,
        "by_binyan": {k: dict(v) for k, v in by_binyan.items()},
        "by_form_key": {k: dict(v) for k, v in by_form_key.items()},
    }
