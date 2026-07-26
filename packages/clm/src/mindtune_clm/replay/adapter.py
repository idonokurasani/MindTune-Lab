"""Adapter from ReplayWindow to CLM-01 ObservationFrame."""

from __future__ import annotations

from mindtune_clm.observations import ObservationFrame
from mindtune_clm.replay.models import NormalizedSensorSample, ReplayWindow


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _channel_values_for_eeg(
    window: ReplayWindow,
    samples: dict[str, NormalizedSensorSample],
    channel_name: str,
) -> list[float]:
    values: list[float] = []
    for sid in window.ordered_sample_ids:
        sample = samples.get(sid)
        if sample is None:
            continue
        v = sample.channel_values.get(channel_name)
        if v is not None:
            values.append(v)
    return values


def to_observation_frame(
    window: ReplayWindow,
    samples: dict[str, NormalizedSensorSample],
    replay_id: str,
    sequence_number: int,
    eeg_channel: str | None = "eeg_stability",
    behavioral_channel: str | None = None,
) -> ObservationFrame:
    """Convert one accepted replay window into one CLM ObservationFrame.

    The adapter explicitly maps replay identifiers, sensor stability, quality,
    available modalities, and provenance.  If the window has no usable EEG
    evidence, ``eeg_stability`` and ``eeg_quality`` are ``None`` so CLM-01
    continues with missing EEG rather than crashing.
    """
    available_modalities: list[str] = []
    eeg_stability: float | None = None
    eeg_quality: str | None = None

    if eeg_channel and window.accepted and eeg_channel in window.channel_coverage:
        values = _channel_values_for_eeg(window, samples, eeg_channel)
        if values:
            eeg_stability = round(_mean(values), 5)
            eeg_quality = "good"
            available_modalities.append("eeg")
    elif not window.accepted:
        # Explicit rejection: keep the sensor modality listed but mark quality poor.
        if eeg_channel and eeg_channel in window.channel_coverage:
            values = _channel_values_for_eeg(window, samples, eeg_channel)
            if values:
                eeg_stability = round(_mean(values), 5)
            else:
                eeg_stability = None
            eeg_quality = "poor_signal"
            available_modalities.append("eeg")

    behavioral_latency_ms: float | None = None
    hesitation_score: float | None = None
    error_score: float | None = None
    if behavioral_channel and behavioral_channel in window.channel_coverage:
        available_modalities.append("behavioral")
        # No fabricated behavioral evidence; leave the fields absent.

    return ObservationFrame(
        observation_frame_id=f"obs-{window.window_id}",
        control_cycle_id=f"cc-{window.window_id}",
        session_id=f"replay-{replay_id}",
        sequence_number=sequence_number,
        observation_timestamp=window.end_replay_timestamp,
        behavioral_latency_ms=behavioral_latency_ms,
        hesitation_score=hesitation_score,
        error_score=error_score,
        eeg_stability=eeg_stability,
        eeg_quality=eeg_quality,
        respiration_stability=None,
        voice_stability=None,
        available_modalities=available_modalities,
        source_event_ids=list(window.ordered_sample_ids),
    )
