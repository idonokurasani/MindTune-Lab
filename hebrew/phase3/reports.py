"""Markdown report generators for Phase 3."""
from __future__ import annotations

import json
from pathlib import Path


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def metrics_to_markdown(metrics: dict, title: str = "Phase 3 Reliability Metrics") -> str:
    """Convert a metrics dict to a markdown report."""
    sections = [f"# {title}", ""]
    sections.append("## Summary")
    summary_rows = [
        ["Metric", "Value"],
        ["Total records", metrics.get("total", 0)],
        ["Accepted records", metrics.get("accepted_count", 0)],
        ["Abstained records", metrics.get("abstention_count", 0)],
        ["Accepted-case accuracy", metrics.get("accepted_case_accuracy", 0.0)],
        ["Coverage", metrics.get("coverage", 0)],
        ["Abstention rate", metrics.get("abstention_rate", 0.0)],
        ["False-confidence rate", metrics.get("false_confidence_rate", 0.0)],
        ["False acceptance of nonexistent forms", metrics.get("false_acceptance_of_nonexistent_forms", 0.0)],
        ["Morphology accuracy", metrics.get("morphology_accuracy", 0.0)],
        ["Canonical unvocalized spelling accuracy", metrics.get("canonical_unvocalized_spelling_accuracy", 0.0)],
        ["Vocalized exact-match accuracy", metrics.get("vocalized_exact_match_accuracy", 0.0)],
        ["Pronunciation accuracy", metrics.get("pronunciation_accuracy", 0.0)],
        ["Stress accuracy", metrics.get("stress_accuracy", 0.0)],
        ["Shva accuracy", metrics.get("shva_accuracy", 0.0)],
        ["Accepted-variant recall", metrics.get("accepted_variant_recall", 0.0)],
    ]
    sections.append(_md_table(["Metric", "Value"], summary_rows[1:]))
    sections.append("")

    if metrics.get("disagreement_rate_by_source"):
        sections.append("## Disagreement rate by source")
        rows = [[k, v] for k, v in metrics["disagreement_rate_by_source"].items()]
        sections.append(_md_table(["Source", "Count"], rows))
        sections.append("")

    if metrics.get("disagreement_rate_by_category"):
        sections.append("## Disagreement rate by category")
        rows = [[k, v] for k, v in metrics["disagreement_rate_by_category"].items()]
        sections.append(_md_table(["Category", "Count"], rows))
        sections.append("")

    return "\n".join(sections)


def write_metrics_report(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(metrics_to_markdown(metrics), encoding="utf-8")


def write_json_report(data: dict | list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
