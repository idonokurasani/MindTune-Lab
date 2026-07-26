"""Deterministic fixed replay windows for CLM-02."""

from __future__ import annotations

from dataclasses import dataclass

from mindtune_clm.replay.features import FeaturePolicy, compute_features
from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow
from mindtune_clm.replay.quality import QualityPolicy, assess_window


@dataclass(frozen=True)
class WindowPolicy:
    """Versioned deterministic windowing policy."""

    policy_id: str
    version: str
    window_duration_s: float
    step_duration_s: float
    min_accepted_sample_count: int = 1
    min_channel_coverage: int = 1
    partial_final_window: bool = True
    feature_policy: FeaturePolicy | None = None


def _coverage_for_window(
    sample_ids: list[str],
    samples: dict[str, NormalizedSensorSample],
) -> list[str]:
    covered: set[str] = set()
    for sid in sample_ids:
        sample = samples.get(sid)
        if sample is None:
            continue
        for ch, v in sample.channel_values.items():
            if v is not None:
                covered.add(ch)
    return sorted(covered)


def _window_quality_score(
    sample_ids: list[str],
    assessments: dict[str, QualityAssessment],
) -> float:
    scores = []
    for sid in sample_ids:
        assessment = assessments.get(sid)
        if assessment and assessment.accepted:
            scores.append(assessment.quality_score)
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def make_windows(
    replay_id: str,
    samples: list[NormalizedSensorSample],
    sample_assessments: list[QualityAssessment],
    window_policy: WindowPolicy,
    quality_policy: QualityPolicy,
) -> list[ReplayWindow]:
    """Create fixed, half-open [start, end) replay windows deterministically.

    Each window knows exactly which samples fall inside it by replay timestamp.
    The final window is emitted only when ``partial_final_window`` is True and
    it contains at least one sample.
    """
    sample_by_id = {s.normalized_sample_id: s for s in samples}
    assessment_by_id = {a.sample_id: a for a in sample_assessments if a.sample_id}
    sorted_samples = sorted(
        samples,
        key=lambda s: (s.replay_relative_timestamp if s.replay_relative_timestamp is not None else -1.0, s.source_sample_index),
    )
    if not sorted_samples:
        return []

    max_time = max(
        s.replay_relative_timestamp for s in sorted_samples if s.replay_relative_timestamp is not None
    )

    windows: list[ReplayWindow] = []
    start = 0.0
    window_index = 0
    duration = window_policy.window_duration_s
    step = window_policy.step_duration_s

    while True:
        end = start + duration
        in_window = [
            s.normalized_sample_id
            for s in sorted_samples
            if s.replay_relative_timestamp is not None and start <= s.replay_relative_timestamp < end
        ]
        is_partial = end > max_time

        if not in_window and is_partial:
            break

        accepted_ids = [
            sid for sid in in_window
            if assessment_by_id.get(sid) is not None and assessment_by_id[sid].accepted
        ]
        rejected_ids = [sid for sid in in_window if sid not in accepted_ids]
        channel_coverage = _coverage_for_window(in_window, sample_by_id)
        aggregate_quality = _window_quality_score(in_window, assessment_by_id)

        feature_policy = window_policy.feature_policy or FeaturePolicy(
            policy_id="default",
            version="1.0.0",
            primary_channel=None,
            amplitude_range=1.0,
        )

        window = ReplayWindow(
            window_id=f"w-{replay_id}-{window_index}",
            start_replay_timestamp=start,
            end_replay_timestamp=min(end, max_time),
            ordered_sample_ids=in_window,
            accepted_sample_count=len(accepted_ids),
            rejected_sample_count=len(rejected_ids),
            channel_coverage=channel_coverage,
            aggregate_quality=round(aggregate_quality, 5),
            deterministic_feature_values={},
            quality_assessment_id="",
            provenance=[replay_id] + in_window,
        )

        window_assessment = assess_window(window, assessment_by_id, quality_policy)
        # Re-apply window assessment to adjust acceptance based on window-level rules.
        accepted = window_assessment.accepted
        reason_codes = list(window_assessment.reason_codes)
        if is_partial and not window_policy.partial_final_window:
            accepted = False
            reason_codes.append("partial_window_rejected")
        if len(accepted_ids) < window_policy.min_accepted_sample_count:
            accepted = False
            reason_codes.append("insufficient_accepted_samples")
        if len(channel_coverage) < window_policy.min_channel_coverage:
            accepted = False
            reason_codes.append("missing_required_channel")

        features = compute_features(window, sample_by_id, assessment_by_id, feature_policy)
        final_window = ReplayWindow(
            window_id=window.window_id,
            start_replay_timestamp=window.start_replay_timestamp,
            end_replay_timestamp=window.end_replay_timestamp,
            ordered_sample_ids=window.ordered_sample_ids,
            accepted_sample_count=window.accepted_sample_count,
            rejected_sample_count=window.rejected_sample_count,
            channel_coverage=window.channel_coverage,
            aggregate_quality=window.aggregate_quality,
            deterministic_feature_values=features,
            quality_assessment_id=window_assessment.assessment_id,
            provenance=window.provenance,
            accepted=accepted,
            reason_codes=list(dict.fromkeys(reason_codes)),
        )
        windows.append(final_window)

        if is_partial or start + step > max_time:
            break

        start += step
        window_index += 1

    return windows
