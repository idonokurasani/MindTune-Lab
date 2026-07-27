"""Repository-grounded fixtures for Phase 1 Mantra engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .sheva import DIACRITICS
from .spec import GrammaticalGroup, MantraForm, MantraSpecification, PauseConfig, SpeechConfig
from .utils import load_json, normalize_unicode

CONSOLE_DIR = Path(__file__).resolve().parents[2]
MANTRA_SCRIPTS_DIR = CONSOLE_DIR / "data" / "mantra" / "scripts"


def _morphology_from_form_key(form_key: str) -> dict[str, Any]:
    """Infer person/number/gender from a Pealim-style form key."""
    parts = form_key.split("_")
    if "infinitive" in parts or "example" in parts:
        return {}
    person = None
    number = None
    gender = None
    for part in parts:
        if part in {"1", "2", "3"}:
            person = part
        elif part in {"singular", "plural"}:
            number = part
        elif part in {"masculine", "feminine"}:
            gender = part
    return {"person": person, "number": number, "gender": gender}


def load_fixture_001_lichtov() -> MantraSpecification:
    """Load the verified 001_lichtov script into a MantraSpecification."""
    data = load_json(MANTRA_SCRIPTS_DIR / "001_lichtov.json")
    groups: list[GrammaticalGroup] = []
    for group_data in data["sections"]:
        forms = []
        for line in group_data["lines"]:
            morph = _morphology_from_form_key(line.get("form_key", ""))
            hebrew_pointed = normalize_unicode(line["hebrew_with_niqqud"])
            hebrew_unpointed = "".join(c for c in hebrew_pointed if c not in DIACRITICS)
            forms.append(
                MantraForm(
                    form_key=line["form_key"],
                    hebrew_with_niqqud=hebrew_pointed,
                    hebrew_plain=hebrew_unpointed,
                    vocalized=hebrew_pointed,
                    transliteration=line.get("transliteration", ""),
                    stress_syllable_index=line.get("stress_syllable_index", 0) or 0,
                    italian_gloss=line.get("italian_gloss", ""),
                    tts_input=hebrew_unpointed,
                    person=morph.get("person"),
                    number=morph.get("number"),
                    gender=morph.get("gender"),
                )
            )
        groups.append(
            GrammaticalGroup(
                tense=group_data["section"],
                label_he=normalize_unicode(group_data.get("label_he", "")),
                label_it=group_data.get("label_it", ""),
                forms=forms,
            )
        )

    pauses = data.get("pauses_ms", {})
    return MantraSpecification(
        id="mantra-001-lichtov",
        version="1.0.0",
        language="he-IL",
        verb_id=data["verb_key"],
        hebrew_infinitive=normalize_unicode(data["hebrew_infinitive"]),
        lexical_root=data.get("root", ""),
        binyan=data.get("binyan", ""),
        groups=groups,
        repetitions_per_form=1,
        repetitions_per_cycle=1,
        cycles=1,
        speech=SpeechConfig(
            provider="speechgen",
            locale="he-IL",
            voice="Aaron",
            rate=1.0,
            pitch=0.0,
            format="wav",
        ),
        pauses=PauseConfig(
            opening_ms=500,
            closing_ms=500,
            between_forms_ms=pauses.get("between_forms", 500),
            between_groups_ms=pauses.get("between_sections", 900),
            between_cycles_ms=1200,
            segment_pause_ms=pauses.get("between_forms", 500),
            italian_cue_pause_ms=pauses.get("after_example", 700),
        ),
        output_format="wav",
        build_seed="seed-001-lichtov",
        pronunciation_lexicon_path="data/mantra/pronunciation_lexicon_001_lichtov.json",
        metadata={
            "source_url": data.get("source_url", ""),
            "script_path": str(MANTRA_SCRIPTS_DIR / "001_lichtov.json"),
        },
    )
