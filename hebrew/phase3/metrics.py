"""Reliability metrics for the Phase 3 Hebrew engine benchmark.

All metrics compare engine predictions against a frozen external reference.
The reference is the benchmark partition loaded from
hebrew.phase3.benchmark (or a similar frozen source), not the engine output.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


class BenchmarkMetrics:
    """Compute reliability metrics from (reference, prediction) pairs."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def compute(self) -> dict[str, Any]:
        total = len(self.rows)
        accepted = [
            r
            for r in self.rows
            if r.get("predicted_status") in ("verified_consensus", "high_confidence_candidate")
        ]
        abstained = [
            r
            for r in self.rows
            if r.get("predicted_status") in ("unresolved", "disputed", "rejected")
            or r.get("predicted_status") is None
        ]
        accepted_count = len(accepted)
        abstention_count = len(abstained)

        accepted_correct = 0
        accepted_total_with_reference = 0
        vocalized_match = 0
        canonical_match = 0
        pronunciation_match = 0
        stress_match = 0
        shva_match = 0
        morphology_match = 0
        variant_recall = 0
        variant_total = 0
        false_confidence = 0
        false_accept_nonexistent = 0
        false_accept_count = 0

        disagreement_by_source: Counter[str] = Counter()
        disagreement_by_category: Counter[str] = Counter()

        for r in self.rows:
            pred = r.get("predicted", {})
            ref = r.get("reference", {})
            pred_status = r.get("predicted_status", "unresolved")
            ref_status = ref.get("status", "accepted")

            # Disagreement bookkeeping.
            for disc in r.get("disagreements", []):
                src = disc.get("source", "unknown")
                cat = disc.get("category", "unknown")
                disagreement_by_source[src] += 1
                disagreement_by_category[cat] += 1

            # For accepted-case metrics, consider only predictions that the
            # engine accepted and the reference marks as accepted.
            if pred_status in ("verified_consensus", "high_confidence_candidate"):
                if ref_status == "accepted":
                    accepted_total_with_reference += 1
                    if pred.get("surface_vocalized") == ref.get("surface_vocalized"):
                        vocalized_match += 1
                    if pred.get("surface_plain") == ref.get("surface_plain"):
                        canonical_match += 1
                    if pred.get("pronunciation") == ref.get("pronunciation"):
                        pronunciation_match += 1
                    if pred.get("stress") == ref.get("stress"):
                        stress_match += 1
                    if pred.get("shva_status") == ref.get("shva_status"):
                        shva_match += 1
                    if pred.get("form_key") == ref.get("form_key") and pred.get(
                        "surface_vocalized"
                    ) == ref.get("surface_vocalized"):
                        morphology_match += 1
                    if pred.get("surface_vocalized") == ref.get("surface_vocalized"):
                        accepted_correct += 1

                    # Accepted-variant recall: list of acceptable plain surfaces.
                    variants = ref.get("accepted_variants", [ref.get("surface_plain")])
                    if variants and pred.get("surface_plain") in variants:
                        variant_recall += 1
                    variant_total += 1

                else:
                    false_confidence += 1

                if ref_status == "nonexistent" or ref_status == "rejected":
                    false_accept_nonexistent += 1
                    false_accept_count += 1

        def safe(num: int, den: int) -> float:
            return round(num / den, 4) if den else 0.0

        accepted_case_accuracy = safe(accepted_correct, accepted_total_with_reference)
        coverage = total
        abstention_rate = safe(abstention_count, total)
        false_confidence_rate = safe(false_confidence, accepted_count)
        false_acceptance_rate = safe(false_accept_nonexistent, false_accept_count)

        return {
            "total": total,
            "accepted_count": accepted_count,
            "abstention_count": abstention_count,
            "accepted_case_accuracy": accepted_case_accuracy,
            "coverage": coverage,
            "abstention_rate": abstention_rate,
            "false_confidence_rate": false_confidence_rate,
            "false_acceptance_of_nonexistent_forms": false_acceptance_rate,
            "morphology_accuracy": safe(morphology_match, accepted_total_with_reference),
            "canonical_unvocalized_spelling_accuracy": safe(
                canonical_match, accepted_total_with_reference
            ),
            "vocalized_exact_match_accuracy": safe(vocalized_match, accepted_total_with_reference),
            "pronunciation_accuracy": safe(pronunciation_match, accepted_total_with_reference),
            "stress_accuracy": safe(stress_match, accepted_total_with_reference),
            "shva_accuracy": safe(shva_match, accepted_total_with_reference),
            "accepted_variant_recall": safe(variant_recall, variant_total),
            "disagreement_rate_by_source": dict(disagreement_by_source),
            "disagreement_rate_by_category": dict(disagreement_by_category),
        }
