"""Select a diverse, high-frequency 100-verb expansion set.

The selection maximizes corpus frequency while covering the seven binyanim and
major weak-root classes.  It does not promote any verb to verified_consensus;
that decision is made later by the evidence pipeline.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..morphology import (
    binyan_from_pattern,
    morphology_features_to_form_key,
    parse_morphology_tag,
)
from ..normalization import strip_niqqud
from .data_loader import Phase3DataLoader


def _root_plain(root: str) -> str:
    return strip_niqqud(root).replace("'", "").replace("\u05f3", "")


def classify_root(root: str) -> dict[str, bool]:
    """Classify a stripped root string into weak-root features."""
    r = _root_plain(root)
    if not r:
        return {}

    letters = list(r)
    gutturals = {"א", "ה", "ח", "ע"}
    initial_nun = letters[0] == "נ" if letters else False
    contains_yod_vav = any(c in {"י", "ו"} for c in letters)
    final_he = letters[-1] == "ה" if letters else False
    hollow = (
        len(letters) == 3 and letters[1] in {"ו", "י"}
    ) or (
        len(letters) == 2 and letters[0] in {"ב", "ר", "ש"}
    )
    geminate = (
        len(letters) == 3 and letters[0] == letters[1]
    ) or (
        len(letters) == 3 and letters[1] == letters[2]
    )
    quadriliteral = len(letters) >= 4
    irregular = r in {"היה", "הוה", "ראה", "עשה"}

    return {
        "guttural": any(c in gutturals for c in letters),
        "initial_nun": initial_nun,
        "contains_yod_vav": contains_yod_vav,
        "final_he": final_he,
        "hollow": hollow,
        "geminate": geminate,
        "quadriliteral": quadriliteral,
        "irregular": irregular,
    }


def _group_frequency(
    group_rows: list[dict], counts: dict, pattern: str, table_number: int
) -> tuple[int, int, str, str]:
    """Return infinitive frequency, total frequency, infinitive surface, and representative plain surface."""
    infinitive_plain = ""
    representative_plain = ""
    infinitive_frequency = 0
    total = 0
    for row in group_rows:
        plain = strip_niqqud(row["vocalized_inflection"])
        morph = row["morphology"]
        features = parse_morphology_tag(morph, pattern, table_number)
        form_key = morphology_features_to_form_key(features)
        cnt = counts.get((plain, form_key), 1)
        total += cnt
        if form_key == "infinitive":
            infinitive_frequency += cnt
            if not infinitive_plain:
                infinitive_plain = plain
        if not representative_plain and form_key.startswith("past_"):
            representative_plain = plain
    if not representative_plain and group_rows:
        representative_plain = strip_niqqud(group_rows[0]["vocalized_inflection"])
    return infinitive_frequency, total, infinitive_plain, representative_plain


def select_100_verbs(
    loader: Phase3DataLoader | None = None,
    target_size: int = 100,
) -> list[dict]:
    """Return a ranked list of at least target_size candidate verb groups.

    Each item contains group_key, verb_label (infinitive or base form),
    frequency, root, binyan, pattern, table_number, root_class, and
    selection_reason.
    """
    if loader is None:
        loader = Phase3DataLoader()
        loader.load_all()

    counts = loader.corpus_counts()
    groups = loader.verb_groups()

    candidates: list[dict] = []
    for (pattern, table_number, base_form), rows in groups.items():
        inf_freq, total, infinitive_plain, representative_plain = _group_frequency(
            rows, counts, pattern, table_number
        )
        root = loader.get_root(pattern, table_number, base_form) or base_form
        binyan = binyan_from_pattern(pattern)
        root_class = classify_root(root)
        label = infinitive_plain if infinitive_plain else representative_plain
        candidates.append(
            {
                "group_key": f"{pattern}_{table_number}_{base_form}",
                "verb_label": label,
                "infinitive_plain": infinitive_plain,
                "representative_plain": representative_plain,
                "infinitive_frequency": inf_freq,
                "frequency": total,
                "root": root,
                "binyan": binyan,
                "pattern": pattern,
                "table_number": table_number,
                "base_form_plain": base_form,
                "root_class": root_class,
            }
        )

    # Sort primarily by infinitive frequency; verbs with no infinitive drop to the
    # bottom so that the expansion set is verb-first and high-frequency-first.
    candidates.sort(key=lambda x: (x["infinitive_frequency"] == 0, -x["infinitive_frequency"], -x["frequency"]))

    by_binyan: dict[str, list[dict]] = defaultdict(list)
    by_root_class: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        by_binyan[c["binyan"]].append(c)
        for rc, val in c["root_class"].items():
            if val:
                by_root_class[rc].append(c)

    selected: list[dict] = []
    seen_key: set[str] = set()
    seen_verb: set[tuple[str, str]] = set()
    seen_binyan: set[str] = set()
    seen_root_class: dict[str, set[str]] = defaultdict(set)
    order_index: dict[str, int] = {}

    def _coverage_reasons(c: dict) -> list[str]:
        reasons: list[str] = []
        b = c["binyan"]
        if b not in seen_binyan:
            reasons.append(f"binyan_{b}")
        for rc, val in c["root_class"].items():
            if val and c["group_key"] not in seen_root_class[rc]:
                reasons.append(f"root_class_{rc}")
        return reasons

    def _pick(c: dict, reasons: list[str]) -> None:
        if c["group_key"] in seen_key:
            return
        verb_id = (c["root"], c["binyan"])
        if verb_id in seen_verb:
            return
        c = dict(c)
        c["selection_reason"] = reasons
        selected.append(c)
        seen_key.add(c["group_key"])
        seen_verb.add(verb_id)
        seen_binyan.add(c["binyan"])
        for rc, val in c["root_class"].items():
            if val:
                seen_root_class[rc].add(c["group_key"])
        order_index[c["group_key"]] = len(order_index)

    # Coverage pass: ensure every binyan and every root class is represented.
    all_binyanim = sorted(set(by_binyan.keys()))
    all_root_classes = sorted(set(by_root_class.keys()))

    for b in all_binyanim:
        if b not in seen_binyan:
            for c in by_binyan[b]:
                reasons = _coverage_reasons(c)
                if reasons:
                    _pick(c, reasons)
                    break

    for rc in all_root_classes:
        if rc not in seen_root_class or len(seen_root_class[rc]) == 0:
            for c in by_root_class[rc]:
                reasons = _coverage_reasons(c)
                if reasons:
                    _pick(c, reasons)
                    break

    # Fill remaining slots by frequency up to target_size.
    for c in candidates:
        if len(selected) >= target_size:
            break
        if c["group_key"] in seen_key:
            continue
        _pick(c, ["frequency"])

    # Stable sort: coverage picks first, then frequency.
    selected.sort(key=lambda c: (order_index.get(c["group_key"], 10**9), -c["frequency"]))
    return selected


def coverage_summary(selected: list[dict]) -> dict[str, Any]:
    from collections import Counter

    bins = Counter(v["binyan"] for v in selected)
    rc = Counter()
    for v in selected:
        for k, val in v["root_class"].items():
            if val:
                rc[k] += 1
    return {
        "count": len(selected),
        "binyan": dict(bins),
        "root_class": dict(rc),
        "no_infinitive": sum(1 for v in selected if not v["infinitive_plain"]),
    }
