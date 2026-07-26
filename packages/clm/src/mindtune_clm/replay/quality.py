"""Deterministic sample and window quality gating for CLM-02."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow


@dataclass(frozen=True)
class QualityPolicy:
    """Versioned deterministic quality policy."""

    policy_id: str
    version: str
    amplitude_min: float = -1.0e6
    amplitude_max: float = 1.0e6
    flatline_tolerance: float = 0.0
    discontinuity_threshold: float = 1.0e6
    max_missing_channels: int = 0
    max_missingness: float = 1.0
    artifact_keywords: set[str] = field(default_factory=lambda: {"artifact", "poor", "poor_signal", "bad"})
    min_accepted_sample_count: int = 1
    min_channel_coverage: int = 1

    def assess(self, sample: NormalizedSensorSample, previous: NormalizedSensorSample | None = None) -> QualityAssessment:
        """Assess one normalized sample."""
        return assess_sample(sample, previous, self)

    def assess_window(self, window: ReplayWindow, sample_assessments: dict[str, QualityAssessment]) -> QualityAssessment:
        """Assess one replay window."""
        return assess_window(window, sample_assessments, self)


def assess_sample(  # noqa: C901
    sample: NormalizedSensorSample,
    previous: NormalizedSensorSample | None,
    policy: QualityPolicy,
) -> QualityAssessment:
    """Return a deterministic quality assessment for one normalized sample."""
    reason_codes: list[str] = []
    artifacts: list[str] = []
    missing_channels = 0
    total_channels = len(sample.channel_values)

    if sample.source_timestamp is None:
        reason_codes.append("missing_timestamp")

    if sample.replay_relative_timestamp is None:
        reason_codes.append("timestamp_regression")

    if "duplicate_rejected" in sample.normalization_operations:
        reason_codes.append("duplicate_sample")

    if "parse_failed" in " ".join(sample.normalization_operations):
        reason_codes.append("malformed_value")

    for op in sample.normalization_operations:
        if op.startswith("missing_required_channel:"):
            reason_codes.append("missing_required_channel")
            missing_channels += 1
        elif op.startswith("malformed_value:"):
            reason_codes.append("malformed_value")

    flatline_channels = 0
    for ch, value in sample.channel_values.items():
        if value is None:
            missing_channels += 1
            continue
        if not math.isfinite(value):
            reason_codes.append("malformed_value")
            continue
        if value < policy.amplitude_min or value > policy.amplitude_max:
            reason_codes.append("amplitude_out_of_range")
            artifacts.append(f"amplitude_out_of_range:{ch}")
        if previous is not None:
            prev_value = previous.channel_values.get(ch)
            if prev_value is not None and math.isfinite(prev_value):
                if policy.flatline_tolerance is not None and abs(value - prev_value) <= policy.flatline_tolerance:
                    flatline_channels += 1
                if abs(value - prev_value) > policy.discontinuity_threshold:
                    reason_codes.append("abrupt_discontinuity")
                    artifacts.append(f"abrupt_discontinuity:{ch}")

    # We do not have the original raw quality string in the normalized sample,
    # but the source-provided quality flag can be preserved in normalization
    # operations if the parser stores it.  For this slice we use a sentinel
    # operation string injected by the runner when the raw quality is present.
    if any("quality_flag:" in op for op in sample.normalization_operations):
        reason_codes.append("poor_signal")
        artifacts.append("movement_or_artifact_flag")

    missingness = missing_channels / max(1, total_channels)
    if missingness > policy.max_missingness:
        reason_codes.append("excessive_missingness")

    quality_score = max(0.0, 1.0 - len(reason_codes) * 0.1)
    accepted_sample = len(reason_codes) == 0

    return QualityAssessment(
        assessment_id=f"qa-{sample.normalized_sample_id}",
        sample_id=sample.normalized_sample_id,
        accepted=accepted_sample,
        quality_score=round(quality_score, 3),
        reason_codes=list(dict.fromkeys(reason_codes)),
        detected_artifacts=artifacts,
        missingness=round(missingness, 3),
        policy_version=policy.version,
        source_ids=list(sample.source_provenance),
    )


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def assess_window(
    window: ReplayWindow,
    sample_assessments: dict[str, QualityAssessment],
    policy: QualityPolicy,
) -> QualityAssessment:
    """Assess a replay window based on its accepted samples and coverage."""
    reason_codes: list[str] = []
    accepted = 0
    rejected = 0
    accepted_scores: list[float] = []
    accepted_ids: list[str] = []

    for sample_id in window.ordered_sample_ids:
        assessment = sample_assessments.get(sample_id)
        if assessment is None:
            rejected += 1
            continue
        if assessment.accepted:
            accepted += 1
            accepted_scores.append(assessment.quality_score)
            accepted_ids.extend(assessment.source_ids)
        else:
            rejected += 1
            if any("artifact" in code or "poor_signal" in code for code in assessment.reason_codes):
                reason_codes.append("poor_signal")

    total = accepted + rejected
    if accepted < policy.min_accepted_sample_count:
        reason_codes.append("insufficient_accepted_samples")
    if len(window.channel_coverage) < policy.min_channel_coverage:
        reason_codes.append("missing_required_channel")

    missingness = (total - accepted) / max(1, total)
    if missingness > policy.max_missingness:
        reason_codes.append("excessive_missingness")

    quality_score = round(_mean(accepted_scores), 3)
    accepted_window = len(reason_codes) == 0

    return QualityAssessment(
        assessment_id=f"qa-{window.window_id}",
        window_id=window.window_id,
        accepted=accepted_window,
        quality_score=quality_score,
        reason_codes=list(dict.fromkeys(reason_codes)),
        detected_artifacts=[],
        missingness=round(missingness, 3),
        policy_version=policy.version,
        source_ids=list(dict.fromkeys(accepted_ids)),
    )
