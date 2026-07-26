"""CLM-04B live closed-loop MPE event type constants."""

from __future__ import annotations

from enum import Enum


class LiveClosedLoopEventType(str, Enum):
    """MPE-registered live closed-loop events for CLM-04B.

    Each string is also registered in ``mpe.events.SUPPORTED_EVENT_TYPES``.
    """

    ORCHESTRATOR_STARTED = "live_closed_loop_started"
    ORCHESTRATOR_COMPLETED = "live_closed_loop_completed"
    ORCHESTRATOR_PAUSED = "live_closed_loop_paused"
    ORCHESTRATOR_RESUMED = "live_closed_loop_resumed"
    ORCHESTRATOR_STOPPED = "live_closed_loop_stopped"
    ORCHESTRATOR_KILLED = "live_closed_loop_killed"

    OBSERVATION_FRAME_CONSUMED = "live_closed_loop_observation_frame_consumed"
    CONTROL_DECISION_MADE = "live_closed_loop_control_decision_made"
    ACTUATION_APPLIED = "live_closed_loop_actuation_applied"
    SAFETY_ENVELOPE_VIOLATED = "live_closed_loop_safety_envelope_violated"
    BASELINE_FALLBACK_ACTIVATED = "live_closed_loop_baseline_fallback_activated"
    BASELINE_FALLBACK_RELEASED = "live_closed_loop_baseline_fallback_released"
    POLICY_FROZEN = "live_closed_loop_policy_frozen"
    POLICY_UNFROZEN = "live_closed_loop_policy_unfrozen"
    RENDER_FAILED = "live_closed_loop_render_failed"
    PLAYBACK_FAILED = "live_closed_loop_playback_failed"
    CACHE_MISS = "live_closed_loop_cache_miss"
    LATENCY_EXCEEDED = "live_closed_loop_latency_exceeded"
    HEALTH_CHANGED = "live_closed_loop_health_changed"
    INTERVENTION_OUTCOME = "live_closed_loop_intervention_outcome"

    @classmethod
    def all(cls) -> frozenset[str]:
        """Return all CLM-04B event type strings."""
        return frozenset(member.value for member in cls)
