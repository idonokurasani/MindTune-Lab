"""Phase 2 adaptation command boundary — Phase 1 validation only."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AdaptationCommand(str, Enum):
    """Bounded adaptation commands that Phase 2 may submit."""

    EXTEND_NEXT_PAUSE = "extend_next_pause"
    REDUCE_NEXT_PAUSE = "reduce_next_pause"
    REPEAT_CURRENT_FORM = "repeat_current_form"
    REPEAT_CURRENT_GROUP = "repeat_current_group"
    HOLD_PROGRESSION = "hold_progression"
    RESUME_PROGRESSION = "resume_progression"
    REDUCE_NEW_MATERIAL_RATE = "reduce_new_material_rate"
    RESTORE_BASELINE_CADENCE = "restore_baseline_cadence"


@dataclass(frozen=True)
class AdaptationRecord:
    """An append-only adaptation decision record."""

    session_id: str
    mantra_id: str
    timeline_version: str
    current_segment_id: str
    command: str
    delta: dict[str, Any]
    reason: str
    policy_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mantra_id": self.mantra_id,
            "timeline_version": self.timeline_version,
            "current_segment_id": self.current_segment_id,
            "command": self.command,
            "delta": self.delta,
            "reason": self.reason,
            "policy_version": self.policy_version,
        }


class AdaptationError(Exception):
    """Raised when an adaptation command is unsupported or out-of-bounds."""


class AdaptationBoundary:
    """Validate bounded Phase 2 adaptation commands without mutating events."""

    def __init__(
        self,
        max_pause_extension_ms: int = 2000,
        max_repeat_count: int = 3,
        min_material_rate: float = 0.5,
        max_material_rate: float = 1.0,
    ):
        self.max_pause_extension_ms = max_pause_extension_ms
        self.max_repeat_count = max_repeat_count
        self.min_material_rate = min_material_rate
        self.max_material_rate = max_material_rate

    def apply(
        self,
        session_id: str,
        mantra_id: str,
        timeline_version: str,
        current_segment_id: str,
        command: str,
        delta: dict[str, Any],
        reason: str,
        policy_version: str,
    ) -> AdaptationRecord:
        """Validate and record an adaptation command."""
        try:
            AdaptationCommand(command)
        except ValueError as exc:
            raise AdaptationError(f"Unsupported adaptation command: {command!r}") from exc

        if command in (AdaptationCommand.EXTEND_NEXT_PAUSE, AdaptationCommand.REDUCE_NEXT_PAUSE):
            delta_ms = delta.get("delta_ms", 0)
            if not isinstance(delta_ms, (int, float)):
                raise AdaptationError(f"delta_ms must be numeric, got {type(delta_ms)}")
            if abs(delta_ms) > self.max_pause_extension_ms:
                raise AdaptationError(
                    f"Pause delta {delta_ms}ms exceeds bound {self.max_pause_extension_ms}ms"
                )

        if command in (AdaptationCommand.REPEAT_CURRENT_FORM, AdaptationCommand.REPEAT_CURRENT_GROUP):
            count = delta.get("count", 1)
            if not isinstance(count, int) or count < 1 or count > self.max_repeat_count:
                raise AdaptationError(
                    f"Repeat count {count} out of bounds [1, {self.max_repeat_count}]"
                )

        if command == AdaptationCommand.REDUCE_NEW_MATERIAL_RATE:
            rate = delta.get("rate", 1.0)
            if not isinstance(rate, (int, float)):
                raise AdaptationError(f"rate must be numeric, got {type(rate)}")
            if rate < self.min_material_rate or rate > self.max_material_rate:
                raise AdaptationError(
                    f"Material rate {rate} out of bounds [{self.min_material_rate}, {self.max_material_rate}]"
                )

        return AdaptationRecord(
            session_id=session_id,
            mantra_id=mantra_id,
            timeline_version=timeline_version,
            current_segment_id=current_segment_id,
            command=command,
            delta=delta,
            reason=reason,
            policy_version=policy_version,
        )
