"""Source provenance and conflict detection."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import SourceDisagreement, SourceEvidence


def create_source_evidence(
    source: str,
    record: dict[str, Any],
    confidence: float = 1.0,
    trust_tier: int = 3,
) -> SourceEvidence:
    return SourceEvidence(
        source=source,
        record=record,
        confidence=confidence,
        trust_tier=trust_tier,
    )


def compare_values(
    form_key: str,
    field: str,
    values: dict[str, Any],
    severity: str = "major",
) -> SourceDisagreement | None:
    """Return a disagreement if values differ across sources."""
    normalized = {k: str(v).strip() for k, v in values.items()}
    if len(set(normalized.values())) <= 1:
        return None
    return SourceDisagreement(
        field_name=field,
        values=values,
        severity=severity,
        resolution="unresolved",
    )


def classify_difference(
    expected: str,
    actual: str,
) -> str:
    """Classify the type of difference between two surface forms."""
    if expected == actual:
        return "exact match"
    if expected.replace(" ", "") == actual.replace(" ", ""):
        return "spelling-only mismatch (whitespace)"
    # placeholder heuristics
    if "ו" in actual and "ו" not in expected:
        return "mater lectionis mismatch"
    return "spelling/vocalization mismatch"


def reconcile_stress(values: dict[str, int], approved_source: str | None = None) -> int:
    """Pick a stress value from source evidence.

    Hierarchy: manually approved source > pealim > others.
    """
    if approved_source and approved_source in values:
        return int(values[approved_source])
    for source in ["pealim", "eran_tomer", "verb_inflector", "phonikud"]:
        if source in values:
            return int(values[source])
    return int(list(values.values())[0])


def build_provenance_report(
    sources: dict[str, dict[str, Any]],
    approved_source: str | None = "pealim",
) -> dict[str, Any]:
    """Build a provenance report with disagreements and resolved values."""
    report = {
        "sources": sources,
        "disagreements": [],
        "resolved": {},
    }

    # Surface form disagreement
    surface_values = {
        k: v.get("surface_vocalized", "") for k, v in sources.items() if v.get("surface_vocalized")
    }
    if len(set(surface_values.values())) > 1:
        report["disagreements"].append(
            compare_values("surface_vocalized", "surface_vocalized", surface_values)
        )
    report["resolved"]["surface_vocalized"] = surface_values.get(
        approved_source, list(surface_values.values())[0] if surface_values else ""
    )

    # Stress disagreement
    stress_values = {
        k: v.get("lexical_stress", 0) for k, v in sources.items() if v.get("lexical_stress")
    }
    if len(set(stress_values.values())) > 1:
        report["disagreements"].append(
            compare_values("lexical_stress", "lexical_stress", stress_values, severity="major")
        )
    report["resolved"]["lexical_stress"] = reconcile_stress(stress_values, approved_source)

    return report
