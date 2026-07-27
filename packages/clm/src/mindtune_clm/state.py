"""Cognitive-state estimate, control state, and estimator for CLM-01."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.observations import ObservationFrame, fuse_observation
from mpe.enums import CognitiveState


@dataclass(frozen=True)
class CognitiveStateEstimate:
    """A typed, immutable cognitive-state estimate for the control loop."""

    estimate_id: str
    source_observation_frame_id: str
    source_control_cycle_id: str
    cognitive_state: CognitiveState
    attention_stability: float
    cognitive_load: float
    fatigue_probability: float
    recovery_probability: float
    confidence: float
    trend: str
    validity_horizon: float
    evidence_used: list[str] = field(default_factory=list)
    evidence_rejected: list[dict[str, Any]] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MantraControlState:
    """Immutable control parameters for the mantra actuator.

    Baseline values represent the default presentation with *no added
    assistance* (assistance_level == 0.0). Safety bounds are enforced by the
    actuator; any proposed state is clamped into these ranges.
    """

    tempo_ratio: float = 1.0
    pre_stimulus_pause_ms: int = 0
    post_stimulus_pause_ms: int = 0
    repetition_count: int = 1
    prosodic_emphasis: float = 0.0
    vocal_energy: float = 0.0
    breathing_cue: bool = False
    assistance_level: float = 0.0
    control_state_id: str = ""

    BOUNDS: dict[str, Any] = field(
        default_factory=lambda: {
            "tempo_ratio": (0.5, 1.0),
            "pre_stimulus_pause_ms": (0, 5000),
            "post_stimulus_pause_ms": (0, 3000),
            "repetition_count": (1, 5),
            "prosodic_emphasis": (0.0, 1.0),
            "vocal_energy": (0.0, 1.0),
            "breathing_cue": (False, True),  # range is conceptual for bool
            "assistance_level": (0.0, 1.0),
        },
        repr=False,
    )

    def __post_init__(self) -> None:
        if not self.control_state_id:
            object.__setattr__(self, "control_state_id", f"cs-{uuid.uuid4()}")

    @classmethod
    def baseline(cls) -> "MantraControlState":
        """Return the canonical baseline control state (no added assistance)."""
        return cls(
            tempo_ratio=1.0,
            pre_stimulus_pause_ms=0,
            post_stimulus_pause_ms=0,
            repetition_count=1,
            prosodic_emphasis=0.0,
            vocal_energy=0.0,
            breathing_cue=False,
            assistance_level=0.0,
            control_state_id="baseline",
        )

    def clamped(self) -> "MantraControlState":
        """Return a new state clamped to the safety bounds."""
        b = self.BOUNDS
        return MantraControlState(
            tempo_ratio=max(b["tempo_ratio"][0], min(b["tempo_ratio"][1], self.tempo_ratio)),
            pre_stimulus_pause_ms=max(
                b["pre_stimulus_pause_ms"][0],
                min(b["pre_stimulus_pause_ms"][1], self.pre_stimulus_pause_ms),
            ),
            post_stimulus_pause_ms=max(
                b["post_stimulus_pause_ms"][0],
                min(b["post_stimulus_pause_ms"][1], self.post_stimulus_pause_ms),
            ),
            repetition_count=max(
                b["repetition_count"][0],
                min(b["repetition_count"][1], self.repetition_count),
            ),
            prosodic_emphasis=max(
                b["prosodic_emphasis"][0],
                min(b["prosodic_emphasis"][1], self.prosodic_emphasis),
            ),
            vocal_energy=max(b["vocal_energy"][0], min(b["vocal_energy"][1], self.vocal_energy)),
            breathing_cue=self.breathing_cue,
            assistance_level=max(
                b["assistance_level"][0],
                min(b["assistance_level"][1], self.assistance_level),
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable dictionary representation (without the id)."""
        return {
            "tempo_ratio": self.tempo_ratio,
            "pre_stimulus_pause_ms": self.pre_stimulus_pause_ms,
            "post_stimulus_pause_ms": self.post_stimulus_pause_ms,
            "repetition_count": self.repetition_count,
            "prosodic_emphasis": self.prosodic_emphasis,
            "vocal_energy": self.vocal_energy,
            "breathing_cue": self.breathing_cue,
            "assistance_level": self.assistance_level,
        }


@dataclass
class StateEstimator:
    """Hysteretic, multi-modal cognitive-state estimator.

    The estimator is sensor-independent: it fuses any available high-quality
    modalities and explicitly tracks rejected evidence. Sustained evidence is
    required for both deterioration and recovery.
    """

    high_threshold: float = 0.6
    low_threshold: float = 0.3
    min_high: int = 2
    min_low: int = 1
    recovery_steps: int = 1
    latency_bound_ms: float = 1000.0

    state: CognitiveState = field(default=CognitiveState.STABLE)
    consecutive_high: int = 0
    consecutive_low: int = 0
    recovery_steps_remaining: int = 0
    estimate_counter: int = 0

    def estimate(
        self,
        frame: ObservationFrame,
        calibrated_values: dict[str, float] | None = None,
    ) -> CognitiveStateEstimate:
        """Return the next immutable estimate from an observation frame.

        When ``calibrated_values`` is supplied, the estimator fuses those values
        while leaving the raw ObservationFrame unchanged for audit.
        """
        fused = fuse_observation(
            frame,
            latency_bound_ms=self.latency_bound_ms,
            calibrated_values=calibrated_values,
        )
        self.estimate_counter += 1
        self._transition(fused.load)

        if self.state == CognitiveState.STABLE:
            trend = "stable"
        elif self.state in (CognitiveState.POSSIBLE_DRIFT, CognitiveState.RECOVERY_REQUIRED):
            trend = "deteriorating"
        else:
            trend = "recovering"

        load = fused.load
        confidence = self._confidence()
        recovery_probability = (
            0.8
            if self.state in (CognitiveState.RECOVERING, CognitiveState.STABLE) and load <= self.low_threshold
            else 0.0
        )

        return CognitiveStateEstimate(
            estimate_id=f"estimate-{frame.session_id}-{self.estimate_counter}",
            source_observation_frame_id=fused.source_observation_frame_id,
            source_control_cycle_id=frame.control_cycle_id,
            cognitive_state=self.state,
            attention_stability=max(0.0, 1.0 - load),
            cognitive_load=load,
            fatigue_probability=load,
            recovery_probability=recovery_probability,
            confidence=confidence,
            trend=trend,
            validity_horizon=frame.observation_timestamp + 1.0,
            evidence_used=list(fused.used),
            evidence_rejected=list(fused.rejected),
            reason_codes=list(fused.reason_codes)
            + [
                f"consecutive_high={self.consecutive_high}",
                f"consecutive_low={self.consecutive_low}",
                f"recovery_steps_remaining={self.recovery_steps_remaining}",
            ],
        )

    def _transition(self, load: float) -> None:  # noqa: C901
        if load >= self.high_threshold:
            self.consecutive_high += 1
            self.consecutive_low = 0
            if self.state is CognitiveState.STABLE:
                self.state = CognitiveState.POSSIBLE_DRIFT
            if self.consecutive_high >= self.min_high:
                self.state = CognitiveState.RECOVERY_REQUIRED
                self.recovery_steps_remaining = self.recovery_steps
        elif load <= self.low_threshold:
            self.consecutive_low += 1
            self.consecutive_high = 0
            if self.state is CognitiveState.POSSIBLE_DRIFT:
                # One low sample returns from possible drift to stable.
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
            # Dead band: clear counters to prevent threshold oscillation.
            self.consecutive_high = 0
            self.consecutive_low = 0

    def _confidence(self) -> float:
        if self.state is CognitiveState.RECOVERY_REQUIRED:
            return min(1.0, self.consecutive_high / max(1, self.min_high))
        if self.state is CognitiveState.RECOVERING:
            return min(1.0, 1.0 - (self.recovery_steps_remaining / max(1, self.recovery_steps)))
        if self.consecutive_low:
            return min(1.0, self.consecutive_low / max(1, self.min_low))
        return 1.0
