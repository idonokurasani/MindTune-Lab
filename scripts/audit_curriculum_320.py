#!/usr/bin/env python3
"""Audit the v1.0.0 Hebrew curriculum and produce deterministic reports."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
    verb_id: str
    source_identifier: str
    source_infinitive: str
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
    # Very conservative: if the vocalized form contains holam/qubuts but the
    # plain form lacks vav/yod, flag for review.
    plain = strip_niqqud(text)
    if "\u05b9" in text or "\u05bb" in text:
        return "ו" not in plain and "י" not in plain
    return False


def _is_infinitive(text: str) -> bool:
    plain = strip_niqqud(text)
    # Infinitives in Hebrew begin with ל (lamed prefix).
    return plain.startswith("ל")


def _load_source_lookup() -> dict[str, dict[str, Any]]:
    loader = Phase3DataLoader()
    loader.load_all()
    candidates = select_100_verbs(loader, target_size=400)
    lookup: dict[str, dict[str, Any]] = {}
    for c in candidates:
        key = c["infinitive_plain"]
        if key:
            lookup[key] = c
    return lookup


def _audit(  # noqa: C901
    curriculum: dict[str, Any], source_lookup: dict[str, dict[str, Any]]
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
        source = source_lookup.get(inf_plain, {})

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
        if dup_inf:
            issues.append("duplicate_infinitive")
            action = "exclude_in_next_curriculum_version"
            confidence = "high"
            blocks = True
        if dup_prefix:
            issues.append("duplicate_asset_id_prefix")
            action = "exclude_in_next_curriculum_version"
            confidence = "high"
            blocks = True

        suspicious = False
        # Infinitive should be pointed and start with lamed.
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
        # Full spelling is only a note, not an issue.

        tokenization_problem = False
        if re.search(r"[a-zA-Z0-9]", inf_plain):
            issues.append("latin_or_digits_in_infinitive")
            tokenization_problem = True
            action = "manual_review_required"
            blocks = True

        # Lexical ambiguity: if multiple source groups share the same plain
        # infinitive, the lemma may be ambiguous.
        lexical_ambiguity = seen_infs[inf_plain] > 1

        lemma_specified = bool(verb.get("root") and verb.get("binyan"))
        if not lemma_specified:
            issues.append("lemma_not_fully_specified")
            action = "manual_review_required"
            blocks = True

        if not source:
            issues.append("not_found_in_source_lookup")
            action = "keep_with_note"
            confidence = "medium"

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
            source_identifier=source.get("group_key", ""),
            source_infinitive=inf_plain,
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
            pedagogical_suitability=pedagogical,
            is_infinitive=_is_infinitive(inf_pointed),
            lemma_sufficiently_specified=lemma_specified,
            issue_categories=issues,
            confidence=confidence,
            recommended_action=action,
            evidence=(
                f"source={source.get('group_key','')}; frequency={verb.get('frequency',0)}; "
                f"selection_reason={verb.get('selection_reason',[])}"
            ),
            blocks_asset_generation=blocks,
        )
        entries.append(entry)
    return entries


def _investigated(entries: list[CurriculumAuditEntry]) -> list[CurriculumAuditEntry]:
    targets = {"לעשות", "לחבר", "לבצוע", "לחבור", "לתת"}
    return [e for e in entries if e.verb_id in targets]


def _write_json(entries: list[CurriculumAuditEntry], curriculum: dict[str, Any]) -> None:
    AUDIT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_version": "1.0.0",
        "curriculum_version": curriculum["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
        },
        "investigated_verbs": [e.to_dict() for e in _investigated(entries)],
        "entries": [e.to_dict() for e in entries],
    }
    AUDIT_JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False), encoding="utf-8"
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
    }
    lines = [
        "# Curriculum v1.0.0 Audit Report",
        "",
        f"- Curriculum version: {curriculum['version']}",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Source: {curriculum.get('source', 'unknown')}",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Investigated verbs", ""])
    for e in _investigated(entries):
        lines.append(f"### {e.verb_id}")
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
        "lookup, detects duplicates, checks Unicode normalization (NFC), "
        "flags non-infinitive lemmas, and records pedagogical notes. "
        "Corpus frequency alone does not determine pedagogical priority."
    )
    AUDIT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    curriculum = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
    source_lookup = _load_source_lookup()
    entries = _audit(curriculum, source_lookup)
    _write_json(entries, curriculum)
    _write_md(entries, curriculum)
    print(f"Wrote {AUDIT_JSON_PATH} and {AUDIT_MD_PATH}")


if __name__ == "__main__":
    main()
