#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "citizen_cafe_all_courses"
ARTIFACT_VERSION = "1.1"

AUDIT = DATA / "quizlet_hebrew_audit.csv"
SEED = DATA / "quizlet_hebrew_seed.json"
ACTIVE_SEED = OUT / "quizlet_hebrew_seed.canonical.json"
PATCH_BACK_ONLY = ROOT.parent / "exports" / "zai_patch_review_20260714" / "zai_patch_candidate_apply_back_only.csv"

HEBREW_MARKS_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")
LATIN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
MOJIBAKE_OR_SYMBOL_RE = re.compile(r"[�₪]")
SUSPICIOUS_BACK_RE = re.compile(r"\d{3,}|['\")]\d|[A-Z]'?\d|[A-Z]'[A-Z]|[<>]")
ENGLISH_TOKEN_RE = re.compile(
    r"\b("
    r"about|absolutely|also|answer|big|both|busy|cake|coming|correct|doesn|enough|evening|excuse|finally|great|"
    r"hers|his|hungry|ice|if|large|learning|maybe|milk|money|morning|night|phone|problem|question|ready|"
    r"red|remember|small|strange|strawberries|studying|sugar|telling|thing|thinking|time|tired|tommorow|tomorrow|"
    r"very|white|wine|working|wrong|yet"
    r")\b",
    re.IGNORECASE,
)

COLOR_LEVELS = [
    ("red", "Red", 1, "#ff5f7e"),
    ("orange", "Orange", 2, "#ff9d45"),
    ("pink", "Pink", 3, "#f472c2"),
    ("yellow", "Yellow", 4, "#ffe66d"),
    ("light blue", "Light Blue", 5, "#7dddf7"),
    ("blue", "Blue", 6, "#6ea2ff"),
    ("lime", "Lime", 7, "#a6ff67"),
    ("green", "Green", 8, "#5fe39a"),
    ("dark green", "Dark Green", 9, "#27ce88"),
    ("turquoise", "Turquoise", 10, "#36e8c6"),
    ("indigo", "Indigo", 11, "#8b78ff"),
    ("purple", "Purple", 12, "#c07cff"),
]
COLOR_BY_LABEL = {label: (slug, level, swatch) for slug, label, level, swatch in COLOR_LEVELS}

LOCAL_BACK_CORRECTIONS = {
    "zip::citizen_cafe_orange_level::405": "rosso",
    "zip::citizen_cafe_orange_level::409": "bianco",
    "zip::citizen_cafe_yellow::278": "continuerai a lavorare",
    "zip::light_blue_7_23_dave_citizen_caf::832": "lui inizierà domani mattina",
    "zip::light_blue_7_23_dave_citizen_caf::841": "lui continuerà domani mattina",
    "zip::light_blue_7_23_dave_citizen_caf::870": "pensi che finiremo in tempo?",
    "zip::light_blue_7_23_dave_citizen_caf::875": "se tu inizi, anche lei inizierà",
    "zip::light_blue_7_23_dave_citizen_caf::877": "se lui pagherà, anche lei pagherà",
    "tab::jan_green_08_30_m_thu_ron::2925": "finito/a; esausto/a (colloquiale)",
    "zip::citizen_cafe_turquoise_spring_2026::758": "peggio per lui / ci perde lui",
    "pdf::purple::0159": "si impone / viene spontaneo / è richiesto",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def clean_space(value: Any) -> str:
    text = str(value or "").replace("\ufeff", "")
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_niqqud(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = HEBREW_MARKS_RE.sub("", text)
    text = "".join(ch for ch in text if not (unicodedata.combining(ch) and "\u0590" <= ch <= "\u05ff"))
    return unicodedata.normalize("NFC", text)


def normalize_hebrew(value: Any) -> str:
    return clean_space(strip_niqqud(value))


def normalize_translation(value: Any) -> str:
    text = clean_space(strip_niqqud(value))
    replacements = {
        "m.s.": "masch. sing.",
        "f.s.": "femm. sing.",
        "m.p.": "masch. plur.",
        "f.p.": "femm. plur.",
        "m.sg.": "masch. sing.",
        "f.sg.": "femm. sing.",
        "m.pl.": "masch. plur.",
        "f.pl.": "femm. plur.",
    }
    for before, after in replacements.items():
        text = re.sub(rf"\b{re.escape(before)}\b", after, text, flags=re.IGNORECASE)
    text = text.replace(" / ", " / ")
    return clean_space(text)


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "\u241f".join(str(part or "") for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def load_audit_rows() -> list[dict[str, str]]:
    with AUDIT.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_seed_items() -> list[dict[str, Any]]:
    payload = read_json(SEED)
    return payload.get("items", payload if isinstance(payload, list) else [])


def load_back_only_patches() -> dict[str, dict[str, str]]:
    if not PATCH_BACK_ONLY.exists():
        return {}
    with PATCH_BACK_ONLY.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    patches: dict[str, dict[str, str]] = {}
    for row in rows:
        item_id = clean_space(row.get("id"))
        if not item_id:
            continue
        if clean_space(row.get("match_status")) != "exact_match":
            continue
        if clean_space(row.get("apply_recommendation")) != "candidate_apply_back_only":
            continue
        patches[item_id] = row
    return patches


def apply_back_patch(item: dict[str, Any], patches: dict[str, dict[str, str]]) -> tuple[str, dict[str, str] | None]:
    item_id = clean_space(item.get("id"))
    current_front = normalize_hebrew(item.get("raw_front") or item.get("term"))
    current_back = normalize_translation(item.get("raw_back") or item.get("meaning"))
    patch = patches.get(item_id)
    if not patch:
        return current_back, None
    if normalize_hebrew(patch.get("front")) != current_front:
        return current_back, None
    if normalize_translation(patch.get("back_attuale")) != current_back:
        return current_back, None
    proposed = normalize_translation(patch.get("back_proposto"))
    return proposed or current_back, patch


def apply_local_back_correction(item: dict[str, Any], current_back: str) -> tuple[str, dict[str, str] | None]:
    item_id = clean_space(item.get("id"))
    proposed = LOCAL_BACK_CORRECTIONS.get(item_id)
    if not proposed:
        return current_back, None
    return normalize_translation(proposed), {
        "source": "mindtune_local_correction",
        "motivo": "Correzione deterministica di inglese residuo nel retro; fronte ebraico non modificato.",
        "confidenza": "media",
        "flag": "semantic_review",
    }


def quality_flags(seed_item: dict[str, Any], audit_match: dict[str, str] | None) -> list[str]:
    flags: list[str] = []
    for flag in seed_item.get("quality_flags") or []:
        if flag and flag not in flags:
            flags.append(str(flag))
    if audit_match:
        for flag in str(audit_match.get("flags") or "").split("|"):
            flag = flag.strip()
            if flag and flag not in flags:
                flags.append(flag)
    front = normalize_hebrew(seed_item.get("raw_front"))
    back = normalize_translation(seed_item.get("raw_back"))
    if not front:
        flags.append("empty_front")
    if not back:
        flags.append("empty_back")
    if LATIN_RE.search(front):
        flags.append("front_contains_latin")
    if HEBREW_RE.search(back):
        flags.append("back_contains_hebrew")
    if ENGLISH_TOKEN_RE.search(back):
        flags.append("translation_language_mixed")
    return sorted(set(flags))


def structural_quality_flags(front: str, back: str) -> list[str]:
    flags: list[str] = []
    joined = f"{front} {back}"
    if MOJIBAKE_OR_SYMBOL_RE.search(joined):
        flags.append("mojibake_or_extraction_symbol")
    if back and len(back.strip()) <= 1:
        flags.append("back_too_short")
    if SUSPICIOUS_BACK_RE.search(back):
        flags.append("suspicious_translation_payload")
    if front and LATIN_RE.search(front):
        flags.append("front_contains_latin")
    if back and HEBREW_RE.search(back):
        flags.append("back_contains_hebrew")
    return sorted(set(flags))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    audit_rows = load_audit_rows()
    seed_items = load_seed_items()
    back_patches = load_back_only_patches()

    audit_index: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in audit_rows:
        key = (
            clean_space(row.get("deck")),
            normalize_hebrew(row.get("front")),
            normalize_translation(row.get("back")),
        )
        audit_index[key].append(row)

    raw_records: list[dict[str, Any]] = []
    canonical_items: list[dict[str, Any]] = []
    curriculum_items: list[dict[str, Any]] = []
    source_map: list[dict[str, Any]] = []
    review_records: list[dict[str, Any]] = []
    lu_candidates: list[dict[str, Any]] = []

    seen_key: dict[tuple[str, str, str], str] = {}
    duplicate_count = 0
    quarantined = 0
    counts = Counter()
    source_counts = Counter()

    for position, item in enumerate(seed_items, start=1):
        deck = clean_space(item.get("deck") or item.get("citizen_color") or "Unclassified")
        slug, level, swatch = COLOR_BY_LABEL.get(deck, ("unclassified", 99, "#9ca3af"))
        front_original = clean_space(item.get("raw_front_original") or item.get("raw_front") or item.get("term"))
        back_original = clean_space(item.get("raw_back_original") or item.get("raw_back") or item.get("meaning"))
        front = normalize_hebrew(item.get("raw_front") or front_original)
        back_before_patch = normalize_translation(item.get("raw_back") or back_original)
        back, applied_patch = apply_back_patch(item, back_patches)
        local_patch = None
        if not applied_patch:
            back, local_patch = apply_local_back_correction(item, back)
        effective_patch = applied_patch or local_patch
        source = clean_space(item.get("source") or "unknown")
        source_file = clean_space(item.get("source_file") or "")
        source_row = clean_space(item.get("source_row") or "")
        source_deck = clean_space(item.get("source_deck") or deck)
        audit_matches = audit_index.get((deck, front, back), [])
        audit_match = audit_matches[0] if audit_matches else None
        flags = quality_flags(item, audit_match)
        if effective_patch and "translation_language_mixed" in flags and not ENGLISH_TOKEN_RE.search(back):
            flags = [flag for flag in flags if flag != "translation_language_mixed"]
        flags = sorted(set(flags + structural_quality_flags(front, back)))
        key = (deck, front, back)
        duplicate_of = seen_key.get(key)
        duplicate_candidate = duplicate_of is not None
        if duplicate_candidate:
            duplicate_count += 1
        else:
            seen_key[key] = clean_space(item.get("id")) or stable_id("cc", deck, front, back)
        blocking_flags = {
            "empty_back",
            "empty_front",
            "back_contains_hebrew",
            "mojibake_or_extraction_symbol",
            "suspicious_translation_payload",
            "back_too_short",
            "front_contains_latin",
        }
        quarantine_status = "quarantine" if (blocking_flags.intersection(flags) or duplicate_candidate) else "active_candidate"
        if quarantine_status == "quarantine":
            quarantined += 1
        item_id = clean_space(item.get("id")) or stable_id("cc", deck, source_file, source_row, front, back)
        canonical_item_id = stable_id("cclex", deck, front, back)
        lu_id = stable_id("lu", "hebrew_modern", canonical_item_id, "flashcard")
        source_ref = stable_id("src", deck, source, source_file, source_row, front_original, back_original)

        raw_records.append(
            {
                "record_id": stable_id("raw", item_id, position),
                "source_kind": "runtime_seed_with_audit_lineage",
                "source": source,
                "source_file": source_file,
                "source_deck": source_deck,
                "source_row": source_row,
                "deck": deck,
                "citizen_color": slug,
                "citizen_level": level,
                "local_sequence": position,
                "raw_hebrew_text": front_original,
                "raw_translation_text": back_original,
                "logical_order_hebrew_candidate": front,
                "normalized_translation_candidate": back,
                "normalized_translation_before_patch": back_before_patch,
                "applied_patch_id": stable_id("patch", item_id) if effective_patch else "",
                "rtl_reversal_flag": False,
                "front_back_pairing_confidence": "high" if audit_match or source != "pdf_extracted_raw" else "medium",
                "extraction_confidence": item.get("extraction_confidence") or ("verified" if item.get("study_ready", True) else "candidate"),
                "duplicate_candidate": duplicate_candidate,
                "duplicate_of": duplicate_of or "",
                "quarantine_status": quarantine_status,
                "notes": "; ".join(flags),
            }
        )

        canonical_items.append(
            {
                "canonical_item_id": canonical_item_id,
                "canonical_item_version": "1.0.0",
                "language": "hebrew_modern",
                "script": "Hebrew",
                "course_family": "Citizen Cafe",
                "deck": deck,
                "citizen_color": slug,
                "citizen_level": level,
                "hebrew": front,
                "italian": back,
                "italian_before_patch": back_before_patch,
                "source_map_ref": source_ref,
                "quality_flags": flags,
                "status": "needs_human_review" if flags else "candidate_ready",
            }
        )

        curriculum_items.append(
            {
                "curriculum_item_id": stable_id("cccur", "course_all", deck, canonical_item_id),
                "curriculum_version": "draft-1.0.0",
                "canonical_item_id": canonical_item_id,
                "domain_id": "hebrew_modern",
                "curriculum_id": "citizen_cafe_all_courses",
                "course_label": "Citizen Cafe all color levels",
                "level_label": deck,
                "level_order": level,
                "default_skill_targets": ["vocabulary_recognition", "vocabulary_recall"],
                "estimated_difficulty": level,
                "presentation_order": position,
                "review_status": "draft_unverified" if flags else "draft_candidate",
            }
        )

        source_map.append(
            {
                "source_map_ref": source_ref,
                "canonical_item_id": canonical_item_id,
                "source": source,
                "source_file": source_file,
                "source_row": source_row,
                "source_deck": source_deck,
                "seed_item_id": item_id,
                "raw_front_original": front_original,
                "raw_back_original": back_original,
                "raw_back_before_patch": back_before_patch,
                "applied_patch": {
                    "source": str(PATCH_BACK_ONLY) if applied_patch else "",
                    "motivo": applied_patch.get("motivo", "") if applied_patch else "",
                    "confidenza": applied_patch.get("confidenza", "") if applied_patch else "",
                    "flag": applied_patch.get("flag", "") if applied_patch else "",
                } if applied_patch else (local_patch or {}),
                "audit_status": audit_match.get("status") if audit_match else "",
                "audit_flags": audit_match.get("flags") if audit_match else "",
            }
        )

        if flags:
            review_records.append(
                {
                    "review_id": stable_id("review", canonical_item_id, "|".join(flags)),
                    "canonical_item_id": canonical_item_id,
                    "deck": deck,
                    "hebrew": front,
                    "italian": back,
                    "review_type": "linguistic_review",
                    "review_status": "open",
                    "flags": flags,
                    "responsible_owner": "human_hebrew_reviewer",
                    "source_map_ref": source_ref,
                }
            )

        lu_candidates.append(
            {
                "learning_unit_id": lu_id,
                "projection_version": "draft-1.0.0",
                "domain_id": "hebrew_modern",
                "domain_adapter_id": "hebrew_lab",
                "curriculum_id": "citizen_cafe_all_courses",
                "curriculum_version": "draft-1.0.0",
                "canonical_item_id": canonical_item_id,
                "canonical_item_version": "1.0.0",
                "title": f"{deck}: {front}",
                "metadata": {
                    "deck": deck,
                    "citizen_color": slug,
                    "citizen_level": level,
                    "front": front,
                    "back": back,
                    "source_map_ref": source_ref,
                    "quality_flags": flags,
                },
                "status": "draft_unverified" if flags else "draft_candidate",
            }
        )

        counts[deck] += 1
        source_counts[source] += 1

    active_seed_items: list[dict[str, Any]] = []
    for position, (seed_item, canonical) in enumerate(zip(seed_items, canonical_items), start=1):
        deck = canonical["deck"]
        active_seed_items.append(
            {
                **seed_item,
                "id": clean_space(seed_item.get("id")) or stable_id("seed", canonical["canonical_item_id"]),
                "deck": deck,
                "term": canonical["hebrew"],
                "meaning": canonical["italian"],
                "raw_front": canonical["hebrew"],
                "raw_back": canonical["italian"],
                "raw_back_before_patch": canonical.get("italian_before_patch", canonical["italian"]),
                "raw_front_original": clean_space(seed_item.get("raw_front_original") or canonical["hebrew"]),
                "raw_back_original": clean_space(seed_item.get("raw_back_original") or canonical["italian"]),
                "citizen_color": canonical["citizen_color"],
                "citizen_level": canonical["citizen_level"],
                "study_position": position,
                "canonical_item_id": canonical["canonical_item_id"],
                "canonical_item_version": canonical["canonical_item_version"],
                "source_map_ref": canonical["source_map_ref"],
                "quality_flags": canonical["quality_flags"],
                "study_ready": canonical["status"] == "candidate_ready",
                "semantic_method": "local_deterministic_normalization",
                "semantic_note": "Normalized locally from MindTune audit/seed; human linguistic approval still required for flagged items.",
            }
        )

    generated = {
        "schema": f"mindtune.quizlet_hebrew_seed.citizen_cafe_all_courses.v{ARTIFACT_VERSION}",
        "generated_at": now,
        "source_seed": str(SEED),
        "source_audit": str(AUDIT),
        "total_cards": len(active_seed_items),
        "study_ready_cards": sum(1 for item in active_seed_items if item.get("study_ready") is not False),
        "human_review_cards": sum(1 for item in active_seed_items if item.get("study_ready") is False),
        "decks": [label for _, label, _, _ in COLOR_LEVELS if counts[label]],
        "source_counts": dict(source_counts),
        "duplicate_cards_skipped": 0,
        "empty_back_cards_skipped": 0,
        "items": active_seed_items,
    }
    write_json(ACTIVE_SEED, generated)

    write_json(
        OUT / f"CITIZEN_CAFE_ALL_COURSES_RAW_EXTRACT_v{ARTIFACT_VERSION}.json",
        {
            "schema": f"citizen_cafe.raw_extract.all_courses.v{ARTIFACT_VERSION}",
            "generated_at": now,
            "source_note": "Source-faithful normalized extraction from MindTune audit and active seed. PDF availability is partial; raw PDF-only fragments remain in audit and are not promoted unless selected as seed candidates.",
            "records": raw_records,
        },
    )
    write_json(
        OUT / f"CITIZEN_CAFE_ALL_COURSES_SOURCE_MAP_v{ARTIFACT_VERSION}.json",
        {"schema": f"citizen_cafe.source_map.all_courses.v{ARTIFACT_VERSION}", "generated_at": now, "items": source_map},
    )
    write_json(
        OUT / f"CITIZEN_CAFE_ALL_COURSES_CANONICAL_MODEL_DRAFT_v{ARTIFACT_VERSION}.json",
        {"schema": f"citizen_cafe.canonical_linguistic_model.all_courses.v{ARTIFACT_VERSION}", "generated_at": now, "items": canonical_items},
    )
    write_json(
        OUT / f"CITIZEN_CAFE_ALL_COURSES_CURRICULUM_MODEL_DRAFT_v{ARTIFACT_VERSION}.json",
        {"schema": f"citizen_cafe.curriculum_model.all_courses.v{ARTIFACT_VERSION}", "generated_at": now, "items": curriculum_items},
    )
    write_json(
        OUT / f"CITIZEN_CAFE_ALL_COURSES_REVIEW_MODEL_DRAFT_v{ARTIFACT_VERSION}.json",
        {"schema": f"citizen_cafe.review_model.all_courses.v{ARTIFACT_VERSION}", "generated_at": now, "items": review_records},
    )
    write_json(
        OUT / f"CITIZEN_CAFE_ALL_COURSES_LU_PROJECTION_CANDIDATES_v{ARTIFACT_VERSION}.json",
        {"schema": f"citizen_cafe.learning_unit_projection_candidates.all_courses.v{ARTIFACT_VERSION}", "generated_at": now, "items": lu_candidates},
    )

    ledger_path = OUT / f"CITIZEN_CAFE_ALL_COURSES_CORRECTION_LEDGER_v{ARTIFACT_VERSION}.jsonl"
    with ledger_path.open("w", encoding="utf-8") as f:
        for record in review_records:
            f.write(json.dumps({
                "decision_id": stable_id("decision", record["review_id"]),
                "canonical_item_id": record["canonical_item_id"],
                "json_pointer": "/quality_flags",
                "previous_value": record["flags"],
                "proposed_value": None,
                "rationale": "Open human review item generated by deterministic local normalization.",
                "evidence_ref": record["source_map_ref"],
                "review_status": "open",
                "reviewer_role": record["responsible_owner"],
                "created_at": now,
                "supersedes_decision_id": "",
            }, ensure_ascii=False) + "\n")

    inventory_lines = [
        f"# Citizen Cafe All Courses - Raw Inventory v{ARTIFACT_VERSION}",
        "",
        f"Generated: `{now}`",
        "",
        "## Inputs",
        "",
        f"- Active runtime seed: `{SEED}`",
        f"- Audit table: `{AUDIT}`",
        "- Direct PDF sources available in this workspace are partial; all promoted cards are traceable through seed/audit source metadata.",
        "",
        "## Counts By Color",
        "",
        "| Color | Level | Cards |",
        "|---|---:|---:|",
    ]
    for _, label, level, _ in COLOR_LEVELS:
        inventory_lines.append(f"| {label} | {level} | {counts[label]} |")
    inventory_lines.extend([
        "",
        f"Total cards promoted: **{len(active_seed_items)}**",
        f"Study-ready cards: **{sum(1 for item in active_seed_items if item.get('study_ready') is not False)}**",
        f"Cards blocked pending human review: **{sum(1 for item in active_seed_items if item.get('study_ready') is False)}**",
        f"Quarantined candidates: **{quarantined}**",
        f"Duplicate candidates detected in promoted seed: **{duplicate_count}**",
        "",
        "## Source Counts",
        "",
        "| Source | Cards |",
        "|---|---:|",
    ])
    for source, count in source_counts.most_common():
        inventory_lines.append(f"| `{source}` | {count} |")
    write_text(OUT / f"CITIZEN_CAFE_ALL_COURSES_RAW_INVENTORY_v{ARTIFACT_VERSION}.md", "\n".join(inventory_lines))

    audit_lines = [
        f"# Citizen Cafe All Courses - Source Audit v{ARTIFACT_VERSION}",
        "",
        f"Generated: `{now}`",
        "",
        "This audit promotes only the current MindTune runtime seed candidates, then preserves source lineage into source_map_ref.",
        "",
        "## Gate Rule",
        "",
        "- Empty Hebrew or empty translation: quarantine.",
        "- Hebrew detected in Italian back side: quarantine.",
        "- Mojibake/extraction symbols and suspicious translation payloads: quarantine.",
        "- Duplicate exact `(deck, Hebrew, Italian)` in promoted seed: quarantine duplicate.",
        "- Any existing audit/source flag remains visible in canonical quality_flags.",
        "",
        "## Not A Linguistic Approval",
        "",
        "These artifacts are normalized and structured, not frozen. Human linguistic review remains required before declaring the corpus approved.",
    ]
    write_text(OUT / f"CITIZEN_CAFE_ALL_COURSES_SOURCE_AUDIT_v{ARTIFACT_VERSION}.md", "\n".join(audit_lines))

    review_lines = [
        f"# Citizen Cafe All Courses - Human Review Queue v{ARTIFACT_VERSION}",
        "",
        f"Generated: `{now}`",
        "",
        f"Open review records: **{len(review_records)}**",
        "",
        "| Deck | Hebrew | Italian | Flags |",
        "|---|---|---|---|",
    ]
    for record in review_records[:400]:
        review_lines.append(
            f"| {record['deck']} | {record['hebrew']} | {record['italian']} | {', '.join(record['flags'])} |"
        )
    if len(review_records) > 400:
        review_lines.append(f"| ... | ... | ... | {len(review_records) - 400} more records in JSON review model |")
    write_text(OUT / f"CITIZEN_CAFE_ALL_COURSES_HUMAN_REVIEW_QUEUE_v{ARTIFACT_VERSION}.md", "\n".join(review_lines))

    completeness_lines = [
        f"# Citizen Cafe All Courses - Completeness Report v{ARTIFACT_VERSION}",
        "",
        f"Generated: `{now}`",
        "",
        f"Active seed cards: **{len(seed_items)}**",
        f"Canonical items generated: **{len(canonical_items)}**",
        f"Runtime seed generated: **{len(active_seed_items)}**",
        f"Study-ready runtime cards: **{sum(1 for item in active_seed_items if item.get('study_ready') is not False)}**",
        f"Runtime cards blocked pending human review: **{sum(1 for item in active_seed_items if item.get('study_ready') is False)}**",
        f"Source map rows: **{len(source_map)}**",
        f"Open human review rows: **{len(review_records)}**",
        "",
        "## Status",
        "",
        "The corpus is structurally complete relative to the current MindTune runtime seed. It is not a linguistic approval. Cards with suspicious extraction/translation payloads remain in provenance and review models but are blocked from study until corrected.",
        "",
        "## Final Classification",
        "",
        "READY FOR HUMAN LINGUISTIC REVIEW — NOT APPROVED FOR CURRICULUM FREEZE",
    ]
    write_text(OUT / f"CITIZEN_CAFE_ALL_COURSES_COMPLETENESS_REPORT_v{ARTIFACT_VERSION}.md", "\n".join(completeness_lines))

    print(f"generated_cards={len(active_seed_items)}")
    print(f"review_records={len(review_records)}")
    print(f"out={OUT}")
    for _, label, _, _ in COLOR_LEVELS:
        print(f"{label}: {counts[label]}")


if __name__ == "__main__":
    main()
