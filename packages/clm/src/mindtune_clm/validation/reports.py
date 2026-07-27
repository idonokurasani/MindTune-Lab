"""Deterministic, reproducible scientific-validation reports for CLM-08."""

from __future__ import annotations

import csv
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from io import StringIO
from typing import Any

from mindtune_clm.validation.analysis_plan import AnalysisResult
from mindtune_clm.validation.datasets import AnalysisDataset
from mindtune_clm.validation.designs import StudyDefinition
from mindtune_clm.validation.quality import QualityReport


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class StudyReport:
    """Deterministic, reproducible study report."""

    report_id: str
    study_id: str
    study_version: int
    analysis_id: str
    generated_at: float
    sections: dict[str, Any]
    limitations: list[str]
    interpretation: str
    machine_readable_results: dict[str, Any]
    format: str
    format_version: str

    def checksum(self) -> str:
        payload = self.as_dict()
        payload.pop("report_id", None)
        payload.pop("generated_at", None)
        return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "study_id": self.study_id,
            "study_version": self.study_version,
            "analysis_id": self.analysis_id,
            "generated_at": self.generated_at,
            "sections": dict(self.sections),
            "limitations": list(self.limitations),
            "interpretation": self.interpretation,
            "machine_readable_results": dict(self.machine_readable_results),
            "format": self.format,
            "format_version": self.format_version,
        }

    def to_json(self) -> str:
        return _stable_json(self.as_dict())

    def to_markdown(self) -> str:
        lines: list[str] = [
            f"# Study Report: {self.sections.get('title', self.study_id)}",
            "",
            f"- Study ID: `{self.study_id}` (version {self.study_version})",
            f"- Report ID: `{self.report_id}`",
            f"- Generated at: {self.generated_at}",
            "",
            "## Research Question",
            "",
            str(self.sections.get("research_question", "")),
            "",
            "## Primary Analysis",
            "",
            f"Effect estimate: {self.sections.get('effect_estimate', 'N/A')}",
            f"Confidence interval: {self.sections.get('confidence_interval', 'N/A')}",
            f"P-value: {self.sections.get('p_value', 'N/A')}",
            f"Adjusted p-value: {self.sections.get('adjusted_p_value', 'N/A')}",
            "",
            "## Data Quality",
            "",
            str(self.sections.get("quality", "")),
            "",
            "## Limitations",
            "",
        ]
        for lim in self.limitations:
            lines.append(f"- {lim}")
        lines.extend(["", "## Interpretation", "", self.interpretation, ""])
        return "\n".join(lines)

    def to_csv(self) -> str:
        rows = self.machine_readable_results.get("rows", [])
        if not rows or not isinstance(rows, list):
            return ""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return output.getvalue()


def _consort_summary(study: StudyDefinition, dataset: AnalysisDataset) -> dict[str, Any]:
    participants = list({r.participant_id for r in dataset.rows})
    conditions: dict[str, int] = {}
    for r in dataset.rows:
        conditions[r.condition] = conditions.get(r.condition, 0) + 1
    return {
        "participants_assigned": len(participants),
        "rows": len(dataset.rows),
        "condition_counts": conditions,
        "quality_ready": dataset.quality.analysis_ready,
        "blocking_errors": dataset.quality.blocking_errors,
    }


def generate_study_report(
    study: StudyDefinition,
    dataset: AnalysisDataset,
    result: AnalysisResult,
    quality: QualityReport | None = None,
) -> StudyReport:
    """Generate a deterministic study report."""
    quality = quality or dataset.quality
    sections = {
        "title": study.title,
        "study_id": study.study_id,
        "study_version": study.study_version,
        "research_question": study.research_question,
        "primary_endpoint_id": study.primary_endpoint_id,
        "effect_estimate": result.effect_estimate,
        "confidence_interval": list(result.confidence_interval),
        "p_value": result.p_value,
        "adjusted_p_value": result.adjusted_p_value,
        "population": result.population,
        "dataset_checksum": dataset.checksum,
        "quality": quality.as_dict(),
        "consort_summary": _consort_summary(study, dataset),
    }
    limitations = [
        "Synthetic fixture; not a real-study evidence claim.",
        "Results are conditional on the prespecified analysis plan.",
    ]
    interpretation = (
        f"The estimated effect of {result.effect_estimate} "
        f"with 95% confidence interval {list(result.confidence_interval)} "
        f"does not imply causal efficacy or therapeutic benefit beyond the study design."
    )
    return StudyReport(
        report_id=str(uuid.uuid4()),
        study_id=study.study_id,
        study_version=study.study_version,
        analysis_id=result.analysis_id,
        generated_at=time.time(),
        sections=sections,
        limitations=limitations,
        interpretation=interpretation,
        machine_readable_results=result.as_dict(),
        format="markdown",
        format_version="1.0",
    )
