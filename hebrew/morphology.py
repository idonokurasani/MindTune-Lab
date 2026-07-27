"""Morphological parsing and feature conversion."""

from __future__ import annotations

from .models import MorphologicalFeatures


TENSE_MAP = {
    "PAST": "past",
    "PRESENT": "present",
    "FUTURE": "future",
    "IMPERATIVE": "imperative",
    "INFINITIVE": "infinitive",
}

PERSON_MAP = {
    "FIRST": "first",
    "SECOND": "second",
    "THIRD": "third",
}

GENDER_MAP = {
    "M": "masculine",
    "F": "feminine",
    "MF": "masculine+feminine",
}

NUMBER_MAP = {
    "SINGULAR": "singular",
    "PLURAL": "plural",
}


def parse_morphology_tag(
    tag: str, pattern: str = "", table_number: int = 0
) -> MorphologicalFeatures:
    """Parse a Verb Inflector morphology tag into a MorphologicalFeatures object."""
    parts = [p.strip() for p in tag.split("+")]
    features = MorphologicalFeatures(pattern=pattern, table_number=table_number)

    for p in parts:
        upper = p.upper()
        if upper in TENSE_MAP:
            features.tense = TENSE_MAP[upper]
        elif upper in PERSON_MAP:
            features.person = PERSON_MAP[upper]
        elif upper in GENDER_MAP:
            features.gender = GENDER_MAP[upper]
        elif upper in NUMBER_MAP:
            features.number = NUMBER_MAP[upper]
        elif upper in ("COMPLETE", "MISSING"):
            features.completeness = upper.lower()

    # Tags without tense but with person/gender/number are passive participles.
    if not features.tense and features.person and features.gender and features.number:
        features.tense = "past_participle"
        features.person = ""  # participles are not inflected for person

    return features


def morphology_features_to_form_key(features: MorphologicalFeatures) -> str:
    """Convert a feature set to a normalized form key."""

    def normalize(value: str) -> str:
        value = value.lower().strip()
        if value in ("masculine+feminine", "masc+fem"):
            return "mf"
        if value == "masculine":
            return "m"
        if value == "feminine":
            return "f"
        return value

    # Present tense and participles are not inflected for person in Hebrew.
    include_person = features.tense not in ("present", "past_participle")
    person = normalize(features.person) if include_person else ""

    parts = [
        normalize(features.tense),
        person,
        normalize(features.gender),
        normalize(features.number),
    ]
    parts = [p for p in parts if p]
    return "_".join(parts) or "unknown"


def tense_name_for_display(tense: str) -> str:
    return tense.lower()


def binyan_from_pattern(pattern: str) -> str:
    """Map Verb Inflector pattern letter to a Hebrew binyan name."""
    mapping = {
        "A": "PA'AL",
        "B": "NIF'AL",
        "C": "PI'EL",
        "D": "PU'AL",
        "E": "HITPA'EL",
        "F": "HIF'IL",
        "G": "HUF'AL",
    }
    return mapping.get(pattern.upper(), "UNKNOWN")


def pattern_from_binyan(binyan: str) -> str:
    """Map binyan name to Verb Inflector pattern letter(s)."""
    mapping = {
        "PA'AL": "A",
        "NIF'AL": "B",
        "PI'EL": "C",
        "PU'AL": "D",
        "HITPA'EL": "E",
        "HIF'IL": "F",
        "HUF'AL": "G",
    }
    return mapping.get(binyan.upper(), "")
