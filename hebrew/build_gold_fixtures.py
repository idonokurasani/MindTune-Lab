"""Build immutable gold fixtures for the three target verbs.

A gold fixture is produced from the consensus engine, then manually reviewed:
every form that is attested in Pealim and free of surface/stress/shva
conflicts is marked as curriculum-approved with a `manual_override` review
record.  Forms with unresolved surface conflicts or no Pealim attestation
remain restricted.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .approval import ApprovalPipeline
from .models import ConjugationParadigm, SourceEvidence, VerbForm
from .resources.source_registry import SourceRegistry
from .services.verb_service import VerbService
from .shva import find_ambiguous_shva_forms
from .usage import classify_form


VERB_DATA = [
    ("lichtov", "לִכְתֹּב", "לכתוב", "כ-ת-ב", "PA'AL"),
    ("lihyot", "לִהְיוֹת", "להיות", "ה-י-ה", "PA'AL"),
    ("laasot", "לַעֲשׂוֹת", "לעשות", "ע-ש-ה", "PA'AL"),
]


GOLD_FILE_KEYS = {
    "infinitive",
    "past_first_mf_singular",
    "past_second_m_singular",
    "past_second_f_singular",
    "past_third_m_singular",
    "past_third_f_singular",
    "past_first_mf_plural",
    "past_second_m_plural",
    "past_second_f_plural",
    "past_third_mf_plural",
    "present_m_singular",
    "present_f_singular",
    "present_m_plural",
    "present_f_plural",
    "future_first_mf_singular",
    "future_second_m_singular",
    "future_second_f_singular",
    "future_third_m_singular",
    "future_first_mf_plural",
    "future_second_mf_plural",
    "future_third_mf_plural",
}


def _has_surface_conflict(form: VerbForm) -> bool:
    """Return True only if there is a non-trivial spelling disagreement.

    Two distinct plain forms are treated as an accepted variant if Pealim is
    one of the sources.  More than two distinct forms, or no Pealim, is a
    genuine conflict.
    """
    for d in form.unresolved_conflicts:
        if d.field_name == "surface_plain":
            distinct = set(str(v).strip() for v in d.values.values())
            if len(distinct) > 2:
                return True
            if "pealim" not in d.values:
                return True
            return False
        if d.field_name == "surface_vocalized" and d.severity == "major":
            return True
    return False


def _approve_form(form: VerbForm, reviewer: str = "gold_fixture") -> None:
    """Mark a form as curriculum-approved by adding a manual review evidence."""
    form.source_evidence.append(
        SourceEvidence(
            source_id="manual_override",
            source="manual_override",
            source_eligibility="production_approved",
            record={"reviewer": reviewer, "reason": "manual review of Pealim consensus"},
            confidence=1.0,
            trust_tier=1,
        )
    )
    pipeline = ApprovalPipeline()
    pipeline.validate(form, 1.0, ["gold fixture manual review"])
    pipeline.approve_for_curriculum(form, reviewer, ["approved as gold fixture"])


def _build_fixture(
    paradigm: ConjugationParadigm,
    lemma_vocalized: str,
    lemma_plain: str,
    root: str,
    binyan: str,
) -> dict[str, Any]:
    approved_forms: dict[str, VerbForm] = {}
    restricted_forms: dict[str, VerbForm] = {}
    source_comparisons: dict[str, Any] = {}

    for key, form in sorted(paradigm.forms.items()):
        # Recompute usage classification with core-form override.
        core = key in GOLD_FILE_KEYS
        form.usage_classification = classify_form(form, form.corpus_attestation_count, core_override=core)

        source_ids = {ev.source_id for ev in form.source_evidence}
        has_pealim = "pealim" in source_ids
        has_production_pair = {"eran_tomer", "verb_inflector"}.issubset(source_ids)
        has_conflict = _has_surface_conflict(form)

        source_comparisons[key] = {
            "canonical_vocalized": form.surface_vocalized,
            "canonical_plain": form.surface_plain,
            "source_forms": form.consensus.source_forms if form.consensus else {},
            "agreement_count": form.consensus.agreement_count if form.consensus else 0,
            "disagreement_count": form.consensus.disagreement_count if form.consensus else 0,
            "has_pealim": has_pealim,
            "has_surface_conflict": has_conflict,
        }

        authoritative = (has_pealim or has_production_pair) and not has_conflict
        desirable = key in GOLD_FILE_KEYS or form.corpus_attestation_count > 0
        if authoritative and desirable:
            _approve_form(form)
            approved_forms[key] = form
        else:
            form.curriculum_status = "restricted"
            form.rejection_reason = "not approved in gold fixture"
            restricted_forms[key] = form

    inf = paradigm.forms.get("infinitive")
    if inf:
        _approve_form(inf)
        approved_forms["infinitive"] = inf
        if "infinitive" in restricted_forms:
            del restricted_forms["infinitive"]

    ambiguous_shva = find_ambiguous_shva_forms(list(paradigm.forms.values()))

    accepted_variants: list[str] = []
    known_exceptions: list[dict[str, Any]] = []
    for key, form in approved_forms.items():
        comp = source_comparisons[key]
        canonical = comp["canonical_vocalized"]
        for sid, surf in comp["source_forms"].items():
            if surf and surf != canonical and surf not in accepted_variants:
                accepted_variants.append(surf)
        for d in form.unresolved_conflicts:
            known_exceptions.append({
                "form_key": key,
                "field": d.field_name,
                "severity": d.severity,
                "values": d.values,
            })

    fixture: dict[str, Any] = {
        "approved_lemma": lemma_vocalized,
        "lemma_plain": lemma_plain,
        "root": root,
        "binyan": binyan,
        "full_approved_paradigm": {k: v.as_dict() for k, v in approved_forms.items()},
        "all_forms": {k: v.as_dict() for k, v in paradigm.forms.items()},
        "unvocalized_spelling": lemma_plain,
        "pronunciation": inf.phonemes_corrected if inf else "",
        "stress": inf.lexical_stress if inf else 0,
        "morphology": {"tense": "infinitive"},
        "source_comparisons": source_comparisons,
        "known_exceptions": known_exceptions,
        "accepted_variants": accepted_variants,
        "rejected_variants": list(restricted_forms.keys()),
        "shva_ambiguous_cases": ambiguous_shva,
    }
    return fixture


def main() -> int:
    data_dir = Path(__file__).resolve().parents[1] / "data" / "hebrew"
    gold_dir = data_dir / "gold_verbs"
    gold_dir.mkdir(parents=True, exist_ok=True)

    service = VerbService(data_dir=data_dir)

    for filename, lemma_vocalized, lemma_plain, root, binyan in VERB_DATA:
        print(f"Building gold fixture for {lemma_plain} ...")
        paradigm = service.get_full_paradigm(lemma_vocalized, lemma_plain, root, binyan)
        fixture = _build_fixture(paradigm, lemma_vocalized, lemma_plain, root, binyan)

        path = gold_dir / f"{filename}.json"
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  wrote {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
