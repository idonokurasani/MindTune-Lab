#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CITIZEN_DIR = DATA / "citizen_cafe_all_courses"
STREETWISE_DIR = DATA / "hebrew_enrichment" / "streetwise_hebrew"
OUT = DATA / "citizen_cafe_consolidation"

CANONICAL = CITIZEN_DIR / "CITIZEN_CAFE_ALL_COURSES_CANONICAL_MODEL_DRAFT_v1.1.json"
SOURCE_MAP = CITIZEN_DIR / "CITIZEN_CAFE_ALL_COURSES_SOURCE_MAP_v1.1.json"
STREETWISE_MATCHES = STREETWISE_DIR / "STREETWISE_HEBREW_MATCHES_v0.1.jsonl"

ARTIFACT_VERSION = "0.1"

HEBREW_RE = re.compile(r"[\u0590-\u05ff]")
ITALIAN_HINT_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
ENGLISH_RESIDUE_RE = re.compile(
    r"\b("
    r"about|answer|busy|coming|doesn|enough|evening|finally|great|large|learning|maybe|morning|night|"
    r"phone|question|ready|remember|small|strange|studying|thinking|tired|tomorrow|working|wrong"
    r")\b",
    re.IGNORECASE,
)

BLOCKING_FLAGS = {
    "empty_front",
    "empty_back",
    "back_contains_hebrew",
    "mojibake_or_extraction_symbol",
    "suspicious_translation_payload",
    "back_too_short",
    "front_contains_latin",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def load_streetwise_index() -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not STREETWISE_MATCHES.exists():
        return index
    for line in STREETWISE_MATCHES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        item_id = clean(row.get("canonical_item_id"))
        if item_id:
            index[item_id].append(row)
    return index


def load_source_index() -> dict[str, dict[str, Any]]:
    payload = read_json(SOURCE_MAP)
    return {
        clean(row.get("canonical_item_id")): row
        for row in payload.get("items", [])
        if row.get("canonical_item_id")
    }


def score_item(item: dict[str, Any], source: dict[str, Any] | None, streetwise_hits: list[dict[str, Any]]) -> dict[str, Any]:
    flags = [clean(flag) for flag in item.get("quality_flags") or [] if clean(flag)]
    hebrew = clean(item.get("hebrew"))
    italian = clean(item.get("italian"))

    score = 100
    reasons: list[str] = []
    evidence: list[str] = ["citizen_cafe_source_lineage"]

    blocking = sorted(BLOCKING_FLAGS.intersection(flags))
    if blocking:
        score -= 80
        reasons.append("blocking_quality_flag")

    if flags and not blocking:
        score -= min(35, 8 * len(flags))
        reasons.append("non_blocking_quality_flags")

    if not HEBREW_RE.search(hebrew):
        score -= 80
        reasons.append("missing_hebrew_script")

    if not ITALIAN_HINT_RE.search(italian):
        score -= 35
        reasons.append("weak_italian_surface")

    if ENGLISH_RESIDUE_RE.search(italian):
        score -= 25
        reasons.append("possible_english_residue")

    if "/" in italian and len([part for part in italian.split("/") if clean(part)]) >= 4:
        score -= 8
        reasons.append("many_translation_alternatives")

    if source:
        evidence.append(clean(source.get("source")) or "source_map")
    else:
        score -= 15
        reasons.append("missing_source_map")

    if streetwise_hits:
        score += min(12, 4 * len(streetwise_hits))
        evidence.append("streetwise_context_match")

    score = max(0, min(100, score))
    if blocking or score < 55:
        tier = "quarantine"
    elif score < 85:
        tier = "usable_with_review"
    else:
        tier = "solid_base_candidate"

    if not reasons:
        reasons.append("clean_structural_candidate")

    return {
        "canonical_item_id": item.get("canonical_item_id"),
        "deck": item.get("deck"),
        "citizen_level": item.get("citizen_level"),
        "hebrew": hebrew,
        "italian": italian,
        "quality_flags": "|".join(flags),
        "streetwise_match_count": len(streetwise_hits),
        "consolidation_score": score,
        "consolidation_tier": tier,
        "evidence_sources": "|".join(sorted(set(evidence))),
        "review_reasons": "|".join(sorted(set(reasons))),
        "source_map_ref": item.get("source_map_ref", ""),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    canonical = read_json(CANONICAL)
    items = canonical.get("items", [])
    source_index = load_source_index()
    streetwise_index = load_streetwise_index()

    rows = [
        score_item(item, source_index.get(clean(item.get("canonical_item_id"))), streetwise_index.get(clean(item.get("canonical_item_id")), []))
        for item in items
    ]
    tier_counts = Counter(row["consolidation_tier"] for row in rows)
    deck_counts = Counter((row["deck"], row["consolidation_tier"]) for row in rows)

    fields = [
        "canonical_item_id",
        "deck",
        "citizen_level",
        "hebrew",
        "italian",
        "quality_flags",
        "streetwise_match_count",
        "consolidation_score",
        "consolidation_tier",
        "evidence_sources",
        "review_reasons",
        "source_map_ref",
    ]
    write_csv(OUT / f"CITIZEN_CAFE_CONSOLIDATION_SCORES_v{ARTIFACT_VERSION}.csv", rows, fields)
    write_json(
        OUT / f"CITIZEN_CAFE_CONSOLIDATION_SCORES_v{ARTIFACT_VERSION}.json",
        {
            "schema": f"mindtune.citizen_cafe.consolidation_scores.v{ARTIFACT_VERSION}",
            "generated_at": now,
            "canonical_model": str(CANONICAL),
            "streetwise_matches": str(STREETWISE_MATCHES),
            "items": rows,
        },
    )
    write_csv(
        OUT / f"CITIZEN_CAFE_CONSOLIDATION_REVIEW_QUEUE_v{ARTIFACT_VERSION}.csv",
        [row for row in rows if row["consolidation_tier"] != "solid_base_candidate"],
        fields,
    )

    report = [
        f"# Citizen Cafe Consolidation Report v{ARTIFACT_VERSION}",
        "",
        f"Generated: `{now}`",
        "",
        "## Purpose",
        "",
        "Citizen Cafe is treated as Andrea's personal re-entry corpus: useful because it represents prior study history, not because it is a linguistic or pedagogical authority.",
        "",
        "This consolidation layer decides which old-study fragments can act as a temporary recall base, which need review, and which must remain quarantined.",
        "",
        "Streetwise Hebrew is treated as contextual enrichment and evidence, not as a replacement canonical corpus.",
        "",
        "## Summary",
        "",
        f"- Total Citizen Cafe items: **{len(rows)}**",
        f"- Solid base candidates: **{tier_counts['solid_base_candidate']}**",
        f"- Usable with review: **{tier_counts['usable_with_review']}**",
        f"- Quarantine: **{tier_counts['quarantine']}**",
        f"- Items with Streetwise context match: **{sum(1 for row in rows if row['streetwise_match_count'])}**",
        "",
        "## By Deck",
        "",
        "| Deck | Solid | Review | Quarantine |",
        "|---|---:|---:|---:|",
    ]
    for deck in sorted({row["deck"] for row in rows}, key=lambda value: (next((r["citizen_level"] for r in rows if r["deck"] == value), 99), value)):
        report.append(
            f"| {deck} | {deck_counts[(deck, 'solid_base_candidate')]} | {deck_counts[(deck, 'usable_with_review')]} | {deck_counts[(deck, 'quarantine')]} |"
        )
    report.extend(
        [
            "",
            "## Gate Meaning",
            "",
            "- `solid_base_candidate`: structurally clean and source-traceable; usable as temporary study material, still not frozen.",
            "- `usable_with_review`: probably useful, but needs human linguistic review before curriculum freeze.",
            "- `quarantine`: blocked from exercises until corrected.",
            "",
            "## External Comparison Principle",
            "",
            "Citizen Cafe color levels are retained as one possible progression, but MindTune should not trust that ordering blindly. The long-term base should be checked against:",
            "",
            "- Streetwise Hebrew: real-life register, idioms, spoken usage, podcast/audio context.",
            "- Academy of the Hebrew Language: normative orthography, grammar, terminology, verb/noun tables, dictionary and rulings.",
            "- Ulpan-style progression: beginner to advanced ladder, oral production, grammar recycling, active classroom practice.",
            "- University Modern Hebrew curricula: systematic morphology, reading/listening/writing progression, assessment and level placement.",
            "- Pealim/morphological sources: verb forms, roots, binyanim, infinitives, tense/person checks.",
            "- HeLP/frequency evidence: lexical frequency, reaction-time/recognition evidence, morpho-lexical difficulty.",
            "",
            "## Methodological Decision",
            "",
            "Citizen Cafe may supply Andrea's personal re-entry skeleton only after consolidation. Streetwise may strengthen evidence and supply context. Neither source alone is the curriculum authority.",
            "",
            "## Next Required Work",
            "",
            "1. Review all `usable_with_review` and `quarantine` rows.",
            "2. Add more Streetwise sources through the enrichment importer.",
            "3. Add Pealim-backed morphology for verbs and roots.",
            "4. Add an ulpan comparison matrix before freezing levels.",
            "5. Only then project stable items into MLF LearningUnits.",
        ]
    )
    (OUT / f"CITIZEN_CAFE_CONSOLIDATION_REPORT_v{ARTIFACT_VERSION}.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    matrix = [
        f"# Citizen Cafe vs External Hebrew Learning Sources v{ARTIFACT_VERSION}",
        "",
        f"Generated: `{now}`",
        "",
        "| Source family | Role in MindTune | Strength | Weakness | Boundary |",
        "|---|---|---|---|---|",
        "| Citizen Cafe | Personal re-entry corpus from Andrea's prior study | Historically meaningful exposure path; practical color progression; large available set | Quizlet-derived, uneven translations, not normalized enough; not a general authority | Domain corpus only; never MLF Core |",
            "| Academy of the Hebrew Language | Normative authority | Grammar, orthography, terminology, verb/noun tables, rulings, Hebrew-Hebrew dictionary | Not a learner curriculum and mostly Hebrew-only | Authority/reference layer; never copied wholesale into cards |",
            "| Streetwise Hebrew | Contextual enrichment and spoken-register evidence | Real-life spoken examples, podcast/audio context, idioms | Not a structured curriculum; copyright boundary; needs selective metadata import | Enrichment/read-model layer only |",
        "| Ulpan-style courses | Methodological benchmark | Oral production, active recycling, communicative competence | Public syllabi often incomplete; not personalized | Curriculum design reference only |",
        "| University Modern Hebrew | Rigor benchmark | Placement levels, morphology, reading/listening/writing assessment | Can be slower and less usage-driven | Curriculum/review benchmark only |",
        "| Pealim | Morphological validator | Roots, binyanim, conjugation forms | Not a pedagogy by itself | Hebrew-domain validator/cache only |",
        "| HeLP | Future psycholinguistic profiler | Frequency and processing evidence | Not a course and not implementation-ready | Future read-model/profiler only |",
        "",
        "## Public Methodology Links To Keep As References",
        "",
            "- Streetwise Hebrew official site: https://www.streetwisehebrew.com/",
            "- TLV1 Streetwise podcast index: https://tlv1.fm/podcasts/streetwise-hebrew-show/",
            "- Academy online resources: https://eng.hebrew-academy.org.il/our-work/online-resources/",
            "- Academy terminology database: https://terms.hebrew-academy.org.il/",
            "- Ulpan-Or public program catalogue / levels: https://www.ulpanor.com/",
        "- Council of Europe CEFR resources: https://www.coe.int/en/web/common-european-framework-reference-languages",
        "",
        "These references are methodological comparators. They are not imported as corpora.",
    ]
    (OUT / f"CITIZEN_CAFE_ULPAN_COMPARISON_MATRIX_v{ARTIFACT_VERSION}.md").write_text("\n".join(matrix) + "\n", encoding="utf-8")

    print(f"items={len(rows)}")
    print(f"solid={tier_counts['solid_base_candidate']} review={tier_counts['usable_with_review']} quarantine={tier_counts['quarantine']}")
    print(f"streetwise_matched={sum(1 for row in rows if row['streetwise_match_count'])}")
    print(f"out={OUT}")


if __name__ == "__main__":
    main()
