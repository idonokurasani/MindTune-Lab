"""CLM-05 control-plane command vocabulary."""

from __future__ import annotations

from enum import Enum


class ControlCommand(str, Enum):
    """Allowed control-plane commands."""

    PREPARE = "prepare"
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    KILL = "kill"
    STEP = "step"


class SensorCommand(str, Enum):
    """Allowed sensor commands."""

    CONNECT = "connect"
    DISCONNECT = "disconnect"


class SessionStatus(str, Enum):
    """Session lifecycle status."""

    CREATED = "created"
    PREPARED = "prepared"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"

    @classmethod
    def terminal(cls) -> frozenset[str]:
        return frozenset({cls.COMPLETED, cls.ABORTED, cls.FAILED})
