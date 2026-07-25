"""Deterministic cognitive-state estimator with hysteresis and sustained recovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.enums import CognitiveState


@dataclass
class CognitiveStateUpdate:
    """Output of one estimator update."""

    prior_state: CognitiveState
    state: CognitiveState
    load: float
    consecutive_high: int
    consecutive_low: int
    recovery_steps_remaining: int
    eeg_ignored: bool
    reason: str


@dataclass
class CognitiveStateEstimator:
    """Estimate cognitive load from behavioral and EEG evidence.

    Behavioral evidence is authoritative: an EEG-detected elevation cannot
    force an adaptation when the behavioral sample is already correct and
    within the latency bound.  Low-quality EEG (artifact or poor signal) is
    ignored entirely.

    State transitions are hysteretic and require sustained evidence:
    ``min_high`` consecutive elevated samples to leave STABLE through
    POSSIBLE_DRIFT to RECOVERY_REQUIRED, and ``min_low`` consecutive low
    samples plus ``recovery_steps`` to return to STABLE through RECOVERING.
    """

    high_threshold: float = 0.6
    low_threshold: float = 0.3
    min_high: int = 2
    min_low: int = 2
    recovery_steps: int = 3
    eeg_bad_flags: frozenset[str] = field(default_factory=lambda: frozenset({"artifact", "poor_signal"}))

    state: CognitiveState = field(default=CognitiveState.STABLE)
    consecutive_high: int = 0
    consecutive_low: int = 0
    recovery_steps_remaining: int = 0

    def update(
        self,
        *,
        correct: bool,
        latency: float,
        latency_bound: float,
        eeg_features: dict[str, Any] | None = None,
    ) -> CognitiveStateUpdate:
        """Ingest one trial's behavioral and EEG evidence and return the new state."""
        behavioral_load = self._behavioral_load(correct, latency, latency_bound)
        eeg_load, eeg_ignored = self._eeg_load(eeg_features)
        prior_state = self.state

        # Behavioral evidence is authoritative: EEG can only amplify an already
        # non-zero behavioral load; it cannot create an adaptation by itself.
        if behavioral_load == 0.0:
            combined_load = 0.0
            eeg_ignored = True
        else:
            combined_load = max(behavioral_load, eeg_load)

        self._transition(combined_load)

        reason = (
            f"behavioral_load={behavioral_load:.2f} eeg_load={eeg_load:.2f} "
            f"combined={combined_load:.2f} state={self.state.value}"
        )
        return CognitiveStateUpdate(
            prior_state=prior_state,
            state=self.state,
            load=combined_load,
            consecutive_high=self.consecutive_high,
            consecutive_low=self.consecutive_low,
            recovery_steps_remaining=self.recovery_steps_remaining,
            eeg_ignored=eeg_ignored,
            reason=reason,
        )

    def _behavioral_load(self, correct: bool, latency: float, latency_bound: float) -> float:
        if not correct:
            return 1.0
        if latency > latency_bound:
            return 0.5
        return 0.0

    def _eeg_load(self, eeg_features: dict[str, Any] | None) -> tuple[float, bool]:
        if eeg_features is None:
            return 0.0, True
        quality_flags = eeg_features.get("quality_flags", [])
        if isinstance(quality_flags, str):
            quality_flags = [quality_flags]
        if any(flag in self.eeg_bad_flags for flag in quality_flags):
            return 0.0, True
        payload = eeg_features.get("payload", {})
        if isinstance(payload, dict):
            return float(payload.get("cognitive_load_index", 0.0)), False
        return 0.0, True

    def _transition(self, combined_load: float) -> None:  # noqa: C901
        if combined_load >= self.high_threshold:
            self.consecutive_high += 1
            self.consecutive_low = 0
            if self.state is CognitiveState.STABLE:
                # First high sample moves to POSSIBLE_DRIFT (warning, no action).
                self.state = CognitiveState.POSSIBLE_DRIFT
            if self.consecutive_high >= self.min_high:
                # Sustained high triggers recovery assistance.
                if self.state in (
                    CognitiveState.POSSIBLE_DRIFT,
                    CognitiveState.RECOVERING,
                    CognitiveState.STABLE,
                ):
                    self.state = CognitiveState.RECOVERY_REQUIRED
                    self.recovery_steps_remaining = self.recovery_steps
        elif combined_load <= self.low_threshold:
            self.consecutive_low += 1
            self.consecutive_high = 0
            if self.state is CognitiveState.POSSIBLE_DRIFT:
                if self.consecutive_low >= self.min_low:
                    self.state = CognitiveState.STABLE
            elif self.state is CognitiveState.RECOVERY_REQUIRED:
                if self.consecutive_low >= self.min_low:
                    self.state = CognitiveState.RECOVERING
                    self.recovery_steps_remaining = self.recovery_steps
            elif self.state is CognitiveState.RECOVERING:
                self.recovery_steps_remaining = max(0, self.recovery_steps_remaining - 1)
                if self.recovery_steps_remaining == 0:
                    self.state = CognitiveState.STABLE
        else:
            # Dead band: clear both counters so oscillation around a threshold
            # does not accumulate sustained evidence.
            self.consecutive_high = 0
            self.consecutive_low = 0
