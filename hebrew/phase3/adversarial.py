"""Adversarial tests for false acceptance of invalid Hebrew verb forms.

Generate mutated surfaces from valid Eran Tomer forms and verify that a simple
validator (membership in the Eran Tomer corpus) rejects them. Any mutated form
that is found in the corpus is counted as a false acceptance.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from ..normalization import normalize_hebrew, strip_niqqud
from .data_loader import Phase3DataLoader


_VOWEL_LETTERS = "\u05d5\u05d9"  # ו, י
_VALID_PREFIXES = [
    "\u05dc",  # ל
    "\u05d1",  # ב
    "\u05db",  # כ
    "\u05d5",  # ו
    "\u05d4",  # ה
    "\u05e9",  # ש
    "\u05de",  # מ
    "\u05d9",  # י
    "\u05ea",  # ת
    "\u05e0",  # נ
    "\u05d0",  # א
]
_IMPOSSIBLE_SUFFIXES = [
    "\u05e9\u05dc\u05d5\u05dd",  # שלום
    "\u05e6\u05e5",  # ץץ
    "\u05ea\u05ea",  # תת
    "\u05e0\u05e0",  # ננ
    "\u05d3\u05d2",  # דג
    "\u05e9\u05de\u05e9",  # שמש
]


def _remove_vowel_letter(surface: str, rng: random.Random) -> str | None:
    indices = [i for i, ch in enumerate(surface) if ch in _VOWEL_LETTERS]
    if not indices:
        return None
    i = rng.choice(indices)
    return surface[:i] + surface[i + 1 :]


def _swap_radicals(surface: str, root: str, rng: random.Random) -> str | None:
    r = strip_niqqud(root).replace("'", "").replace("\u05f3", "").strip()
    if len(r) >= 2:
        distinct = []
        seen = set()
        for ch in r:
            if ch not in seen:
                distinct.append(ch)
                seen.add(ch)
        if len(distinct) >= 2:
            a, b = distinct[0], distinct[-1]
            try:
                i = surface.index(a)
            except ValueError:
                i = -1
            try:
                j = surface.rindex(b)
            except ValueError:
                j = -1
            if i >= 0 and j >= 0 and i != j:
                chars = list(surface)
                chars[i], chars[j] = chars[j], chars[i]
                return "".join(chars)
    return None


def _add_impossible_suffix(surface: str, rng: random.Random) -> str:
    return surface + rng.choice(_IMPOSSIBLE_SUFFIXES)


def _replace_valid_prefix(surface: str, rng: random.Random) -> str | None:
    if not surface or surface[0] not in _VALID_PREFIXES:
        return None
    original = surface[0]
    replacement = original
    while replacement == original:
        replacement = rng.choice(_VALID_PREFIXES)
    return replacement + surface[1:]


def _mutate(
    surface: str,
    root: str,
    mutation_type: str,
    rng: random.Random,
) -> str | None:
    if mutation_type == "remove_vowel_letter":
        return _remove_vowel_letter(surface, rng)
    if mutation_type == "swap_radicals":
        return _swap_radicals(surface, root, rng)
    if mutation_type == "add_impossible_suffix":
        return _add_impossible_suffix(surface, rng)
    if mutation_type == "replace_valid_prefix":
        return _replace_valid_prefix(surface, rng)
    return None


def run_adversarial_tests(loader: Phase3DataLoader, sample_size: int = 500) -> dict[str, Any]:
    """Generate adversarial invalid forms and measure false acceptance.

    Returns a report with the number of mutations attempted, false acceptance
    counts by mutation type, and example mutations that were falsely accepted.
    """
    eran_rows = loader.eran_rows()
    corpus_surfaces = {normalize_hebrew(r["vocalized_inflection"]) for r in eran_rows}

    n = min(sample_size, len(eran_rows))
    rng = random.Random(42)
    sample = rng.sample(eran_rows, n) if n < len(eran_rows) else eran_rows

    mutation_types = [
        "remove_vowel_letter",
        "swap_radicals",
        "add_impossible_suffix",
        "replace_valid_prefix",
    ]

    counts: dict[str, int] = {m: 0 for m in mutation_types}
    false_counts: dict[str, int] = {m: 0 for m in mutation_types}
    false_examples: list[dict[str, Any]] = []
    rejected_examples: list[dict[str, Any]] = []

    for row in sample:
        surface = normalize_hebrew(row["vocalized_inflection"])
        base_plain = strip_niqqud(row["base_form"])
        try:
            table_number = int(row["table_number"])
        except ValueError:
            table_number = 0
        root = loader.get_root(row["pattern"], table_number, base_plain)

        for mutation_type in mutation_types:
            mutated = _mutate(surface, root, mutation_type, rng)
            if not mutated or mutated == surface:
                continue
            counts[mutation_type] += 1
            if mutated in corpus_surfaces:
                false_counts[mutation_type] += 1
                if len(false_examples) < 10:
                    false_examples.append(
                        {
                            "mutation_type": mutation_type,
                            "original": surface,
                            "mutated": mutated,
                            "morphology": row["morphology"],
                        }
                    )
            else:
                if len(rejected_examples) < 10:
                    rejected_examples.append(
                        {
                            "mutation_type": mutation_type,
                            "original": surface,
                            "mutated": mutated,
                            "morphology": row["morphology"],
                        }
                    )

    total = sum(counts.values())
    false_total = sum(false_counts.values())
    rate = false_total / total if total else 0.0

    return {
        "sample_size": n,
        "mutation_types": mutation_types,
        "mutation_counts": counts,
        "total_mutations": total,
        "false_acceptance_count": false_total,
        "false_acceptance_by_type": false_counts,
        "false_acceptance_rate": rate,
        "false_acceptance_examples": false_examples,
        "rejected_examples": rejected_examples,
    }
