"""CLM-04B live control pipeline adapter over CLM-01 components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.actuator import ActuationReceipt, MantraActuator
from mindtune_clm.decision import ControlDecision
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.policy import ControlPolicy
from mindtune_clm.state import CognitiveStateEstimate, MantraControlState, StateEstimator


@dataclass
class LiveControlPipeline:
    """Reusable control pipeline: estimate -> decide -> actuate."""

    estimator: StateEstimator = field(default_factory=StateEstimator)
    policy: ControlPolicy = field(default_factory=ControlPolicy)
    actuator: MantraActuator = field(default_factory=MantraActuator)

    def process(
        self,
        frame: ObservationFrame,
        timestamp: float,
        *,
        decision_id: str | None = None,
        command_id: str | None = None,
        override_state: MantraControlState | None = None,
    ) -> tuple[CognitiveStateEstimate, ControlDecision, ActuationReceipt]:
        """Run one control cycle, optionally overriding the proposed state."""
        if decision_id is None:
            decision_id = f"decision-{frame.control_cycle_id}"
        estimate = self.estimator.estimate(frame)
        decision = self.policy.decide(
            estimate,
            self.actuator.current_state,
            timestamp,
            decision_id,
        )
        if override_state is not None:
            decision = self._with_state(decision, override_state)
        receipt = self.actuator.apply(decision, timestamp, command_id)
        return estimate, decision, receipt

    def _with_state(self, decision: ControlDecision, state: MantraControlState) -> ControlDecision:
        from dataclasses import replace
        return replace(decision, proposed_control_state=state)

    def as_dict(self) -> dict[str, Any]:
        return {
            "estimator": self.estimator.__class__.__name__,
            "policy": self.policy.__class__.__name__,
            "actuator": self.actuator.__class__.__name__,
        }
