"""Local Pealim reference layer for manually approved verb forms."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import SourceEvidence, VerbForm
import re

from ..normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
from ..morphology import MorphologicalFeatures


@dataclass
class PealimReference:
    forms_json: Path
    audit_json: Path


def _form_key_to_features(form_key: str) -> MorphologicalFeatures:
    """Convert Pealim form keys to morphological features."""
    features = MorphologicalFeatures()
    # infinitive
    if form_key == "infinitive":
        features.tense = "infinitive"
        return features

    # present
    if form_key.startswith("present_"):
        features.tense = "present"
        parts = form_key.replace("present_", "").split("_")
        if "masculine" in parts:
            features.gender = "masculine"
        elif "feminine" in parts:
            features.gender = "feminine"
        if "singular" in parts:
            features.number = "singular"
        elif "plural" in parts:
            features.number = "plural"
        return features

    # past/future
    if form_key.startswith(("past_", "future_")):
        tense, rest = form_key.split("_", 1)
        features.tense = {"past": "past", "future": "future"}[tense]
        parts = rest.split("_")

        person_map = {"1": "first", "2": "second", "3": "third"}
        for p in parts:
            if p in person_map:
                features.person = person_map[p]
            elif p in ("masculine", "m"):
                features.gender = "masculine"
            elif p in ("feminine", "f"):
                features.gender = "feminine"
            elif p == "singular":
                features.number = "singular"
            elif p == "plural":
                features.number = "plural"

        # First person has no gender distinction in Hebrew; mark as mf.
        if features.person == "first":
            features.gender = features.gender or "masculine+feminine"

        # Past 3rd plural is shared m/f; future 3rd plural sometimes is a single
        # Pealim entry, so default to mf when no gender is explicit.
        if features.number == "plural" and not features.gender:
            features.gender = "masculine+feminine"

        return features

    return features


def load_approved_verbs(forms_path: Path, audit_path: Path) -> list[dict[str, Any]]:
    """Load and enrich Pealim forms with audit overrides."""
    forms = json.loads(forms_path.read_text(encoding="utf-8"))
    audit_rows = json.loads(audit_path.read_text(encoding="utf-8"))
    audit_map = {(r["verb"], r["form_key"]): r for r in audit_rows}

    enriched: list[dict[str, Any]] = []
    for verb in forms:
        query = verb["query"]
        root = verb.get("root", "")
        binyan = verb.get("binyan", "")
        for form_key, form_data in verb.get("forms", {}).items():
            surface = normalize_hebrew(form_data["hebrew_with_niqqud"])
            audit = audit_map.get((query, form_key), {})
            raw_phonemes = audit.get("phonikud_phonemes", "")
            corrected_phonemes = audit.get("manual_override") or raw_phonemes
            stress = int(audit.get("override_stress") or audit.get("expected_stress") or 0)
            vocal_shva = bool(audit.get("vocal_shva_override", False))
            transliteration_html = form_data.get("transcription_html", "")
            transliteration = re.sub(r"</?b>", "", transliteration_html).strip()

            features = _form_key_to_features(form_key)
            from ..morphology import morphology_features_to_form_key

            record = {
                "verb_query": query,
                "form_key": form_key,
                "canonical_form_key": morphology_features_to_form_key(features),
                "root": root,
                "binyan": binyan,
                "surface_vocalized": surface,
                "surface_plain": standard_unvocalized(surface),
                "transliteration": transliteration,
                "phonemes_raw": raw_phonemes,
                "phonemes_corrected": corrected_phonemes,
                "lexical_stress": stress,
                "vocal_shva": vocal_shva,
                "morphology": features.as_dict(),
                "source_url": verb.get("source_url", ""),
                "approval_status": "approved",
            }
            enriched.append(record)
    return enriched
