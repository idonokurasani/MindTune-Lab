"""Collect accepted/rejected observations for a calibration session."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.calibration.models import (
    CalibrationBlock,
    CalibrationSession,
    QualitySummary,
    RawObservation,
)
from mindtune_clm.calibration.protocol import CalibrationProtocol
from mindtune_clm.calibration.quality import ObservationQualityGate


@dataclass
class CalibrationCollector:
    """Aggregates accepted, rejected, and missing observations per block."""

    protocol: CalibrationProtocol
    gate: ObservationQualityGate = field(default_factory=ObservationQualityGate)
    all_observations: list[RawObservation] = field(default_factory=list)
    accepted: list[RawObservation] = field(default_factory=list)
    rejected: list[RawObservation] = field(default_factory=list)
    missing_count: int = 0
    missing_reasons: list[str] = field(default_factory=list)
    feature_values: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    block_id: str = "default"

    def accept(self, observation: RawObservation) -> None:
        self.all_observations.append(observation)
        self.accepted.append(observation)
        try:
            self.feature_values[observation.feature_name].append(float(observation.value))
        except (TypeError, ValueError):
            pass

    def reject(self, observation: RawObservation, reason: str) -> None:
        if not observation.reason_codes:
            object.__setattr__(observation, "reason_codes", [reason])
        self.all_observations.append(observation)
        self.rejected.append(observation)

    def missing(self, reason: str = "missing_observation") -> None:
        self.missing_count += 1
        self.missing_reasons.append(reason)

    def collect(self, observation: RawObservation) -> bool:
        """Apply the quality gate and record accepted or rejected."""
        result = self.gate.evaluate(observation)
        if result.accepted:
            self.accept(observation)
            return True
        self.reject(observation, result.reason_codes[0])
        return False

    def quality_summary(self) -> QualitySummary:
        total = len(self.accepted) + len(self.rejected) + self.missing_count
        artifact_rate = 0.0
        movement_rate = 0.0
        if total > 0:
            artifact_rate = sum(1 for o in self.rejected if "artifact" in o.reason_codes) / total
            movement_rate = sum(1 for o in self.rejected if "movement" in o.reason_codes) / total
        reasons: dict[str, int] = {}
        for o in self.rejected:
            for code in o.reason_codes:
                reasons[code] = reasons.get(code, 0) + 1
        for r in self.missing_reasons:
            reasons[r] = reasons.get(r, 0) + 1
        return QualitySummary(
            accepted_count=len(self.accepted),
            rejected_count=len(self.rejected),
            missing_count=self.missing_count,
            artifact_rate=artifact_rate,
            movement_contamination_rate=movement_rate,
            reason_distribution=reasons,
        )

    def feature_summary(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "accepted": len(values),
                "missing": self.missing_count,
            }
            for name, values in self.feature_values.items()
        }


class SessionCollector:
    """Manage per-block collectors for a CalibrationSession."""

    def __init__(self, session: CalibrationSession) -> None:
        self.session = session
        self.block_collectors: dict[str, CalibrationCollector] = {}
        if session.protocol is None:
            from mindtune_clm.calibration.protocol import CalibrationProtocol
            session.protocol = CalibrationProtocol.default()
        assert session.protocol is not None
        self.protocol = session.protocol
        self._current_block_id: str | None = None

    def start_block(self, block: CalibrationBlock) -> None:
        self.session.blocks.append(block)
        self.session.current_block = block
        self._current_block_id = block.block_id
        self.block_collectors[block.block_id] = CalibrationCollector(
            protocol=self.protocol, block_id=block.block_id
        )

    def current_collector(self) -> CalibrationCollector | None:
        if self._current_block_id is None:
            return None
        return self.block_collectors.get(self._current_block_id)

    def collect(self, observation: RawObservation) -> bool:
        collector = self.current_collector()
        if collector is None:
            self.start_block(
                CalibrationBlock(
                    block_id=f"auto-{len(self.session.blocks)}",
                    block_type="unspecified",
                    target_duration_seconds=0.0,
                )
            )
            collector = self.current_collector()
        assert collector is not None
        accepted = collector.collect(observation)
        self.session.collected_observations.append(observation)
        return accepted

    def missing(self, reason: str = "missing_observation") -> None:
        collector = self.current_collector()
        if collector is not None:
            collector.missing(reason)

    def reject(self, observation: RawObservation, reason: str) -> None:
        collector = self.current_collector()
        if collector is not None:
            collector.reject(observation, reason)

    def overall_summary(self) -> dict[str, Any]:
        accepted = 0
        rejected = 0
        missing = 0
        for coll in self.block_collectors.values():
            q = coll.quality_summary()
            accepted += q.accepted_count
            rejected += q.rejected_count
            missing += q.missing_count
        return {
            "accepted": accepted,
            "rejected": rejected,
            "missing": missing,
            "block_count": len(self.block_collectors),
        }
