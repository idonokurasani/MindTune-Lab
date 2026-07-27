"""Curriculum adapter: load validated Hebrew items and filter readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem

# Italian infinitives for the approved canonical lemmas.  These are the only
# semantic glosses supplied directly by CLM-06; all other Italian strings are
# derived from these roots and the grammatical dimensions of each form.
_LEMMA_ITALIAN = {
    "לכתוב": "scrivere",
    "להיות": "essere",
    "לעשות": "fare",
}


class HebrewCurriculumAdapter:
    """Load validated Hebrew curriculum forms from the repository."""

    def __init__(self, approved_dir: Path | None = None) -> None:
        if approved_dir is None:
            approved_dir = Path(__file__).resolve().parents[5] / "data" / "hebrew" / "approved"
        self.approved_dir = approved_dir
        self._items: list[HebrewAdaptiveItem] = []
        self._loaded = False

    @property
    def items(self) -> list[HebrewAdaptiveItem]:
        if not self._loaded:
            self._load()
        return list(self._items)

    def approved_items(self) -> list[HebrewAdaptiveItem]:
        """Return all items with approved linguistic status."""
        return [i for i in self.items if i.linguistic_validation_status in ("approved", "validated")]

    def ready_items(self, asset_inventory: set[str]) -> list[HebrewAdaptiveItem]:
        """Return items whose required audio assets are present in the inventory."""
        return [i for i in self.approved_items() if all(a in asset_inventory for a in i.required_audio_asset_ids)]

    def readiness_report(self, asset_inventory: set[str]) -> dict[str, Any]:
        """Return a readiness summary with explicit blockers."""
        approved = self.approved_items()
        ready = self.ready_items(asset_inventory)
        blockers: list[str] = []
        missing = {a for i in approved for a in i.required_audio_asset_ids if a not in asset_inventory}
        if missing:
            blockers.append(f"missing_audio_assets: {sorted(missing)}")
        if not approved:
            blockers.append("no_approved_hebrew_items")
        return {
            "ready": len(ready) > 0 and not blockers,
            "approved_count": len(approved),
            "ready_count": len(ready),
            "missing_assets": sorted(missing),
            "blockers": blockers,
        }

    def _load(self) -> None:
        self._loaded = True
        if not self.approved_dir.exists():
            return
        for path in sorted(self.approved_dir.glob("*.json")):
            if path.name == "validation_summary.json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            paradigm = data.get("paradigm", {})
            lemma_data = paradigm.get("lemma", {})
            lemma_pointed = lemma_data.get("lemma_vocalized", "")
            lemma_unpointed = lemma_data.get("lemma_plain", "")
            root = lemma_data.get("root", "")
            binyan = lemma_data.get("binyan", "")
            for form_key, form in paradigm.get("forms", {}).items():
                item = _build_item(
                    form_key=form_key,
                    form=form,
                    lemma_pointed=lemma_pointed,
                    lemma_unpointed=lemma_unpointed,
                    root=root,
                    binyan=binyan,
                )
                if item is not None:
                    self._items.append(item)


def _build_item(
    form_key: str,
    form: dict[str, Any],
    lemma_pointed: str,
    lemma_unpointed: str,
    root: str,
    binyan: str,
) -> HebrewAdaptiveItem | None:
    approval_status = form.get("approval_status", "")
    if approval_status != "approved":
        return None
    unresolved = form.get("unresolved_conflicts", [])
    if unresolved:
        return None

    surface_pointed = form.get("surface_vocalized", "")
    surface_unpointed = form.get("surface_plain", "")
    tense = form.get("tense", "")
    mood = form.get("mood", "")
    person = form.get("person", "")
    gender = form.get("gender", "")
    number = form.get("number", "")
    transliteration = form.get("transliteration", "")
    source_evidence = form.get("source_evidence", [])
    source_id = source_evidence[0].get("source", "pealim") if source_evidence else "pealim"

    sources = [ev.get("source", "") for ev in source_evidence]
    morphology_provenance = f"pealim+{','.join(s for s in sources if s)}"
    pointing_provenance = morphology_provenance

    item_id = f"clm06-{lemma_unpointed}-{form_key}"
    required_asset_id = f"clm06.aaron.{lemma_unpointed}.{form_key}"
    natural = _natural_italian(lemma_unpointed, person, gender, number, tense)
    gloss = _LEMMA_ITALIAN.get(lemma_unpointed, lemma_unpointed)

    return HebrewAdaptiveItem(
        item_id=item_id,
        curriculum_version="clm06-hebrew-v1",
        source_id=source_id,
        lemma=lemma_pointed,
        lemma_pointed=lemma_pointed,
        lemma_unpointed=lemma_unpointed,
        root=root,
        binyan=binyan,
        tense=tense,
        mood=mood,
        person=person,
        gender=gender,
        number=number,
        subject=_subject(person, gender, number),
        register="formal" if form.get("usage_classification") in ("literary", "archaic") else "modern",
        canonical_pointed=surface_pointed,
        canonical_unpointed=surface_unpointed,
        transliteration=transliteration,
        pointed_context_sentence="",
        unpointed_context_sentence="",
        italian_gloss=gloss,
        natural_italian=natural,
        morphology_provenance=morphology_provenance,
        pointing_provenance=pointing_provenance,
        help_references=[],
        linguistic_validation_status=approval_status,
        pronunciation_review_status="approved" if form.get("phonemes_corrected") else "pending",
        required_audio_asset_ids=[required_asset_id],
        accepted_alternates=[surface_pointed, surface_unpointed],
        error_confusion_set=list(form.get("consensus", {}).get("source_forms", {}).values()) or [],
        usage_classification=form.get("usage_classification", "unknown"),
        paradigm_form_key=form_key,
    )


def _subject(person: str, gender: str, number: str) -> str:
    parts = [p for p in (person, gender, number) if p]
    return " ".join(parts) if parts else ""


def _natural_italian(lemma: str, person: str, gender: str, number: str, tense: str) -> str:
    base = _LEMMA_ITALIAN.get(lemma, lemma)
    # Minimal deterministic Italian pronoun / auxiliary hint; not a conjugation.
    if not person and not tense:
        return base
    pronoun = _italian_pronoun(person, gender, number)
    if tense == "past":
        return f"{pronoun} ho {base}"
    if tense == "future":
        return f"{pronoun} {base}rò"
    return f"{pronoun} {base}"


def _italian_pronoun(person: str, gender: str, number: str) -> str:
    if person == "first":
        return "noi" if number == "plural" else "io"
    if person == "second":
        return "voi" if number == "plural" else "tu"
    if person == "third":
        if number == "plural":
            return "loro"
        return "lui" if gender == "masculine" else "lei"
    return "io"
