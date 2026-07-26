"""Deterministic window feature extraction for CLM-02."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow


@dataclass(frozen=True)
class FeaturePolicy:
    """Versioned feature extraction policy."""

    policy_id: str
    version: str
    primary_channel: str | None = None
    amplitude_range: float = 1.0


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def compute_features(  # noqa: C901
    window: ReplayWindow,
    samples: dict[str, NormalizedSensorSample],
    assessments: dict[str, QualityAssessment],
    policy: FeaturePolicy,
) -> dict[str, float]:
    """Compute a bounded deterministic feature vector for a replay window.

    Formulas:
      - signal_stability: 1 - (std(primary_channel) / amplitude_range)
      - accepted_sample_ratio: accepted / total
      - flatline_ratio: samples with no change on primary channel / total
      - normalized_variability: (max - min) / amplitude_range
      - artifact_ratio: rejected / total
      - mean_quality: mean accepted-sample quality score
      - trend: normalized sign of (last - first) on primary channel
      - missing_channel_coverage: 1 - (covered required channels / all source channels)
    """
    ordered: list[NormalizedSensorSample] = [
        s for s in (samples.get(sid) for sid in window.ordered_sample_ids) if s is not None
    ]
    total = len(ordered)
    if total == 0:
        return {
            "signal_stability": 0.0,
            "accepted_sample_ratio": 0.0,
            "flatline_ratio": 0.0,
            "normalized_variability": 0.0,
            "artifact_ratio": 1.0,
            "mean_quality": 0.0,
            "trend": 0.0,
            "missing_channel_coverage": 1.0,
        }

    accepted_total = 0
    accepted_scores: list[float] = []
    primary_values: list[float] = []
    flatlines = 0
    for sample in ordered:
        assessment = assessments.get(sample.normalized_sample_id)
        if assessment and assessment.accepted:
            accepted_total += 1
            accepted_scores.append(assessment.quality_score)
            if policy.primary_channel:
                val = sample.channel_values.get(policy.primary_channel)
                if val is not None:
                    primary_values.append(val)
            # Flatline is detected when this value equals the previous accepted value.
            if len(primary_values) >= 2 and primary_values[-1] == primary_values[-2]:
                flatlines += 1

    channel_keys = set()
    for sample in ordered:
        for ch, v in sample.channel_values.items():
            if v is not None:
                channel_keys.add(ch)
    total_channels = len(channel_keys) if channel_keys else 1
    covered = sum(1 for ch in channel_keys if ch == policy.primary_channel)

    signal_stability = 1.0
    normalized_variability = 0.0
    trend = 0.0
    if primary_values:
        std = _std(primary_values)
        signal_stability = max(0.0, 1.0 - (std / max(1e-9, policy.amplitude_range)))
        rmin = min(primary_values)
        rmax = max(primary_values)
        normalized_variability = (rmax - rmin) / max(1e-9, policy.amplitude_range)
        trend = (primary_values[-1] - primary_values[0]) / max(1e-9, policy.amplitude_range)
        trend = max(-1.0, min(1.0, trend))

    accepted_sample_ratio = accepted_total / total
    flatline_ratio = flatlines / total if total else 0.0
    artifact_ratio = (total - accepted_total) / total
    mean_quality = _mean(accepted_scores)
    missing_channel_coverage = 1.0 - (covered / total_channels)

    return {
        "signal_stability": round(signal_stability, 5),
        "accepted_sample_ratio": round(accepted_sample_ratio, 5),
        "flatline_ratio": round(flatline_ratio, 5),
        "normalized_variability": round(normalized_variability, 5),
        "artifact_ratio": round(artifact_ratio, 5),
        "mean_quality": round(mean_quality, 5),
        "trend": round(trend, 5),
        "missing_channel_coverage": round(missing_channel_coverage, 5),
    }
