"""Typed adaptation decision and a behavioral-authoritative policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.enums import AdaptationDecision as AdaptationDecisionEnum
from mpe.enums import CognitiveState, DeploymentStatus
from mpe.protocol.cognitive_state import CognitiveStateEstimator, CognitiveStateUpdate


@dataclass(frozen=True)
class AdaptationDecision:
    """Typed adaptation decision compatible with MPE_ADAPTATION_CONTRACT.md."""

    adaptation_decision_id: str
    session_id: str
    policy_id: str
    policy_version: str
    deployment_status: str
    target_dimension: str
    current_value: float
    proposed_value: float
    source_event_ids: list[str]
    aggregation_window: int
    minimum_evidence: bool
    uncertainty_threshold: bool
    confidence: float
    cooldown: int
    hysteresis: float
    maximum_step_size: float
    rollback_rule: str
    abstention_rule: str
    decision: str
    reason: str
    prior_state: str
    resulting_state: str
    eeg_ignored: bool
    applied_at: float | None = None

    def as_payload(self) -> dict[str, Any]:
        """Return the event payload for this decision."""
        payload: dict[str, Any] = {
            "adaptation_decision_id": self.adaptation_decision_id,
            "session_id": self.session_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "deployment_status": self.deployment_status,
            "target_dimension": self.target_dimension,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "source_event_ids": list(self.source_event_ids),
            "aggregation_window": self.aggregation_window,
            "minimum_evidence": self.minimum_evidence,
            "uncertainty_threshold": self.uncertainty_threshold,
            "confidence": self.confidence,
            "cooldown": self.cooldown,
            "hysteresis": self.hysteresis,
            "maximum_step_size": self.maximum_step_size,
            "rollback_rule": self.rollback_rule,
            "abstention_rule": self.abstention_rule,
            "decision": self.decision,
            "reason": self.reason,
            "prior_state": self.prior_state,
            "resulting_state": self.resulting_state,
            "eeg_ignored": self.eeg_ignored,
        }
        if self.applied_at is not None:
            payload["applied_at"] = self.applied_at
        return payload


@dataclass
class AdaptationPolicy:
    """Map a cognitive-state estimate to a bounded, typed adaptation decision.

    The policy currently adapts ``response_deadline`` (the actual next-trial
    runtime parameter).  Changes are rate-limited by ``deadline_step`` and clamped
    between ``baseline_deadline`` and ``max_deadline``, which enforces the
    ``maximum_step_size`` and bounded-drift requirements.
    """

    baseline_deadline: float = 10.0
    max_response_deadline: float = 20.0
    deadline_step: float = 0.5
    latency_bound: float = 2.0
    repeat_cap: int = 1
    policy_id: str = "cognitive_load_response_deadline"
    policy_version: str = "1.0.0"
    deployment_status: str = field(default=DeploymentStatus.SHADOW_MODE.value)
    hysteresis: float = 0.1
    rollback_rule: str = "return_to_baseline_on_sustained_recovery"
    abstention_rule: str = "low_quality_eeg_or_insufficient_behavioral_evidence"

    def decide(
        self,
        estimator: CognitiveStateEstimator,
        update: CognitiveStateUpdate,
        current_deadline: float,
        source_event_ids: list[str],
        clock_now: float,
        session_id: str,
    ) -> tuple[AdaptationDecision, float]:
        """Return a typed adaptation decision and the bounded next deadline."""
        target = self._target_deadline(update.state)
        proposed = self._step(current_deadline, target)

        if (
            update.state in (CognitiveState.STABLE, CognitiveState.POSSIBLE_DRIFT)
            and abs(proposed - current_deadline) <= self.hysteresis
        ):
            decision_value = AdaptationDecisionEnum.NO_CHANGE_INSUFFICIENT_EVIDENCE.value
            applied = None
            next_deadline = current_deadline
        else:
            decision_value = AdaptationDecisionEnum.APPLY.value
            applied = clock_now
            next_deadline = proposed

        confidence = self._confidence(update, estimator)
        minimum_evidence = (
            update.consecutive_high >= estimator.min_high
            or update.consecutive_low >= estimator.min_low
            or update.state in (CognitiveState.RECOVERING, CognitiveState.RECOVERY_REQUIRED)
        )

        decision = AdaptationDecision(
            adaptation_decision_id=f"adaptation-{session_id}-{clock_now}",
            session_id=session_id,
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            deployment_status=self.deployment_status,
            target_dimension="response_deadline",
            current_value=round(current_deadline, 3),
            proposed_value=round(next_deadline, 3),
            source_event_ids=list(source_event_ids),
            aggregation_window=estimator.min_high + estimator.min_low + estimator.recovery_steps,
            minimum_evidence=minimum_evidence,
            uncertainty_threshold=not update.eeg_ignored,
            confidence=round(confidence, 3),
            cooldown=0,
            hysteresis=self.hysteresis,
            maximum_step_size=self.deadline_step,
            rollback_rule=self.rollback_rule,
            abstention_rule=self.abstention_rule,
            decision=decision_value,
            reason=update.reason,
            prior_state=update.prior_state.value,
            resulting_state=update.state.value,
            eeg_ignored=update.eeg_ignored,
            applied_at=round(applied, 3) if applied is not None else None,
        )
        return decision, next_deadline

    def _target_deadline(self, state: CognitiveState) -> float:
        if state is CognitiveState.RECOVERY_REQUIRED:
            return self.max_response_deadline
        # POSSIBLE_DRIFT, RECOVERING, and STABLE all target the baseline deadline;
        # the step size enforces gradual restoration instead of an immediate jump.
        return self.baseline_deadline

    def _step(self, current: float, target: float) -> float:
        if target > current:
            return min(target, current + self.deadline_step)
        if target < current:
            return max(target, current - self.deadline_step)
        return current

    def _confidence(self, update: CognitiveStateUpdate, estimator: CognitiveStateEstimator) -> float:
        if update.state is CognitiveState.RECOVERY_REQUIRED:
            return min(1.0, update.consecutive_high / max(1, estimator.min_high))
        if update.state is CognitiveState.RECOVERING:
            return min(1.0, 1.0 - (update.recovery_steps_remaining / max(1, estimator.recovery_steps)))
        if update.consecutive_low:
            return min(1.0, update.consecutive_low / max(1, estimator.min_low))
        return 1.0
