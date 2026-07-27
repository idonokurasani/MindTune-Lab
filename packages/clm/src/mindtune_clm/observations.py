"""Observation frames and multi-modal evidence extraction for CLM-01."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ObservationFrame:
    """A domain-neutral, immutable observation frame for the mantra control loop."""

    observation_frame_id: str
    control_cycle_id: str
    session_id: str
    sequence_number: int
    observation_timestamp: float
    behavioral_latency_ms: float | None = None
    hesitation_score: float | None = None
    error_score: float | None = None
    eeg_stability: float | None = None
    eeg_quality: str | None = None
    respiration_stability: float | None = None
    voice_stability: float | None = None
    available_modalities: list[str] = field(default_factory=list)
    source_event_ids: list[str] = field(default_factory=list)

    def has_modality(self, modality: str) -> bool:
        """Return True when the modality is explicitly listed as available."""
        return modality in self.available_modalities


def _bad_quality(quality: str | None, bad_flags: set[str]) -> bool:
    """Return True when the quality string or flags contain a rejection marker."""
    if quality is None:
        return False
    parts = {part.strip().lower() for part in quality.split(",")}
    return bool(parts & bad_flags)


def _value(frame: ObservationFrame, calibrated_values: dict[str, float] | None, name: str) -> float | None:
    """Return the calibrated value when provided, otherwise the raw value."""
    if calibrated_values is not None and name in calibrated_values:
        return calibrated_values[name]
    return getattr(frame, name)  # type: ignore[no-any-return]


@dataclass
class FusedEvidence:
    """Result of fusing the observation frame into a single load sample."""

    load: float
    source_observation_frame_id: str = ""
    used: list[str] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)


def fuse_observation(  # noqa: C901
    frame: ObservationFrame,
    latency_bound_ms: float = 1000.0,
    calibrated_values: dict[str, float] | None = None,
) -> FusedEvidence:
    """Fuse all available, high-quality modalities into a 0..1 load sample.

    Missing modalities are ignored. Low-quality evidence is explicitly rejected
    and the reason is preserved. EEG is not authoritative: one noisy EEG sample
    cannot cause an immediate high-impact intervention because the resulting load
    is only one input to the hysteretic state estimator.

    When ``calibrated_values`` is supplied, those values are used in place of
    the raw values for the named features while the raw ObservationFrame is
    left unchanged for audit.
    """
    used: list[str] = []
    rejected: list[dict[str, Any]] = []
    reason_codes: list[str] = []
    loads: list[float] = []

    bad_eeg_flags = {"artifact", "poor_signal", "poor"}

    # Behavioral evidence
    behavioral_latency = _value(frame, calibrated_values, "behavioral_latency_ms")
    hesitation = _value(frame, calibrated_values, "hesitation_score")
    error = _value(frame, calibrated_values, "error_score")
    if behavioral_latency is not None or hesitation is not None or error is not None:
        behavioral_load = 0.0
        behavioral_parts: list[str] = []
        if error is not None and error >= 0.5:
            behavioral_load = max(behavioral_load, 1.0)
            behavioral_parts.append("error")
        if hesitation is not None and hesitation >= 0.5:
            behavioral_load = max(behavioral_load, 0.7)
            behavioral_parts.append("hesitation")
        if behavioral_latency is not None and behavioral_latency > latency_bound_ms:
            behavioral_load = max(behavioral_load, 0.5)
            behavioral_parts.append("latency")
        if behavioral_parts:
            used.append("behavioral")
            loads.append(behavioral_load)
            reason_codes.append(f"behavioral_load={behavioral_load:.2f}({','.join(behavioral_parts)})")
        else:
            # Behavioral present but within bounds counts as evidence of stability.
            used.append("behavioral")
            loads.append(0.0)
            reason_codes.append("behavioral_load=0.00(within_bounds)")

    # EEG evidence
    eeg_stability = _value(frame, calibrated_values, "eeg_stability")
    eeg_quality = frame.eeg_quality
    if eeg_stability is not None or eeg_quality is not None:
        if _bad_quality(eeg_quality, bad_eeg_flags):
            rejected.append({
                "observation_frame_id": frame.observation_frame_id,
                "modality": "eeg",
                "reason": "low_quality",
                "quality": eeg_quality,
            })
            reason_codes.append("eeg_rejected_low_quality")
        elif eeg_stability is not None:
            # Low stability implies higher cognitive load.
            eeg_load = max(0.0, min(1.0, 1.0 - eeg_stability))
            used.append("eeg")
            loads.append(eeg_load)
            reason_codes.append(f"eeg_load={eeg_load:.2f}")
        else:
            rejected.append({
                "observation_frame_id": frame.observation_frame_id,
                "modality": "eeg",
                "reason": "missing_stability",
                "quality": eeg_quality,
            })
            reason_codes.append("eeg_rejected_missing_stability")

    # Respiration and voice placeholders are accepted but not used in CLM-01.
    if _value(frame, calibrated_values, "respiration_stability") is not None:
        used.append("respiration")
        reason_codes.append("respiration_ignored_placeholder")
    if _value(frame, calibrated_values, "voice_stability") is not None:
        used.append("voice")
        reason_codes.append("voice_ignored_placeholder")

    if not loads:
        # No usable modalities: the loop continues with a neutral load.
        return FusedEvidence(
            load=0.0,
            source_observation_frame_id=frame.observation_frame_id,
            used=used,
            rejected=rejected,
            reason_codes=reason_codes + ["no_usable_evidence"],
        )

    combined = max(loads)
    return FusedEvidence(
        load=combined,
        source_observation_frame_id=frame.observation_frame_id,
        used=used,
        rejected=rejected,
        reason_codes=reason_codes,
    )
