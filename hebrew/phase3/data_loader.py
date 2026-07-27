"""Load and index Phase 3 source data.

Data sources:
- Eran Tomer InflectedVerbsExtended.csv (production_approved)
- Eran Tomer TheVerbIndex.csv (production_approved)
- Verb Inflector verbCountsFromCorpora.txt (corpus frequency evidence)
- Phase 2 gold fixtures (immutable baseline)
- Pealim reference (reference_only)
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..normalization import normalize_hebrew, strip_niqqud


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def _eran_dir() -> Path:
    return _repo() / "data" / "hebrew" / "resources" / "eran_tomer"


def _verb_inflector_resources() -> Path:
    return (
        _repo()
        / "data"
        / "hebrew_resources"
        / "vendor"
        / "Hebrew-Resources"
        / "code"
        / "VerbInflector"
        / "resources"
    )


def _gold_dir() -> Path:
    return _repo() / "data" / "hebrew" / "gold_verbs"


def _pealim_path() -> Path:
    return _repo() / "data" / "hebrew" / "resources" / "pealim" / "pealim_forms.json"


def _root_plain(root: str) -> str:
    """Normalize index root for matching (strip niqqud and apostrophe hints)."""
    return strip_niqqud(root).replace("'", "").replace("\u05f3", "")


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class Phase3DataLoader:
    """Central data loader for Phase 3."""

    def __init__(self) -> None:
        self._eran_rows: list[dict[str, str]] | None = None
        self._index_rows: list[dict[str, str]] | None = None
        self._index: dict[tuple[str, int, str], str] | None = None
        self._verb_groups: dict[tuple[str, int, str], list[dict[str, str]]] | None = None
        self._infinitive_to_group: dict[str, tuple[tuple[str, int, str], str, int]] | None = None
        self._corpus_counts: dict[tuple[str, str], int] | None = None
        self._gold_fixtures: dict[str, dict[str, Any]] | None = None
        self._pealim: dict[str, Any] | None = None

    def load_all(self) -> None:
        self._load_eran()
        self._load_index()
        self._build_groups()
        self._load_corpus()
        self._load_gold()
        self._load_pealim()

    def _load_eran(self) -> None:
        path = _eran_dir() / "InflectedVerbsExtended.csv"
        self._eran_rows = _load_csv(path)

    def _load_index(self) -> None:
        path = _eran_dir() / "TheVerbIndex.csv"
        self._index_rows = _load_csv(path)
        self._index = {}
        for row in self._index_rows:
            try:
                table = int(row["table_number_1"])
            except ValueError:
                continue
            key = (row["pattern_1"], table, _root_plain(row["base_form"]))
            self._index[key] = row["base_form"]

    def _build_groups(self) -> None:
        groups: dict[tuple[str, int, str], list[dict[str, str]]] = defaultdict(list)
        for row in self._eran_rows or []:
            try:
                table = int(row["table_number"])
            except ValueError:
                continue
            base_plain = strip_niqqud(row["base_form"])
            key = (row["pattern"], table, base_plain)
            groups[key].append(row)
        self._verb_groups = dict(groups)
        self._infinitive_to_group = {}
        for key, rows in self._verb_groups.items():
            infs = [r for r in rows if r["morphology"].startswith("INFINITIVE")]
            if not infs:
                continue
            inf_plain = normalize_hebrew(strip_niqqud(infs[0]["vocalized_inflection"]))
            root = self._index.get((key[0], key[1], key[2]))
            if root is None:
                # fallback: try matching index with apostrophe-normalized root equal to base_plain
                for (p, t, rplain), r in (self._index or {}).items():
                    if p == key[0] and t == key[1] and rplain == key[2]:
                        root = r
                        break
            self._infinitive_to_group[inf_plain] = (key, root or "", len(infs))

    def _load_corpus(self) -> None:
        path = _verb_inflector_resources() / "verbCountsFromCorpora.txt"
        self._corpus_counts = {}
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                form_tag, count_str = line.rsplit(":", 1)
                try:
                    count = int(count_str)
                except ValueError:
                    continue
                cells = form_tag.split(",")
                if len(cells) < 2:
                    continue
                surface = normalize_hebrew(cells[0])
                tense = cells[1].strip().upper()
                features = self._normalize_corpus_features(tense, cells[2:])
                self._corpus_counts[(surface, features)] = (
                    self._corpus_counts.get((surface, features), 0) + count
                )

    @staticmethod
    def _normalize_corpus_features(tense: str, cells: list[str]) -> str:
        """Normalize corpus morphological cells to a form_key-like string."""

        # cells order depends on tense:
        # PAST/FUTURE/IMPERATIVE: gender, person, number
        # BEINONI (present): gender, person (A=any), number
        # INFINITIVE: E,E,E
        def norm_g(s: str) -> str:
            s = s.strip().upper()
            if s == "M":
                return "m"
            if s == "F":
                return "f"
            if s in ("MF", "M+F"):
                return "mf"
            return ""

        def norm_p(s: str) -> str:
            s = s.strip().upper()
            if s == "ONE":
                return "first"
            if s == "TWO":
                return "second"
            if s == "THREE":
                return "third"
            return ""

        def norm_n(s: str) -> str:
            s = s.strip().upper()
            if s == "S":
                return "singular"
            if s == "P":
                return "plural"
            return ""

        if tense == "INFINITIVE":
            return "infinitive"
        if tense == "BEINONI":
            # BEINONI corresponds to present; person is A (any)
            g = norm_g(cells[0]) if len(cells) > 0 else ""
            n = norm_n(cells[2]) if len(cells) > 2 else ""
            if g and n:
                return f"present_{g}_{n}"
            return f"present_{g}_{n}"
        if tense == "PAST":
            g = norm_g(cells[0]) if len(cells) > 0 else ""
            p = norm_p(cells[1]) if len(cells) > 1 else ""
            n = norm_n(cells[2]) if len(cells) > 2 else ""
            return f"past_{p}_{g}_{n}" if p else f"past_{g}_{n}"
        if tense == "FUTURE":
            g = norm_g(cells[0]) if len(cells) > 0 else ""
            p = norm_p(cells[1]) if len(cells) > 1 else ""
            n = norm_n(cells[2]) if len(cells) > 2 else ""
            return f"future_{p}_{g}_{n}" if p else f"future_{g}_{n}"
        if tense == "IMPERATIVE":
            g = norm_g(cells[0]) if len(cells) > 0 else ""
            p = norm_p(cells[1]) if len(cells) > 1 else ""
            n = norm_n(cells[2]) if len(cells) > 2 else ""
            return f"imperative_{p}_{g}_{n}" if p else f"imperative_{g}_{n}"
        return tense.lower()

    def _load_gold(self) -> None:
        self._gold_fixtures = {}
        if not _gold_dir().exists():
            return
        for path in sorted(_gold_dir().glob("*.json")):
            if path.name == "manifest.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            lemma = data.get("lemma_plain") or data.get("approved_lemma", "")
            self._gold_fixtures[strip_niqqud(lemma)] = data

    def _load_pealim(self) -> None:
        path = _pealim_path()
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._pealim = (
                raw
                if isinstance(raw, dict)
                else {
                    item["query"]: item
                    for item in raw
                    if isinstance(item, dict) and "query" in item
                }
            )

    def eran_rows(self) -> list[dict[str, str]]:
        if self._eran_rows is None:
            self._load_eran()
        return self._eran_rows or []

    def verb_groups(self) -> dict[tuple[str, int, str], list[dict[str, str]]]:
        if self._verb_groups is None:
            self._load_eran()
            self._build_groups()
        return self._verb_groups or {}

    def infinitive_to_group(self) -> dict[str, tuple[tuple[str, int, str], str, int]]:
        if self._infinitive_to_group is None:
            self._load_eran()
            self._load_index()
            self._build_groups()
        return self._infinitive_to_group or {}

    def corpus_counts(self) -> dict[tuple[str, str], int]:
        if self._corpus_counts is None:
            self._load_corpus()
        return self._corpus_counts or {}

    def gold_fixtures(self) -> dict[str, dict[str, Any]]:
        if self._gold_fixtures is None:
            self._load_gold()
        return self._gold_fixtures or {}

    def pealim(self) -> dict[str, Any]:
        if self._pealim is None:
            self._load_pealim()
        return self._pealim or {}

    def get_corpus_count(self, surface_plain: str, form_key: str) -> int:
        """Return exact corpus count for a surface + form_key."""
        counts = self.corpus_counts()
        surface = normalize_hebrew(surface_plain)
        return counts.get((surface, form_key), 0)

    def list_verbs(self) -> list[dict[str, Any]]:
        """List all verbs that have an infinitive form."""
        items: list[dict[str, Any]] = []
        for inf, (key, root, inf_count) in self.infinitive_to_group().items():
            rows = self.verb_groups()[key]
            items.append(
                {
                    "infinitive_plain": inf,
                    "pattern": key[0],
                    "table_number": key[1],
                    "base_form_plain": key[2],
                    "root": root,
                    "infinitive_vocalized": rows[0]["vocalized_inflection"] if rows else "",
                    "form_count": len(rows),
                }
            )
        return items

    def get_verb_rows(self, pattern: str, table: int, base_form_plain: str) -> list[dict[str, str]]:
        return self.verb_groups().get((pattern, table, base_form_plain), [])

    def get_root(self, pattern: str, table: int, base_form_plain: str) -> str:
        return self._index.get((pattern, table, base_form_plain), "")
