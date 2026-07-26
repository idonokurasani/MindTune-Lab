"""CLM-04B safety controller enforcing the live closed-loop envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mindtune_clm.live_loop.health import LiveClosedLoopHealth
from mindtune_clm.live_loop.latency import LatencyTracker
from mindtune_clm.live_loop.state import LiveClosedLoopState
from mindtune_clm.state import MantraControlState


class SafetyAction(str, Enum):
    """Outcome of a safety evaluation."""

    ALLOW = "allow"
    BASELINE = "baseline"
    FREEZE = "freeze"
    KILL = "kill"


@dataclass
class SafetyController:
    """Deterministic safety envelope for the live closed loop."""

    version: str = "clm04b-safety.v1"
    max_decisions_per_minute: int = 60
    max_switches_per_minute: int = 30
    min_dwell_time_s: float = 0.5
    max_consecutive_degraded: int = 5
    max_consecutive_missing: int = 3
    max_playback_failures: int = 5
    max_cache_failures: int = 5
    max_pending_commands: int = 3
    max_frame_to_render_ms: float = 200.0
    max_render_to_playback_ms: float = 50.0
    kill_after_consecutive_missing: int = 10

    _frozen: bool = field(default=False, repr=False)
    _force_baseline: bool = field(default=False, repr=False)
    _running: bool = field(default=False, repr=False)

    def start(self) -> None:
        self._running = True

    def pause(self) -> None:
        self._running = False

    def resume(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def kill(self) -> None:
        self._running = False

    def freeze_policy(self) -> None:
        self._frozen = True

    def unfreeze_policy(self) -> None:
        self._frozen = False

    def force_baseline(self) -> None:
        self._force_baseline = True

    def release_force_baseline(self) -> None:
        self._force_baseline = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def force_baseline_active(self) -> bool:
        return self._force_baseline

    @property
    def running(self) -> bool:
        return self._running

    def evaluate(  # noqa: C901
        self,
        timestamp: float,
        proposed_state: MantraControlState,
        current_state: MantraControlState,
        state: LiveClosedLoopState,
        health: LiveClosedLoopHealth,
        latency: LatencyTracker,
        *,
        latency_key: str,
        missing_window: bool = False,
        degraded_window: bool = False,
    ) -> tuple[MantraControlState, SafetyAction, list[str], bool]:
        """Evaluate a proposed control state against the safety envelope.

        Returns (applied_state, action, reason_codes, should_stop).
        """
        reasons: list[str] = []

        if not self._running:
            reasons.append("safety_not_running")
            return MantraControlState.baseline(), SafetyAction.FREEZE, reasons, False

        if missing_window:
            state.consecutive_missing += 1
            reasons.append(f"consecutive_missing_windows:{state.consecutive_missing}")
        else:
            state.consecutive_missing = 0

        if degraded_window:
            state.consecutive_degraded += 1
            reasons.append(f"consecutive_degraded_windows:{state.consecutive_degraded}")
        else:
            state.consecutive_degraded = 0

        # Latency envelope.
        latency_ok, latency_reasons = latency.check(latency_key)
        if not latency_ok:
            reasons.extend(latency_reasons)

        # Decision-rate and switch-rate envelopes.
        window_start = timestamp - 60.0
        recent_decisions = [t for t, _ in state.decision_history if t > window_start]
        recent_switches = [t for t, _, _ in state.switch_history if t > window_start]
        if len(recent_decisions) >= self.max_decisions_per_minute:
            reasons.append(f"max_decisions_per_minute:{len(recent_decisions)}")
        if len(recent_switches) >= self.max_switches_per_minute:
            reasons.append(f"max_switches_per_minute:{len(recent_switches)}")

        # Dwell time: if the proposed state differs from current, enforce min dwell.
        is_switch = not _states_equivalent(proposed_state, current_state)
        if is_switch and (timestamp - state.last_switch_timestamp) < self.min_dwell_time_s:
            reasons.append(
                f"dwell_time_not_met:{timestamp - state.last_switch_timestamp:.3f}s"
            )

        # Pending-command, playback, and cache failure envelopes.
        if state.pending_commands > self.max_pending_commands:
            reasons.append(f"max_pending_commands:{state.pending_commands}")
        if health.playback_failures > self.max_playback_failures:
            reasons.append(f"max_playback_failures:{health.playback_failures}")
        if health.cache_misses > self.max_cache_failures:
            reasons.append(f"max_cache_failures:{health.cache_misses}")

        # Consecutive missing windows beyond kill threshold is a hard stop condition.
        should_stop = False
        if state.consecutive_missing >= self.kill_after_consecutive_missing:
            reasons.append("sensor_loss_kill_threshold")
            should_stop = True

        if self._force_baseline:
            reasons.append("force_baseline_active")
            return MantraControlState.baseline(), SafetyAction.BASELINE, reasons, should_stop

        if self._frozen:
            reasons.append("policy_frozen")
            return current_state, SafetyAction.FREEZE, reasons, should_stop

        if reasons:
            return MantraControlState.baseline(), SafetyAction.BASELINE, reasons, should_stop

        return proposed_state, SafetyAction.ALLOW, reasons, should_stop

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "max_decisions_per_minute": self.max_decisions_per_minute,
            "max_switches_per_minute": self.max_switches_per_minute,
            "min_dwell_time_s": self.min_dwell_time_s,
            "max_consecutive_degraded": self.max_consecutive_degraded,
            "max_consecutive_missing": self.max_consecutive_missing,
            "max_playback_failures": self.max_playback_failures,
            "max_cache_failures": self.max_cache_failures,
            "max_pending_commands": self.max_pending_commands,
            "max_frame_to_render_ms": self.max_frame_to_render_ms,
            "max_render_to_playback_ms": self.max_render_to_playback_ms,
            "frozen": self._frozen,
            "force_baseline": self._force_baseline,
        }


def _states_equivalent(a: MantraControlState, b: MantraControlState) -> bool:
    """Approximate equality for control-state values."""
    return (
        a.tempo_ratio == b.tempo_ratio
        and a.post_stimulus_pause_ms == b.post_stimulus_pause_ms
        and a.repetition_count == b.repetition_count
        and a.prosodic_emphasis == b.prosodic_emphasis
        and a.vocal_energy == b.vocal_energy
        and a.breathing_cue == b.breathing_cue
        and a.assistance_level == b.assistance_level
    )
