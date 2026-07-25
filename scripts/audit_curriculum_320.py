#!/usr/bin/env python3
"""Audit the v1.0.0 Hebrew curriculum and produce deterministic reports."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hebrew.normalization import strip_niqqud
from hebrew.phase3.data_loader import Phase3DataLoader
from hebrew.phase3.selection import select_100_verbs

CURRICULUM_PATH = Path("data/hebrew/curriculum_v1_320.json")
AUDIT_JSON_PATH = Path("data/hebrew/curriculum_v1_320_audit.json")
AUDIT_MD_PATH = Path("docs/audits/curriculum_v1_320_audit.md")


@dataclass(frozen=True)
class CurriculumAuditEntry:
    """One audited curriculum verb with full source provenance."""

    verb_id: str
    infinitive_plain: str
    infinitive_pointed: str
    source_identifier: str
    source_records: list[dict[str, Any]]
    normalized_infinitive: str
    unicode_normalization: str
    binyan: str
    corpus_frequency: int
    asset_id_prefix: str
    transliteration_slug: str
    duplicate_verb_id: bool
    duplicate_infinitive: bool
    duplicate_asset_id_prefix: bool
    suspicious_spelling: bool
    possible_defective_variant: bool
    possible_full_spelling_variant: bool
    possible_tokenization_problem: bool
    possible_lexical_ambiguity: bool
    italian_infinitive_status: str
    pedagogical_suitability: str
    is_infinitive: bool
    lemma_sufficiently_specified: bool
    issue_categories: list[str]
    confidence: str
    recommended_action: str
    evidence: str
    blocks_asset_generation: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _has_vowel_letters(text: str) -> bool:
    return any(c in text for c in "וי")


def _looks_defective(text: str) -> bool:
    """Heuristic: a spelling without expected vav/yod maters may be defective."""
    plain = strip_niqqud(text)
    if "\u05b9" in text or "\u05bb" in text:
        return "ו" not in plain and "י" not in plain
    return False


def _is_infinitive(text: str) -> bool:
    plain = strip_niqqud(text)
    return plain.startswith("ל")


def _load_sources() -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Load source records keyed by group_key and by plain infinitive."""
    loader = Phase3DataLoader()
    loader.load_all()
    candidates = select_100_verbs(loader, target_size=400)

    by_group_key: dict[str, dict[str, Any]] = {}
    by_infinitive: dict[str, list[dict[str, Any]]] = {}
    for c in candidates:
        group_key = c["group_key"]
        by_group_key[group_key] = c
        inf = c["infinitive_plain"]
        if inf:
            by_infinitive.setdefault(inf, []).append(c)
    return by_group_key, by_infinitive


def _audit(  # noqa: C901
    curriculum: dict[str, Any],
    by_group_key: dict[str, dict[str, Any]],
    by_infinitive: dict[str, list[dict[str, Any]]],
) -> list[CurriculumAuditEntry]:
    verbs = curriculum["verbs"]
    seen_ids: Counter[str] = Counter(v["verb_id"] for v in verbs)
    seen_infs: Counter[str] = Counter(v["infinitive_plain"] for v in verbs)
    seen_prefixes: Counter[str] = Counter(v["asset_id_prefix"] for v in verbs)

    entries: list[CurriculumAuditEntry] = []
    for verb in verbs:
        verb_id = verb["verb_id"]
        inf_plain = verb["infinitive_plain"]
        inf_pointed = verb["infinitive_pointed"]
        source_group_key = verb.get("source_group_key", "")

        primary_source = by_group_key.get(source_group_key, {})
        source_records = list(by_infinitive.get(inf_plain, []))

        issues: list[str] = []
        action = "keep"
        confidence = "high"
        blocks = False

        dup_id = seen_ids[verb_id] > 1
        dup_inf = seen_infs[inf_plain] > 1
        dup_prefix = seen_prefixes[verb["asset_id_prefix"]] > 1
        if dup_id:
            issues.append("duplicate_verb_id")
            action = "exclude_in_next_curriculum_version"
            confidence = "high"
            blocks = True
        if dup_prefix:
            issues.append("duplicate_asset_id_prefix")
            action = "exclude_in_next_curriculum_version"
            confidence = "high"
            blocks = True

        # Multiple curriculum records may share the same plain infinitive
        # across binyanim or source tables. This is not a block if each has a
        # unique verb_id and asset_id_prefix.
        if dup_inf:
            issues.append("homographic_infinitive")

        suspicious = False
        if not _is_infinitive(inf_pointed):
            issues.append("not_an_infinitive")
            suspicious = True
            action = "exclude_in_next_curriculum_version"
            blocks = True

        if inf_pointed != _normalize(inf_pointed):
            issues.append("unicode_not_nfc")
            suspicious = True
            action = "correct_in_next_curriculum_version"
            blocks = True

        possible_defective = _looks_defective(inf_pointed)
        if possible_defective:
            issues.append("possible_defective_spelling")
            suspicious = True
            action = "keep_with_note"

        possible_full = _has_vowel_letters(inf_plain) and not possible_defective

        tokenization_problem = False
        if re.search(r"[a-zA-Z0-9]", inf_plain):
            issues.append("latin_or_digits_in_infinitive")
            tokenization_problem = True
            action = "manual_review_required"
            blocks = True

        lexical_ambiguity = seen_infs[inf_plain] > 1 or len(source_records) > 1

        lemma_specified = bool(verb.get("root") and verb.get("binyan"))
        if not lemma_specified:
            issues.append("lemma_not_fully_specified")
            action = "manual_review_required"
            blocks = True

        if not source_records:
            issues.append("not_found_in_source_lookup")
            action = "keep_with_note"
            confidence = "medium"

        italian = verb.get("italian_infinitive")
        if italian is None:
            italian_status = "absent_authoritative_source"
            issues.append("missing_italian_infinitive")
            if action == "keep":
                action = "keep_with_note"
        elif italian == "":
            italian_status = "empty_unexplained"
            issues.append("empty_italian_infinitive")
            if action == "keep":
                action = "keep_with_note"
        else:
            italian_status = "present"

        pedagogical = (
            "high-frequency core verb"
            if verb.get("frequency", 0) >= 1000
            else "lower-frequency; verify pedagogical priority"
        )

        if verb.get("frequency", 0) < 100:
            issues.append("very_low_corpus_frequency")
            action = "keep_with_note"
            confidence = "low"

        entry = CurriculumAuditEntry(
            verb_id=verb_id,
            infinitive_plain=inf_plain,
            infinitive_pointed=inf_pointed,
            source_identifier=primary_source.get("group_key", ""),
            source_records=source_records,
            normalized_infinitive=_normalize(inf_plain),
            unicode_normalization="NFC" if inf_pointed == _normalize(inf_pointed) else "other",
            binyan=verb.get("binyan", ""),
            corpus_frequency=int(verb.get("frequency", 0)),
            asset_id_prefix=verb["asset_id_prefix"],
            transliteration_slug=verb["asset_id_prefix"],
            duplicate_verb_id=dup_id,
            duplicate_infinitive=dup_inf,
            duplicate_asset_id_prefix=dup_prefix,
            suspicious_spelling=suspicious,
            possible_defective_variant=possible_defective,
            possible_full_spelling_variant=possible_full,
            possible_tokenization_problem=tokenization_problem,
            possible_lexical_ambiguity=lexical_ambiguity,
            italian_infinitive_status=italian_status,
            pedagogical_suitability=pedagogical,
            is_infinitive=_is_infinitive(inf_pointed),
            lemma_sufficiently_specified=lemma_specified,
            issue_categories=issues,
            confidence=confidence,
            recommended_action=action,
            evidence=(
                f"source={primary_source.get('group_key','')}; "
                f"source_record_count={len(source_records)}; "
                f"frequency={verb.get('frequency',0)}; "
                f"selection_reason={verb.get('selection_reason',[])}"
            ),
            blocks_asset_generation=blocks,
        )
        entries.append(entry)
    return entries


_INVESTIGATED = {"לעשות", "לחבר", "לבצוע", "לחבור", "לתת"}


def _investigated(entries: list[CurriculumAuditEntry]) -> list[CurriculumAuditEntry]:
    return [e for e in entries if e.infinitive_plain in _INVESTIGATED]


def _write_json(entries: list[CurriculumAuditEntry], curriculum: dict[str, Any]) -> None:
    AUDIT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_version": "1.0.0",
        "curriculum_version": curriculum["version"],
        "summary": {
            "total_verbs": len(entries),
            "duplicate_verb_ids": sum(1 for e in entries if e.duplicate_verb_id),
            "duplicate_infinitives": sum(1 for e in entries if e.duplicate_infinitive),
            "duplicate_asset_id_prefixes": sum(1 for e in entries if e.duplicate_asset_id_prefix),
            "suspicious_spellings": sum(1 for e in entries if e.suspicious_spelling),
            "possible_defective_variants": sum(1 for e in entries if e.possible_defective_variant),
            "tokenization_problems": sum(1 for e in entries if e.possible_tokenization_problem),
            "lexical_ambiguities": sum(1 for e in entries if e.possible_lexical_ambiguity),
            "blocking_issues": sum(1 for e in entries if e.blocks_asset_generation),
            "missing_italian_infinitives": sum(
                1 for e in entries if e.italian_infinitive_status != "present"
            ),
        },
        "investigated_verbs": [e.to_dict() for e in _investigated(entries)],
        "entries": [e.to_dict() for e in entries],
    }
    AUDIT_JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def _write_md(entries: list[CurriculumAuditEntry], curriculum: dict[str, Any]) -> None:
    AUDIT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "total_verbs": len(entries),
        "duplicate_verb_ids": sum(1 for e in entries if e.duplicate_verb_id),
        "duplicate_infinitives": sum(1 for e in entries if e.duplicate_infinitive),
        "duplicate_asset_id_prefixes": sum(1 for e in entries if e.duplicate_asset_id_prefix),
        "suspicious_spellings": sum(1 for e in entries if e.suspicious_spelling),
        "possible_defective_variants": sum(1 for e in entries if e.possible_defective_variant),
        "tokenization_problems": sum(1 for e in entries if e.possible_tokenization_problem),
        "lexical_ambiguities": sum(1 for e in entries if e.possible_lexical_ambiguity),
        "blocking_issues": sum(1 for e in entries if e.blocks_asset_generation),
        "missing_italian_infinitives": sum(
            1 for e in entries if e.italian_infinitive_status != "present"
        ),
    }
    lines = [
        "# Curriculum v1.0.0 Audit Report",
        "",
        f"- Curriculum version: {curriculum['version']}",
        "- Generated at: deterministic (no timestamp)",
        f"- Source: {curriculum.get('source', 'unknown')}",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Investigated verbs", ""])
    for e in _investigated(entries):
        lines.append(f"### {e.infinitive_plain} ({e.verb_id})")
        lines.append(f"- asset_id_prefix: {e.asset_id_prefix}")
        lines.append(f"- binyan: {e.binyan}")
        lines.append(f"- frequency: {e.corpus_frequency}")
        lines.append(f"- is_infinitive: {e.is_infinitive}")
        lines.append(f"- issues: {e.issue_categories or 'none'}")
        lines.append(f"- confidence: {e.confidence}")
        lines.append(f"- recommended action: {e.recommended_action}")
        lines.append(f"- blocks asset generation: {e.blocks_asset_generation}")
        lines.append(f"- evidence: {e.evidence}")
        lines.append("")
    lines.extend(["", "## Methodology", ""])
    lines.append(
        "The audit compares the curriculum JSON against the Eran Tomer source "
        "records keyed by source group, preserves all source records for "
        "homographic infinitives, detects duplicate verb_ids / asset prefixes, "
        "checks Unicode normalization (NFC), flags non-infinitive lemmas, "
        "and records pedagogical notes. Corpus frequency alone does not "
        "determine pedagogical priority."
    )
    AUDIT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    curriculum = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
    by_group_key, by_infinitive = _load_sources()
    entries = _audit(curriculum, by_group_key, by_infinitive)
    _write_json(entries, curriculum)
    _write_md(entries, curriculum)
    print(f"Wrote {AUDIT_JSON_PATH} and {AUDIT_MD_PATH}")


if __name__ == "__main__":
    main()
