"""CLM-06B — Hebrew curriculum expansion and adaptive progression.

This module is intentionally separate from the existing CLM-06 adaptive slice.
It reuses the validated CLM-06 curriculum adapter and scoring, but adds a
versioned curriculum model, skill graph, prerequisite graph, learner model,
progression engine, review scheduler and contrast sets.  It does not contain
its own morphology generator, Pealim integration, upstream-pointing
integration, or paid-TTS client.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.hebrew_slice.curriculum_adapter import HebrewCurriculumAdapter
from mindtune_clm.hebrew_slice.error_taxonomy import is_morphology_error, is_pointing_error
from mindtune_clm.hebrew_slice.models import (
    HebrewAdaptiveItem,
    HebrewItemLearningState,
    HebrewResponse,
    HebrewScore,
)

HEBREW_SKILL_CATALOGUE: dict[str, dict[str, Any]] = {
    "identify_lemma": {"label": "Identify lemma", "parents": []},
    "identify_root": {"label": "Identify root", "parents": ["identify_lemma"]},
    "identify_binyan": {"label": "Identify binyan", "parents": ["identify_root"]},
    "identify_tense": {"label": "Identify tense", "parents": ["identify_binyan"]},
    "identify_person": {"label": "Identify person", "parents": ["identify_tense"]},
    "identify_gender": {"label": "Identify gender", "parents": ["identify_tense"]},
    "identify_number": {"label": "Identify number", "parents": ["identify_tense"]},
    "recognize_pointed_form": {"label": "Recognize pointed form", "parents": ["identify_lemma"]},
    "produce_unpointed_form": {"label": "Produce unpointed form", "parents": ["recognize_pointed_form"]},
    "produce_pointed_form": {"label": "Produce pointed form", "parents": ["produce_unpointed_form"]},
    "understand_contextual_meaning": {"label": "Understand contextual meaning", "parents": ["identify_lemma"]},
    "distinguish_weak_root_patterns": {"label": "Distinguish weak-root patterns", "parents": ["identify_root"]},
    "distinguish_formal_common_modern": {"label": "Distinguish formal and common-modern forms", "parents": ["identify_tense"]},
    "distinguish_semantically_related_verbs": {"label": "Distinguish semantically related verbs", "parents": ["identify_lemma"]},
}


_CURRICULUM_VERSION = "clm06b-hebrew-v2.0.0"


def _stage_for_form_key(form_key: str) -> int:
    if form_key == "infinitive":
        return 0
    if form_key.startswith("present"):
        return 1
    if form_key.startswith("past"):
        return 2
    if form_key.startswith("future"):
        return 3
    if form_key.startswith("imperative"):
        return 4
    return 5


def _tense_for_form_key(form_key: str) -> str:
    if form_key == "infinitive":
        return "infinitive"
    if form_key.startswith("present"):
        return "present"
    if form_key.startswith("past"):
        return "past"
    if form_key.startswith("future"):
        return "future"
    if form_key.startswith("imperative"):
        return "imperative"
    return "unknown"


def _skills_for_item(item: HebrewAdaptiveItem) -> list[str]:
    targets: list[str] = []
    if item.tense:
        targets.append("identify_tense")
    if item.person:
        targets.append("identify_person")
    if item.gender:
        targets.append("identify_gender")
    if item.number:
        targets.append("identify_number")
    if item.root:
        targets.append("identify_root")
    if item.binyan:
        targets.append("identify_binyan")
    if item.lemma_unpointed:
        targets.append("identify_lemma")
    if item.tense in ("infinitive",):
        targets.append("recognize_pointed_form")
    else:
        targets.extend(["produce_unpointed_form", "understand_contextual_meaning"])
    if item.register in ("formal", "archaic", "literary"):
        targets.append("distinguish_formal_common_modern")
    return targets


@dataclass(frozen=True)
class HebrewSkill:
    skill_id: str
    label: str
    parent_skill_ids: tuple[str, ...] = ()
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "label": self.label,
            "parent_skill_ids": list(self.parent_skill_ids),
            "description": self.description,
        }


@dataclass(frozen=True)
class HebrewPrerequisite:
    source_item_id: str
    target_item_id: str
    kind: str  # 'blocking' or 'recommended'
    edge_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_item_id": self.source_item_id,
            "target_item_id": self.target_item_id,
            "kind": self.kind,
            "edge_version": self.edge_version,
        }


@dataclass(frozen=True)
class HebrewContrastSet:
    contrast_set_id: str
    member_item_ids: tuple[str, ...]
    dimensions: tuple[str, ...]
    expected_confusion_types: tuple[str, ...]
    eligibility: str
    progression_rule: str
    review_rule: str
    active: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "contrast_set_id": self.contrast_set_id,
            "member_item_ids": list(self.member_item_ids),
            "dimensions": list(self.dimensions),
            "expected_confusion_types": list(self.expected_confusion_types),
            "eligibility": self.eligibility,
            "progression_rule": self.progression_rule,
            "review_rule": self.review_rule,
            "active": self.active,
        }


@dataclass(frozen=True)
class HebrewCurriculumItem:
    """A versioned curriculum view over a CLM-06 validated adaptive item."""

    item: HebrewAdaptiveItem
    curriculum_version: str
    unit_id: str
    lesson_id: str
    item_version: str
    domain: str
    skill_target_ids: tuple[str, ...]
    prerequisite_item_ids: tuple[str, ...]
    prerequisite_skill_ids: tuple[str, ...]
    difficulty_estimate: float
    help_references: tuple[str, ...]
    morphology_validation_status: str
    pointing_validation_status: str
    pronunciation_review_status: str
    active_learning_eligible: bool
    reference_only: bool
    accepted_alternatives: tuple[str, ...]
    confusion_set_ids: tuple[str, ...]
    source_provenance: str
    deprecated: bool
    replacement_item_id: str | None
    change_reason: str

    @property
    def item_id(self) -> str:
        return self.item.item_id

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "curriculum_version": self.curriculum_version,
            "unit_id": self.unit_id,
            "lesson_id": self.lesson_id,
            "item_version": self.item_version,
            "domain": self.domain,
            "skill_target_ids": list(self.skill_target_ids),
            "prerequisite_item_ids": list(self.prerequisite_item_ids),
            "prerequisite_skill_ids": list(self.prerequisite_skill_ids),
            "difficulty_estimate": self.difficulty_estimate,
            "help_references": list(self.help_references),
            "morphology_validation_status": self.morphology_validation_status,
            "pointing_validation_status": self.pointing_validation_status,
            "pronunciation_review_status": self.pronunciation_review_status,
            "active_learning_eligible": self.active_learning_eligible,
            "reference_only": self.reference_only,
            "accepted_alternatives": list(self.accepted_alternatives),
            "confusion_set_ids": list(self.confusion_set_ids),
            "source_provenance": self.source_provenance,
            "deprecated": self.deprecated,
            "replacement_item_id": self.replacement_item_id,
            "change_reason": self.change_reason,
            "canonical_pointed": self.item.canonical_pointed,
            "canonical_unpointed": self.item.canonical_unpointed,
            "italian_gloss": self.item.italian_gloss,
            "natural_italian": self.item.natural_italian,
        }


@dataclass(frozen=True)
class HebrewCurriculumUnit:
    unit_id: str
    title: str
    lesson_ids: tuple[str, ...]
    skill_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "title": self.title,
            "lesson_ids": list(self.lesson_ids),
            "skill_ids": list(self.skill_ids),
        }


@dataclass(frozen=True)
class HebrewCurriculumLesson:
    lesson_id: str
    unit_id: str
    title: str
    item_ids: tuple[str, ...]
    skill_target_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "unit_id": self.unit_id,
            "title": self.title,
            "item_ids": list(self.item_ids),
            "skill_target_ids": list(self.skill_target_ids),
        }


@dataclass(frozen=True)
class HebrewCurriculum:
    curriculum_id: str
    version: str
    base_version: str
    units: tuple[HebrewCurriculumUnit, ...]
    lessons: tuple[HebrewCurriculumLesson, ...]
    items: tuple[HebrewCurriculumItem, ...]
    skills: tuple[HebrewSkill, ...]
    prereq_graph: tuple[HebrewPrerequisite, ...]
    contrast_sets: tuple[HebrewContrastSet, ...]
    source_provenance: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def item_by_id(self) -> dict[str, HebrewCurriculumItem]:
        return {i.item_id: i for i in self.items}

    @property
    def skill_by_id(self) -> dict[str, HebrewSkill]:
        return {s.skill_id: s for s in self.skills}

    @property
    def unit_by_id(self) -> dict[str, HebrewCurriculumUnit]:
        return {u.unit_id: u for u in self.units}

    @property
    def lesson_by_id(self) -> dict[str, HebrewCurriculumLesson]:
        return {lesson.lesson_id: lesson for lesson in self.lessons}

    def as_dict(self) -> dict[str, Any]:
        return {
            "curriculum_id": self.curriculum_id,
            "version": self.version,
            "base_version": self.base_version,
            "source_provenance": self.source_provenance,
            "metadata": dict(self.metadata),
            "units": [u.as_dict() for u in self.units],
            "lessons": [lesson.as_dict() for lesson in self.lessons],
            "skills": [s.as_dict() for s in self.skills],
            "items": [i.as_dict() for i in self.items],
            "prereq_graph": [e.as_dict() for e in self.prereq_graph],
            "contrast_sets": [c.as_dict() for c in self.contrast_sets],
        }


@dataclass(frozen=True)
class ReadinessBlocker:
    item_id: str | None
    blocker_type: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "blocker_type": self.blocker_type,
            "detail": self.detail,
        }


@dataclass
class CurriculumReadiness:
    ready: bool
    approved_count: int
    ready_count: int
    blocked_items: list[str]
    blockers: list[ReadinessBlocker]
    asset_report: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "approved_count": self.approved_count,
            "ready_count": self.ready_count,
            "blocked_items": list(self.blocked_items),
            "blockers": [b.as_dict() for b in self.blockers],
            "asset_report": list(self.asset_report),
        }


def _defensive_tuple(value: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    return tuple(value)


class HebrewCurriculumBuilder:
    """Build a versioned CLM-06B curriculum from the validated CLM-06 adapter."""

    def __init__(self, adapter: HebrewCurriculumAdapter | None = None) -> None:
        self.adapter = adapter or HebrewCurriculumAdapter()

    def build(self, curriculum_id: str = "clm06b-hebrew") -> HebrewCurriculum:  # noqa: C901
        approved = [i for i in self.adapter.items if i.linguistic_validation_status in ("approved", "validated")]
        by_id = {i.item_id: i for i in approved}

        skills = tuple(
            HebrewSkill(
                skill_id=sk,
                label=HEBREW_SKILL_CATALOGUE[sk]["label"],
                parent_skill_ids=_defensive_tuple(HEBREW_SKILL_CATALOGUE[sk].get("parents", [])),
            )
            for sk in HEBREW_SKILL_CATALOGUE
        )

        lemma_groups: dict[str, list[HebrewAdaptiveItem]] = {}
        for item in approved:
            lemma_groups.setdefault(item.lemma_unpointed, []).append(item)

        # For each lemma, pick one representative for each tense stage to act as
        # the primary prerequisite gate.
        representatives: dict[str, dict[int, str]] = {}
        for lemma, group in lemma_groups.items():
            for item in group:
                stage = _stage_for_form_key(item.paradigm_form_key)
                if stage not in representatives.setdefault(lemma, {}):
                    representatives[lemma][stage] = item.item_id

        curriculum_items: list[HebrewCurriculumItem] = []
        unit_map: dict[str, HebrewCurriculumUnit] = {}
        lesson_map: dict[str, HebrewCurriculumLesson] = {}
        edges: list[HebrewPrerequisite] = []

        for item in approved:
            stage = _stage_for_form_key(item.paradigm_form_key)
            tense = _tense_for_form_key(item.paradigm_form_key)
            unit_id = f"unit-{item.binyan or 'unknown'}"
            unit_title = f"Binyan {item.binyan}" if item.binyan else "Unclassified"
            lesson_id = f"lesson-{item.lemma_unpointed}-{tense}"
            lesson_title = f"{item.lemma_unpointed} — {tense}"

            skill_ids = _skills_for_item(item)
            prereqs: list[str] = []
            if stage > 0:
                prev_stage = stage - 1
                if prev_stage in representatives.get(item.lemma_unpointed, {}):
                    prereqs.append(representatives[item.lemma_unpointed][prev_stage])
                    edges.append(
                        HebrewPrerequisite(
                            source_item_id=representatives[item.lemma_unpointed][prev_stage],
                            target_item_id=item.item_id,
                            kind="blocking",
                            edge_version=_CURRICULUM_VERSION,
                        )
                    )
            # Recommended prerequisite: production depends on recognition of the
            # same form.
            if "produce" in skill_ids:
                rec_id = f"clm06-{item.lemma_unpointed}-{item.paradigm_form_key}"
                if rec_id in by_id and rec_id != item.item_id:
                    prereqs.append(rec_id)
                    edges.append(
                        HebrewPrerequisite(
                            source_item_id=rec_id,
                            target_item_id=item.item_id,
                            kind="recommended",
                            edge_version=_CURRICULUM_VERSION,
                        )
                    )

            active = self._item_active(item)
            ci = HebrewCurriculumItem(
                item=item,
                curriculum_version=_CURRICULUM_VERSION,
                unit_id=unit_id,
                lesson_id=lesson_id,
                item_version="1.0.0",
                domain="hebrew_verbal_morphology",
                skill_target_ids=tuple(skill_ids),
                prerequisite_item_ids=tuple(prereqs),
                prerequisite_skill_ids=(),
                difficulty_estimate=0.5,
                help_references=tuple(item.help_references or []),
                morphology_validation_status=item.linguistic_validation_status,
                pointing_validation_status="validated" if item.canonical_pointed else "pending",
                pronunciation_review_status=item.pronunciation_review_status or "pending",
                active_learning_eligible=active,
                reference_only=not active,
                accepted_alternatives=tuple(item.accepted_alternates or []),
                confusion_set_ids=(),
                source_provenance=item.morphology_provenance,
                deprecated=False,
                replacement_item_id=None,
                change_reason="",
            )
            curriculum_items.append(ci)

            if unit_id not in unit_map:
                unit_map[unit_id] = HebrewCurriculumUnit(
                    unit_id=unit_id,
                    title=unit_title,
                    lesson_ids=(),
                    skill_ids=tuple(sk.skill_id for sk in skills),
                )
            if lesson_id not in lesson_map:
                lesson_map[lesson_id] = HebrewCurriculumLesson(
                    lesson_id=lesson_id,
                    unit_id=unit_id,
                    title=lesson_title,
                    item_ids=(),
                    skill_target_ids=(),
                )
            # update later

        # Patch unit/lesson aggregates.
        for unit in unit_map.values():
            lesson_ids = sorted({ci.lesson_id for ci in curriculum_items if ci.unit_id == unit.unit_id})
            unit_map[unit.unit_id] = HebrewCurriculumUnit(
                unit_id=unit.unit_id,
                title=unit.title,
                lesson_ids=tuple(lesson_ids),
                skill_ids=unit.skill_ids,
            )
        for lesson in lesson_map.values():
            items_in = [ci.item_id for ci in curriculum_items if ci.lesson_id == lesson.lesson_id]
            skill_target_ids = sorted({sk for ci in curriculum_items if ci.lesson_id == lesson.lesson_id for sk in ci.skill_target_ids})
            lesson_map[lesson.lesson_id] = HebrewCurriculumLesson(
                lesson_id=lesson.lesson_id,
                unit_id=lesson.unit_id,
                title=lesson.title,
                item_ids=tuple(items_in),
                skill_target_ids=tuple(skill_target_ids),
            )

        contrast_sets = self._build_contrast_sets(approved)

        return HebrewCurriculum(
            curriculum_id=curriculum_id,
            version=_CURRICULUM_VERSION,
            base_version="clm06-hebrew-v1",
            units=tuple(unit_map.values()),
            lessons=tuple(lesson_map.values()),
            items=tuple(curriculum_items),
            skills=skills,
            prereq_graph=tuple(edges),
            contrast_sets=tuple(contrast_sets),
            source_provenance="clm06_curriculum_adapter",
            metadata={"created_at": time.time(), "schema": "clm06b"},
        )

    def _item_active(self, item: HebrewAdaptiveItem) -> bool:
        if item.linguistic_validation_status not in ("approved", "validated"):
            return False
        if not item.canonical_pointed or not item.canonical_unpointed:
            return False
        if not item.italian_gloss:
            return False
        if not item.morphology_provenance:
            return False
        if item.pronunciation_review_status == "rejected":
            return False
        return True

    def _build_contrast_sets(self, approved: list[HebrewAdaptiveItem]) -> list[HebrewContrastSet]:
        sets: list[HebrewContrastSet] = []
        # Haya family contrast set (static canonical IDs).
        haya_ids = sorted({i.item_id for i in approved if i.lemma_unpointed in ("להיות", "להוות", "להתהוות")})
        if len(haya_ids) >= 2:
            sets.append(
                HebrewContrastSet(
                    contrast_set_id="cs-haya-family",
                    member_item_ids=tuple(haya_ids[:6]),
                    dimensions=("lemma", "binyan"),
                    expected_confusion_types=("wrong_lemma", "haya_hava_hit_hava_confusion"),
                    eligibility="active_learning",
                    progression_rule="trigger_after_error",
                    review_rule="immediate_repeat_bounded",
                )
            )
        # Weak root alternations: group by root.
        root_groups: dict[str, list[HebrewAdaptiveItem]] = {}
        for item in approved:
            root_groups.setdefault(item.root or "unknown", []).append(item)
        for root, group in root_groups.items():
            if len(group) > 1:
                sets.append(
                    HebrewContrastSet(
                        contrast_set_id=f"cs-weak-root-{root}",
                        member_item_ids=tuple(i.item_id for i in group[:4]),
                        dimensions=("root", "binyan"),
                        expected_confusion_types=("wrong_root",),
                        eligibility="active_learning",
                        progression_rule="trigger_after_error",
                        review_rule="delayed_review",
                    )
                )
        # Gender contrast for present forms of the same lemma/tense.
        key_groups: dict[tuple[str, str], list[HebrewAdaptiveItem]] = {}
        for item in approved:
            tense = _tense_for_form_key(item.paradigm_form_key)
            key_groups.setdefault((item.lemma_unpointed, tense), []).append(item)
        for (lemma, tense), group in key_groups.items():
            by_gender: dict[str, list[HebrewAdaptiveItem]] = {}
            for i in group:
                by_gender.setdefault(i.gender or "unspecified", []).append(i)
            if len(by_gender) > 1:
                members = sorted({i.item_id for i in group})
                sets.append(
                    HebrewContrastSet(
                        contrast_set_id=f"cs-gender-{lemma}-{tense}",
                        member_item_ids=tuple(members[:6]),
                        dimensions=("gender",),
                        expected_confusion_types=("wrong_gender",),
                        eligibility="active_learning",
                        progression_rule="trigger_after_repeated_gender_error",
                        review_rule="contrast_drill",
                    )
                )
        return sets


class HebrewPrerequisiteGraph:
    """Deterministic validation and traversal of curriculum prerequisites."""

    def __init__(self, curriculum: HebrewCurriculum) -> None:
        self.curriculum = curriculum
        self._edges: dict[str, list[HebrewPrerequisite]] = {}
        for edge in curriculum.prereq_graph:
            self._edges.setdefault(edge.target_item_id, []).append(edge)

    def missing_references(self) -> list[str]:
        item_ids = {i.item_id for i in self.curriculum.items}
        missing: list[str] = []
        for edge in self.curriculum.prereq_graph:
            if edge.source_item_id not in item_ids:
                missing.append(edge.source_item_id)
            if edge.target_item_id not in item_ids:
                missing.append(edge.target_item_id)
        return sorted(set(missing))

    def has_cycle(self) -> bool:  # noqa: C901
        item_ids = {i.item_id for i in self.curriculum.items}
        graph: dict[str, set[str]] = {i: set() for i in item_ids}
        for edge in self.curriculum.prereq_graph:
            if edge.kind == "blocking":
                if edge.source_item_id in item_ids and edge.target_item_id in item_ids:
                    graph[edge.target_item_id].add(edge.source_item_id)
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def visit(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if visit(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in item_ids:
            if node not in visited:
                if visit(node):
                    return True
        return False

    def validate(self) -> tuple[bool, list[str]]:
        blockers: list[str] = []
        missing = self.missing_references()
        if missing:
            blockers.append(f"missing_prerequisite_references: {missing}")
        if self.has_cycle():
            blockers.append("prerequisite_cycle_detected")
        return (not blockers, blockers)

    def blocking_prerequisites(self, item_id: str) -> list[str]:
        return [
            e.source_item_id
            for e in self._edges.get(item_id, [])
            if e.kind == "blocking"
        ]

    def recommended_prerequisites(self, item_id: str) -> list[str]:
        return [
            e.source_item_id
            for e in self._edges.get(item_id, [])
            if e.kind == "recommended"
        ]

    def eligible_items(
        self,
        item_states: dict[str, HebrewItemLearningState],
        *,
        research_override: set[str] | None = None,
    ) -> list[str]:
        research_override = research_override or set()
        eligible: list[str] = []
        for item in self.curriculum.items:
            if item.deprecated or item.reference_only:
                continue
            if item.item_id in research_override:
                eligible.append(item.item_id)
                continue
            blocking = self.blocking_prerequisites(item.item_id)
            if all(
                s in item_states and item_states[s].current_mastery_estimate >= 0.5
                for s in blocking
            ):
                eligible.append(item.item_id)
        return eligible


class HebrewCurriculumReadinessEvaluator:
    """Surface explicit readiness blockers without mutating curriculum truth."""

    def __init__(self, curriculum: HebrewCurriculum, asset_inventory: set[str]) -> None:
        self.curriculum = curriculum
        self.asset_inventory = asset_inventory

    def evaluate_item(self, item: HebrewCurriculumItem) -> list[ReadinessBlocker]:  # noqa: C901
        blockers: list[ReadinessBlocker] = []
        if not item.morphology_validation_status or item.morphology_validation_status not in ("approved", "validated"):
            blockers.append(ReadinessBlocker(item.item_id, "morphology_unresolved", "morphology not validated"))
        if not item.item.canonical_pointed:
            blockers.append(ReadinessBlocker(item.item_id, "missing_pointed_form", "canonical pointed form missing"))
        if not item.item.canonical_unpointed:
            blockers.append(ReadinessBlocker(item.item_id, "missing_unpointed_form", "canonical unpointed form missing"))
        if not item.item.italian_gloss:
            blockers.append(ReadinessBlocker(item.item_id, "missing_translation", "Italian gloss missing"))
        for asset_id in item.item.required_audio_asset_ids:
            if asset_id not in self.asset_inventory:
                blockers.append(ReadinessBlocker(item.item_id, "missing_audio_asset", f"missing audio asset {asset_id}"))
        if item.pronunciation_review_status == "rejected":
            blockers.append(ReadinessBlocker(item.item_id, "rejected_pronunciation", "pronunciation review rejected"))
        if not item.source_provenance:
            blockers.append(ReadinessBlocker(item.item_id, "missing_provenance", "source provenance missing"))
        for prereq_id in item.prerequisite_item_ids:
            if prereq_id not in self.curriculum.item_by_id:
                blockers.append(ReadinessBlocker(item.item_id, "missing_prerequisite", f"missing prerequisite {prereq_id}"))
        if not item.active_learning_eligible:
            blockers.append(ReadinessBlocker(item.item_id, "not_active_eligible", "not active-learning eligible"))
        return blockers

    def asset_readiness_report(self) -> list[dict[str, Any]]:
        report: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in self.curriculum.items:
            for aid in item.item.required_audio_asset_ids:
                if aid in seen:
                    continue
                seen.add(aid)
                report.append(
                    {
                        "required_asset": aid,
                        "present": aid in self.asset_inventory,
                        "voice": "Aaron",
                        "locale": "he-IL",
                        "pointed_request_checksum": "",
                        "pronunciation_review_status": item.pronunciation_review_status,
                        "cache_compatibility": "compatible" if aid in self.asset_inventory else "missing",
                        "historical_incompatibility_reason": None,
                    }
                )
        return report

    def evaluate(self) -> CurriculumReadiness:
        graph = HebrewPrerequisiteGraph(self.curriculum)
        _, graph_blockers = graph.validate()
        approved = [i for i in self.curriculum.items if i.morphology_validation_status in ("approved", "validated")]
        ready_ids: list[str] = []
        all_blockers: list[ReadinessBlocker] = []
        for item in approved:
            blockers = self.evaluate_item(item)
            if not blockers:
                ready_ids.append(item.item_id)
            all_blockers.extend(blockers)
        return CurriculumReadiness(
            ready=not all_blockers and not graph_blockers,
            approved_count=len(approved),
            ready_count=len(ready_ids),
            blocked_items=[b.item_id for b in all_blockers if b.item_id is not None],
            blockers=all_blockers + [ReadinessBlocker(None, "graph", b) for b in graph_blockers],
            asset_report=self.asset_readiness_report(),
        )


@dataclass
class HebrewSkillLearningState:
    skill_id: str
    exposures: int = 0
    correct: int = 0
    incorrect: int = 0
    last_seen_semantic_time: float | None = None
    mastery: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "exposures": self.exposures,
            "correct": self.correct,
            "incorrect": self.incorrect,
            "last_seen_semantic_time": self.last_seen_semantic_time,
            "mastery": self.mastery,
        }


@dataclass
class HebrewLearnerModel:
    """Transparent, rule-based learner model pinned to a curriculum version."""

    learner_id: str
    session_id: str
    pinned_curriculum_version: str
    item_states: dict[str, HebrewItemLearningState] = field(default_factory=dict)
    skill_states: dict[str, HebrewSkillLearningState] = field(default_factory=dict)
    exposure_history: list[dict[str, Any]] = field(default_factory=list)
    response_accuracy: list[bool] = field(default_factory=list)
    response_times_ms: list[float] = field(default_factory=list)
    confidence_values: list[int] = field(default_factory=list)
    error_profile: dict[str, int] = field(default_factory=dict)
    pointing_accuracy: list[bool] = field(default_factory=list)
    morphology_accuracy: list[bool] = field(default_factory=list)
    review_history: list[dict[str, Any]] = field(default_factory=list)
    completed_item_ids: set[str] = field(default_factory=set)
    deferred_item_ids: set[str] = field(default_factory=set)
    blocked_item_ids: set[str] = field(default_factory=set)
    active_difficulty: float = 0.5
    semantic_time: float = 0.0
    deferred_until: dict[str, float] = field(default_factory=dict)
    assistance_history: list[float] = field(default_factory=list)
    contrast_drill_queue: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "learner_id": self.learner_id,
            "session_id": self.session_id,
            "pinned_curriculum_version": self.pinned_curriculum_version,
            "item_states": {k: v.as_dict() for k, v in self.item_states.items()},
            "skill_states": {k: v.as_dict() for k, v in self.skill_states.items()},
            "exposure_count": len(self.exposure_history),
            "completed_item_ids": sorted(self.completed_item_ids),
            "deferred_item_ids": sorted(self.deferred_item_ids),
            "blocked_item_ids": sorted(self.blocked_item_ids),
            "active_difficulty": self.active_difficulty,
            "semantic_time": self.semantic_time,
        }

    def update(
        self,
        curriculum: HebrewCurriculum,
        item: HebrewCurriculumItem,
        response: HebrewResponse,
        score: HebrewScore,
        semantic_time: float,
    ) -> None:
        from mindtune_clm.hebrew_slice.learning_state import update_learning_state

        old_state = self.item_states.get(item.item_id, HebrewItemLearningState(item_id=item.item_id))
        new_state = update_learning_state(old_state, response, score, semantic_time)
        self.item_states[item.item_id] = new_state
        self.semantic_time = semantic_time

        is_correct = score.overall == "correct"
        self.exposure_history.append(
            {
                "item_id": item.item_id,
                "semantic_time": semantic_time,
                "overall": score.overall,
                "error_codes": list(score.error_codes),
            }
        )
        self.response_accuracy.append(is_correct)
        self.response_times_ms.append(response.response_time_ms)
        self.confidence_values.append(response.confidence)
        self.assistance_history.append(response.audio_assistance_level)

        for code in score.error_codes:
            self.error_profile[code] = self.error_profile.get(code, 0) + 1
        self.pointing_accuracy.append(score.pointed_orthography == "correct")
        self.morphology_accuracy.append(all(getattr(score, d) == "correct" for d in ("lemma", "root", "binyan", "tense_mood", "person", "gender", "number")))

        for skill_id in item.skill_target_ids:
            ss = self.skill_states.get(skill_id, HebrewSkillLearningState(skill_id=skill_id))
            ss.exposures += 1
            ss.last_seen_semantic_time = semantic_time
            if is_correct:
                ss.correct += 1
            else:
                ss.incorrect += 1
            ss.mastery = round(ss.correct / max(1, ss.exposures), 3)
            self.skill_states[skill_id] = ss

        if new_state.current_mastery_estimate >= 0.8:
            self.completed_item_ids.add(item.item_id)

    def is_eligible(self, item: HebrewCurriculumItem, graph: HebrewPrerequisiteGraph) -> tuple[bool, list[str]]:
        if item.deprecated or item.reference_only or not item.active_learning_eligible:
            return False, ["item_not_active"]
        blockers: list[str] = []
        for pid in graph.blocking_prerequisites(item.item_id):
            ps = self.item_states.get(pid)
            if ps is None or ps.current_mastery_estimate < 0.5:
                blockers.append(f"blocking_prerequisite_not_mastered:{pid}")
        for sid in item.prerequisite_skill_ids:
            ss = self.skill_states.get(sid)
            if ss is None or ss.mastery < 0.5:
                blockers.append(f"blocking_skill_not_mastered:{sid}")
        if item.item_id in self.deferred_item_ids and self.semantic_time < self.deferred_until.get(item.item_id, 0.0):
            blockers.append("item_deferred")
        return (not blockers, blockers)

    def skill_mastery(self, skill_id: str) -> float:
        return self.skill_states.get(skill_id, HebrewSkillLearningState(skill_id=skill_id)).mastery


@dataclass(frozen=True)
class HebrewProgressionDecision:
    action: str
    next_item_id: str | None
    next_trial_type: str | None
    assistance_delta: float
    reason_codes: list[str]
    repeat_same_item: bool = False
    interleave_item_id: str | None = None
    review_scheduled: dict[str, Any] = field(default_factory=dict)
    contrast_set_id: str | None = None
    blocked: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "next_item_id": self.next_item_id,
            "next_trial_type": self.next_trial_type,
            "assistance_delta": self.assistance_delta,
            "reason_codes": list(self.reason_codes),
            "repeat_same_item": self.repeat_same_item,
            "interleave_item_id": self.interleave_item_id,
            "review_scheduled": dict(self.review_scheduled),
            "contrast_set_id": self.contrast_set_id,
            "blocked": self.blocked,
        }


class HebrewReviewScheduler:
    """Deterministic within-session and cross-session review scheduler."""

    def __init__(self) -> None:
        self._schedule: dict[str, dict[str, Any]] = {}
        self._session_boundary_id: int = 0

    def schedule(
        self,
        kind: str,
        item_id: str,
        semantic_time: float,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "item_id": item_id,
            "kind": kind,
            "scheduled_at": semantic_time,
            "due_at": semantic_time + self._delta(kind),
            "session_boundary_id": self._session_boundary_id,
            "context": dict(context or {}),
        }
        self._schedule[item_id] = entry
        return entry

    def _delta(self, kind: str) -> float:
        if kind == "immediate_repeat":
            return 0.0
        if kind == "short_delayed_review":
            return 3.0
        if kind == "next_session_priority":
            return 10.0
        return 5.0

    def advance_session(self) -> None:
        self._session_boundary_id += 1

    def due(self, semantic_time: float) -> list[dict[str, Any]]:
        return sorted(
            [e for e in self._schedule.values() if e["due_at"] <= semantic_time],
            key=lambda x: x["due_at"],
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_boundary_id": self._session_boundary_id,
            "schedule": {k: dict(v) for k, v in self._schedule.items()},
        }


class HebrewProgressionEngine:
    """Bounded deterministic progression for the CLM-06B curriculum."""

    def __init__(
        self,
        max_repeats: int = 3,
        min_mastery_for_advance: float = 0.8,
        min_mastery_for_recall: float = 0.6,
    ) -> None:
        self.max_repeats = max_repeats
        self.min_mastery_for_advance = min_mastery_for_advance
        self.min_mastery_for_recall = min_mastery_for_recall
        self.scheduler = HebrewReviewScheduler()

    def decide(  # noqa: C901
        self,
        curriculum: HebrewCurriculum,
        learner: HebrewLearnerModel,
        current_item: HebrewCurriculumItem,
        score: HebrewScore,
        response: HebrewResponse,
        control_state: dict[str, Any],
    ) -> HebrewProgressionDecision:
        graph = HebrewPrerequisiteGraph(curriculum)
        item_state = learner.item_states.get(current_item.item_id, HebrewItemLearningState(item_id=current_item.item_id))
        reasons: list[str] = []

        # CLM safety may affect presentation support only.
        if control_state.get("assistance_level", 0.0) >= 0.8:
            return HebrewProgressionDecision(
                action="baseline_lock_progression",
                next_item_id=current_item.item_id,
                next_trial_type="italian_to_hebrew",
                assistance_delta=-0.5,
                reason_codes=["clm_high_assistance_baseline_lock"],
                repeat_same_item=False,
            )

        # Pointing weakness => pointing-focused review.
        if any(is_pointing_error(c) for c in score.error_codes):
            self.scheduler.schedule("immediate_repeat", current_item.item_id, learner.semantic_time, {"focus": "pointing"})
            return HebrewProgressionDecision(
                action="schedule_pointing_review",
                next_item_id=current_item.item_id,
                next_trial_type="immediate_repetition",
                assistance_delta=0.1,
                reason_codes=["pointing_error", "pointing_review_scheduled"],
                repeat_same_item=True,
                review_scheduled={"reviews": self.scheduler.due(learner.semantic_time)},
            )

        # Gender confusion => contrast drill, bounded.
        if "wrong_gender" in score.error_codes or any("gender" in c for c in score.error_codes):
            contrast_id = self._gender_contrast_id(curriculum, current_item)
            if contrast_id:
                learner.contrast_drill_queue.append(contrast_id)
                return HebrewProgressionDecision(
                    action="introduce_contrast_item",
                    next_item_id=current_item.item_id,
                    next_trial_type="hebrew_recognition",
                    assistance_delta=0.0,
                    reason_codes=["gender_confusion", "contrast_drill"],
                    contrast_set_id=contrast_id,
                    repeat_same_item=False,
                )

        # Repeated failures.
        if item_state.consecutive_failures >= self.max_repeats:
            if item_state.consecutive_failures == self.max_repeats:
                reasons.append("repeat_limit_reached")
                interleave = self._pick_interleave(curriculum, learner, current_item, graph)
                return HebrewProgressionDecision(
                    action="interleave_previous_item",
                    next_item_id=interleave or current_item.item_id,
                    next_trial_type="hebrew_recognition",
                    assistance_delta=0.0,
                    reason_codes=reasons,
                    interleave_item_id=interleave,
                )
            return HebrewProgressionDecision(
                action="defer_item",
                next_item_id=None,
                next_trial_type=None,
                assistance_delta=0.0,
                reason_codes=["max_repeats_exceeded_defer"],
                blocked=True,
            )

        # Incorrect morphology => downgrade recall to recognition.
        if score.overall in ("incorrect", "invalid", "not_answered") or any(is_morphology_error(c) for c in score.error_codes):
            reasons.append("morphology_error_downgrade")
            return HebrewProgressionDecision(
                action="downgrade_recall_to_recognition",
                next_item_id=current_item.item_id,
                next_trial_type="hebrew_recognition",
                assistance_delta=0.15,
                reason_codes=reasons,
                repeat_same_item=True,
            )

        # Correct unpointed => continue with pointing support.
        if score.overall in ("correct_unpointed", "accepted_alternate"):
            self.scheduler.schedule("short_delayed_review", current_item.item_id, learner.semantic_time, {"focus": "pointing"})
            return HebrewProgressionDecision(
                action="repeat_with_support",
                next_item_id=current_item.item_id,
                next_trial_type="immediate_repetition",
                assistance_delta=0.05,
                reason_codes=["correct_unpointed_needs_pointing_support"],
                repeat_same_item=True,
            )

        # Correct and mastery high enough => advance to next eligible item.
        if score.overall == "correct":
            if item_state.current_mastery_estimate >= self.min_mastery_for_recall:
                reasons.append("recognition_to_recall_upgrade")
                next_item = self._next_eligible(curriculum, learner, current_item, graph)
                return HebrewProgressionDecision(
                    action="upgrade_recognition_to_recall" if next_item == current_item.item_id else "continue",
                    next_item_id=next_item,
                    next_trial_type="italian_to_hebrew" if next_item == current_item.item_id else "italian_to_hebrew",
                    assistance_delta=-0.1,
                    reason_codes=reasons,
                )
            next_item = self._next_eligible(curriculum, learner, current_item, graph)
            return HebrewProgressionDecision(
                action="continue",
                next_item_id=next_item,
                next_trial_type="italian_to_hebrew",
                assistance_delta=-0.1,
                reason_codes=["correct_continue"],
            )

        return HebrewProgressionDecision(
            action="repeat_item",
            next_item_id=current_item.item_id,
            next_trial_type="italian_to_hebrew",
            assistance_delta=0.0,
            reason_codes=["default_repeat"],
            repeat_same_item=True,
        )

    def _gender_contrast_id(self, curriculum: HebrewCurriculum, current_item: HebrewCurriculumItem) -> str | None:
        tense = _tense_for_form_key(current_item.item.paradigm_form_key)
        for cs in curriculum.contrast_sets:
            if current_item.item_id in cs.member_item_ids and "gender" in cs.dimensions:
                return cs.contrast_set_id
        return f"cs-gender-{current_item.item.lemma_unpointed}-{tense}"

    def _pick_interleave(
        self,
        curriculum: HebrewCurriculum,
        learner: HebrewLearnerModel,
        current_item: HebrewCurriculumItem,
        graph: HebrewPrerequisiteGraph,
    ) -> str | None:
        eligible = [i.item_id for i in curriculum.items if i.item_id != current_item.item_id and learner.is_eligible(i, graph)[0]]
        return eligible[0] if eligible else None

    def _next_eligible(
        self,
        curriculum: HebrewCurriculum,
        learner: HebrewLearnerModel,
        current_item: HebrewCurriculumItem,
        graph: HebrewPrerequisiteGraph,
    ) -> str:
        eligible = [i for i in curriculum.items if i.item_id != current_item.item_id and learner.is_eligible(i, graph)[0]]
        # Prefer items whose prerequisites have just been mastered; then lowest mastery.
        eligible.sort(key=lambda i: (
            not all(graph.blocking_prerequisites(i.item_id)),
            learner.item_states.get(i.item_id, HebrewItemLearningState(item_id=i.item_id)).current_mastery_estimate,
        ))
        return eligible[0].item_id if eligible else current_item.item_id


def build_clm06b_curriculum(adapter: HebrewCurriculumAdapter | None = None) -> HebrewCurriculum:
    return HebrewCurriculumBuilder(adapter).build()
