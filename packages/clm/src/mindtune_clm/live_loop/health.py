"""CLM-04B live closed-loop health state and transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LiveClosedLoopHealthStatus(str, Enum):
    """Discrete health states for the live closed-loop orchestrator."""

    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    PAUSED = "paused"
    STOPPED = "stopped"
    KILLED = "killed"
    ERROR = "error"


@dataclass
class LiveClosedLoopHealth:
    """Mutable-in-place health summary with immutable transition semantics."""

    health_id: str
    status: LiveClosedLoopHealthStatus = LiveClosedLoopHealthStatus.UNKNOWN
    running: bool = False
    paused: bool = False
    killed: bool = False
    frame_count: int = 0
    decision_count: int = 0
    render_count: int = 0
    playback_count: int = 0
    safety_violations: int = 0
    baseline_fallback_count: int = 0
    cache_misses: int = 0
    render_failures: int = 0
    playback_failures: int = 0
    latency_violations: int = 0
    policy_frozen: bool = False
    forced_baseline: bool = False
    last_error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def transition(
        self, status: LiveClosedLoopHealthStatus, *, error: str | None = None
    ) -> "LiveClosedLoopHealth":
        """Return a new health snapshot reflecting the requested transition."""
        new = LiveClosedLoopHealth(
            health_id=self.health_id,
            status=status,
            running=self.running,
            paused=self.paused,
            killed=self.killed,
            frame_count=self.frame_count,
            decision_count=self.decision_count,
            render_count=self.render_count,
            playback_count=self.playback_count,
            safety_violations=self.safety_violations,
            baseline_fallback_count=self.baseline_fallback_count,
            cache_misses=self.cache_misses,
            render_failures=self.render_failures,
            playback_failures=self.playback_failures,
            latency_violations=self.latency_violations,
            policy_frozen=self.policy_frozen,
            forced_baseline=self.forced_baseline,
            last_error=error if error is not None else self.last_error,
            warnings=list(self.warnings),
        )
        if status == LiveClosedLoopHealthStatus.HEALTHY:
            new.running = True
            new.paused = False
            new.killed = False
        elif status in {
            LiveClosedLoopHealthStatus.STOPPED,
            LiveClosedLoopHealthStatus.ERROR,
        }:
            new.running = False
            new.paused = False
        elif status == LiveClosedLoopHealthStatus.PAUSED:
            new.running = False
            new.paused = True
        elif status == LiveClosedLoopHealthStatus.KILLED:
            new.running = False
            new.killed = True
            new.paused = False
        return new

    def with_counters(
        self,
        *,
        frame_count: int = 0,
        decision_count: int = 0,
        render_count: int = 0,
        playback_count: int = 0,
        safety_violations: int = 0,
        baseline_fallback_count: int = 0,
        cache_misses: int = 0,
        render_failures: int = 0,
        playback_failures: int = 0,
        latency_violations: int = 0,
    ) -> "LiveClosedLoopHealth":
        """Return a new health object with adjusted counters."""
        new = LiveClosedLoopHealth(
            health_id=self.health_id,
            status=self.status,
            running=self.running,
            paused=self.paused,
            killed=self.killed,
            frame_count=self.frame_count + frame_count,
            decision_count=self.decision_count + decision_count,
            render_count=self.render_count + render_count,
            playback_count=self.playback_count + playback_count,
            safety_violations=self.safety_violations + safety_violations,
            baseline_fallback_count=self.baseline_fallback_count + baseline_fallback_count,
            cache_misses=self.cache_misses + cache_misses,
            render_failures=self.render_failures + render_failures,
            playback_failures=self.playback_failures + playback_failures,
            latency_violations=self.latency_violations + latency_violations,
            policy_frozen=self.policy_frozen,
            forced_baseline=self.forced_baseline,
            last_error=self.last_error,
            warnings=list(self.warnings),
        )
        return new

    def with_warning(self, message: str) -> "LiveClosedLoopHealth":
        """Return a new health object with an additional warning."""
        new = LiveClosedLoopHealth(
            health_id=self.health_id,
            status=self.status,
            running=self.running,
            paused=self.paused,
            killed=self.killed,
            frame_count=self.frame_count,
            decision_count=self.decision_count,
            render_count=self.render_count,
            playback_count=self.playback_count,
            safety_violations=self.safety_violations,
            baseline_fallback_count=self.baseline_fallback_count,
            cache_misses=self.cache_misses,
            render_failures=self.render_failures,
            playback_failures=self.playback_failures,
            latency_violations=self.latency_violations,
            policy_frozen=self.policy_frozen,
            forced_baseline=self.forced_baseline,
            last_error=self.last_error,
            warnings=list(self.warnings) + [message],
        )
        return new

    def with_error(self, error: str) -> "LiveClosedLoopHealth":
        """Return a new health object with an error message."""
        new = self.with_warning(error)
        new.last_error = error
        return new

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable dictionary."""
        return {
            "health_id": self.health_id,
            "status": self.status.value,
            "running": self.running,
            "paused": self.paused,
            "killed": self.killed,
            "frame_count": self.frame_count,
            "decision_count": self.decision_count,
            "render_count": self.render_count,
            "playback_count": self.playback_count,
            "safety_violations": self.safety_violations,
            "baseline_fallback_count": self.baseline_fallback_count,
            "cache_misses": self.cache_misses,
            "render_failures": self.render_failures,
            "playback_failures": self.playback_failures,
            "latency_violations": self.latency_violations,
            "policy_frozen": self.policy_frozen,
            "forced_baseline": self.forced_baseline,
            "last_error": self.last_error,
            "warnings": list(self.warnings),
        }
