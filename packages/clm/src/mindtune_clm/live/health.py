"""Gateway health state and deterministic transitions for CLM-04."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LiveHealthStatus(str, Enum):
    """Discrete health states for the live sensor gateway."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LiveGatewayHealth:
    """Mutable-in-place health summary with immutable transition semantics.

    Each call to ``transition`` returns a new health snapshot while the
    gateway is free to track counters in place for performance.
    """

    health_id: str
    status: LiveHealthStatus = LiveHealthStatus.DISCONNECTED
    connected: bool = False
    paused: bool = False
    epoch: int = 0
    reconnect_attempts: int = 0
    reconnect_exhausted: bool = False
    packets_received: int = 0
    packets_late: int = 0
    packets_duplicate: int = 0
    buffer_overflows: int = 0
    last_error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def transition(
        self,
        status: LiveHealthStatus,
        *,
        error: str | None = None,
    ) -> "LiveGatewayHealth":
        """Return a new health object reflecting the requested transition."""
        new = LiveGatewayHealth(
            health_id=self.health_id,
            status=status,
            connected=self.connected,
            paused=self.paused,
            epoch=self.epoch,
            reconnect_attempts=self.reconnect_attempts,
            reconnect_exhausted=self.reconnect_exhausted,
            packets_received=self.packets_received,
            packets_late=self.packets_late,
            packets_duplicate=self.packets_duplicate,
            buffer_overflows=self.buffer_overflows,
            last_error=error if error is not None else self.last_error,
            warnings=list(self.warnings),
        )

        if status == LiveHealthStatus.CONNECTED:
            new.connected = True
        elif status in {
            LiveHealthStatus.DISCONNECTED,
            LiveHealthStatus.STOPPED,
            LiveHealthStatus.ERROR,
        }:
            new.connected = False
            new.paused = False

        if status == LiveHealthStatus.PAUSED:
            new.paused = True
        elif status == LiveHealthStatus.RUNNING:
            new.paused = False

        return new

    def with_counters(
        self,
        *,
        packets_received: int = 0,
        packets_late: int = 0,
        packets_duplicate: int = 0,
        buffer_overflows: int = 0,
    ) -> "LiveGatewayHealth":
        """Return a new health object with adjusted counters."""
        new = LiveGatewayHealth(
            health_id=self.health_id,
            status=self.status,
            connected=self.connected,
            paused=self.paused,
            epoch=self.epoch,
            reconnect_attempts=self.reconnect_attempts,
            reconnect_exhausted=self.reconnect_exhausted,
            packets_received=self.packets_received + packets_received,
            packets_late=self.packets_late + packets_late,
            packets_duplicate=self.packets_duplicate + packets_duplicate,
            buffer_overflows=self.buffer_overflows + buffer_overflows,
            last_error=self.last_error,
            warnings=list(self.warnings),
        )
        return new

    def add_warning(self, message: str) -> "LiveGatewayHealth":
        """Return a new health object with an additional warning."""
        new = LiveGatewayHealth(
            health_id=self.health_id,
            status=self.status,
            connected=self.connected,
            paused=self.paused,
            epoch=self.epoch,
            reconnect_attempts=self.reconnect_attempts,
            reconnect_exhausted=self.reconnect_exhausted,
            packets_received=self.packets_received,
            packets_late=self.packets_late,
            packets_duplicate=self.packets_duplicate,
            buffer_overflows=self.buffer_overflows,
            last_error=self.last_error,
            warnings=list(self.warnings) + [message],
        )
        return new
