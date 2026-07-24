"""Confidence calibration and status classification for Phase 3 records.

Status hierarchy:
- verified_consensus: at least two independent production-approved sources agree,
  and no production-approved source disagrees.
- high_confidence_candidate: one strong production source plus corroborating
  corpus or private-research evidence; no disagreement.
- disputed: independent sources disagree on the accepted form.
- unresolved: insufficient evidence or a known ambiguity.
- rejected: a production source or normative rule explicitly rejects the form.
"""
from __future__ import annotations

import math

from ..normalization import normalize_hebrew


# Source trust tiers.
PRODUCTION_SOURCES = {
    "eran_tomer",
    "verb_inflector",
    "pealim_approved",
    "normative_rule_engine",
}
CORPUS_SOURCES = {"corpus"}
PRIVATE_RESEARCH_SOURCES = {"phonikud", "morphological_disambiguator", "lexicon"}


def _agreement_sources(evidence: dict) -> set[str]:
    """Return sources whose surface (or analysis) agrees with the canonical record."""
    agreed: set[str] = set()
    canonical = evidence.get("canonical", {})
    canonical_surface = normalize_hebrew(canonical.get("surface_vocalized", ""))
    for source, item in evidence.items():
        if source == "canonical":
            continue
        if not isinstance(item, dict):
            continue
        if item.get("agrees", False):
            agreed.add(source)
            continue
        if item.get("present"):
            surface = normalize_hebrew(item.get("surface_vocalized", ""))
            if surface and surface == canonical_surface:
                agreed.add(source)
    return agreed


def _disagreement_sources(evidence: dict) -> set[str]:
    """Return sources that explicitly disagree with the canonical record."""
    disagreed: set[str] = set()
    canonical = evidence.get("canonical", {})
    canonical_surface = normalize_hebrew(canonical.get("surface_vocalized", ""))
    for source, item in evidence.items():
        if source == "canonical":
            continue
        if not isinstance(item, dict):
            continue
        if item.get("rejected"):
            disagreed.add(source)
            continue
        if item.get("agrees") is False:
            disagreed.add(source)
            continue
        if item.get("present"):
            surface = normalize_hebrew(item.get("surface_vocalized", ""))
            if surface and surface != canonical_surface:
                disagreed.add(source)
    return disagreed


def _production_agreement(agreed: set[str]) -> set[str]:
    return agreed & PRODUCTION_SOURCES


def _production_disagreement(disagreed: set[str]) -> set[str]:
    return disagreed & PRODUCTION_SOURCES


def confidence_from_evidence(
    evidence: dict,
    corpus_count: int = 0,
    rule_trace: list[str] | None = None,
    unresolved: bool = False,
) -> tuple[float, str]:
    """Return (confidence, status) for a record from its evidence."""
    agreed = _agreement_sources(evidence)
    disagreed = _disagreement_sources(evidence)
    prod_agreed = _production_agreement(agreed)
    prod_disagreed = _production_disagreement(disagreed)

    if unresolved or evidence.get("abstain"):
        return 0.0, "unresolved"

    if prod_disagreed:
        # Even one production source rejection should mark the record rejected
        # unless another production source overrides it with higher priority.
        return 0.0, "rejected"

    if len(prod_agreed) >= 2:
        # Verified consensus: independent production sources agree.
        base = 0.95
        corpus_boost = 1 - math.exp(-corpus_count / 100.0)
        confidence = round(base + 0.04 * corpus_boost, 4)
        return min(confidence, 0.99), "verified_consensus"

    if prod_agreed and (agreed & CORPUS_SOURCES or (corpus_count > 10)):
        confidence = 0.85 + 0.1 * (1 - math.exp(-corpus_count / 200.0))
        return round(min(confidence, 0.94), 4), "high_confidence_candidate"

    if prod_agreed and (agreed & PRIVATE_RESEARCH_SOURCES or corpus_count > 0):
        confidence = 0.7 + 0.1 * (1 - math.exp(-corpus_count / 500.0))
        return round(min(confidence, 0.84), 4), "high_confidence_candidate"

    if disagreed:
        # Disagreement without production rejection is disputed.
        return 0.5, "disputed"

    if prod_agreed:
        return 0.6, "high_confidence_candidate"

    if corpus_count > 0:
        return 0.3, "unresolved"

    return 0.0, "unresolved"
