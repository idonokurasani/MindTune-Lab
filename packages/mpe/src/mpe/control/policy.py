"""Control policy that maps cognitive-state estimates to mantra control decisions."""

from __future__ import annotations

import math
from dataclasses import dataclass

from mpe.control.decision import ControlDecision, ControlDecisionKind
from mpe.control.state import CognitiveStateEstimate, MantraControlState
from mpe.enums import CognitiveState


def _states_close(a: MantraControlState, b: MantraControlState) -> bool:
    """Approximate equality for control-state fields."""
    return (
        math.isclose(a.tempo_ratio, b.tempo_ratio, rel_tol=1e-6)
        and a.pre_stimulus_pause_ms == b.pre_stimulus_pause_ms
        and a.post_stimulus_pause_ms == b.post_stimulus_pause_ms
        and a.repetition_count == b.repetition_count
        and math.isclose(a.prosodic_emphasis, b.prosodic_emphasis, rel_tol=1e-6)
        and math.isclose(a.vocal_energy, b.vocal_energy, rel_tol=1e-6)
        and a.breathing_cue == b.breathing_cue
        and a.assistance_level == b.assistance_level
    )


@dataclass(frozen=True)
class ControlPolicy:
    """Deterministic hysteresis policy for mantra control parameters.

    The policy intervenes gradually when the state is ``RECOVERY_REQUIRED``,
    maintains assistance during ``POSSIBLE_DRIFT`` and initial ``RECOVERING``,
    and withdraws assistance at a rate that is at most the intervention rate
    during sustained recovery (``STABLE`` after an elevated assistance level).
    """

    baseline: MantraControlState = MantraControlState.baseline()
    intervention: MantraControlState = MantraControlState(
        tempo_ratio=0.7,
        pre_stimulus_pause_ms=0,
        post_stimulus_pause_ms=1200,
        repetition_count=2,
        prosodic_emphasis=0.6,
        vocal_energy=0.7,
        breathing_cue=True,
        assistance_level=3,
    )

    # Intervention step sizes per control cycle (full target reached in one apply).
    tempo_intervention_step: float = 0.3
    post_intervention_step_ms: int = 1200
    prosodic_intervention_step: float = 0.6
    vocal_intervention_step: float = 0.2
    assistance_intervention_step: int = 2
    repetition_intervention_step: int = 1

    # Withdrawal step sizes per control cycle; must be <= intervention rates.
    tempo_withdrawal_step: float = 0.02
    post_withdrawal_step_ms: int = 100
    prosodic_withdrawal_step: float = 0.05
    vocal_withdrawal_step: float = 0.05
    assistance_withdrawal_step: int = 1
    repetition_withdrawal_step: int = 1

    safe_application_boundary: str = "between_mantra_cycles"

    def decide(
        self,
        estimate: CognitiveStateEstimate,
        previous: MantraControlState,
        decision_timestamp: float,
        decision_id: str,
    ) -> ControlDecision:
        """Return a deterministic control decision for the current estimate."""
        state = estimate.cognitive_state

        if state is CognitiveState.RECOVERY_REQUIRED:
            if _states_close(previous, self.intervention):
                kind = ControlDecisionKind.MAINTAIN
                target = previous
            else:
                kind = ControlDecisionKind.APPLY
                target = self.intervention
        elif state is CognitiveState.RECOVERING:
            kind = ControlDecisionKind.MAINTAIN
            target = previous
        elif state is CognitiveState.POSSIBLE_DRIFT:
            kind = ControlDecisionKind.ABSTAIN
            target = previous
        else:  # STABLE
            if _states_close(previous, self.baseline):
                kind = ControlDecisionKind.MAINTAIN
                target = self.baseline
            else:
                kind = ControlDecisionKind.WITHDRAW
                target = self.baseline

        proposed = self._step(previous, target, kind)
        reason_codes = [f"state={state.value}", f"decision_kind={kind.value}"] + list(estimate.reason_codes)

        return ControlDecision(
            decision_id=decision_id,
            decision_kind=kind,
            previous_control_state=previous,
            proposed_control_state=proposed,
            evidence=list(estimate.evidence_used) + [f"load={estimate.cognitive_load:.2f}"],
            confidence=round(estimate.confidence, 3),
            reason_codes=reason_codes,
            safe_application_boundary=self.safe_application_boundary,
            decision_timestamp=decision_timestamp,
        )

    def _step(
        self, current: MantraControlState, target: MantraControlState, kind: ControlDecisionKind
    ) -> MantraControlState:
        """Move the current state one bounded step toward the target."""
        if kind in (ControlDecisionKind.MAINTAIN, ControlDecisionKind.ABSTAIN):
            return current

        if kind is ControlDecisionKind.APPLY:
            tempo_step = self.tempo_intervention_step
            post_step = self.post_intervention_step_ms
            prosodic_step = self.prosodic_intervention_step
            vocal_step = self.vocal_intervention_step
            assistance_step = self.assistance_intervention_step
            repetition_step = self.repetition_intervention_step
        else:  # WITHDRAW
            tempo_step = self.tempo_withdrawal_step
            post_step = self.post_withdrawal_step_ms
            prosodic_step = self.prosodic_withdrawal_step
            vocal_step = self.vocal_withdrawal_step
            assistance_step = self.assistance_withdrawal_step
            repetition_step = self.repetition_withdrawal_step

        def move(current_value: float, target_value: float, step: float) -> float:
            if target_value > current_value:
                return min(target_value, current_value + step)
            if target_value < current_value:
                return max(target_value, current_value - step)
            return current_value

        return MantraControlState(
            tempo_ratio=round(move(current.tempo_ratio, target.tempo_ratio, tempo_step), 3),
            pre_stimulus_pause_ms=current.pre_stimulus_pause_ms,
            post_stimulus_pause_ms=int(move(current.post_stimulus_pause_ms, target.post_stimulus_pause_ms, post_step)),
            repetition_count=int(move(current.repetition_count, target.repetition_count, repetition_step)),
            prosodic_emphasis=round(move(current.prosodic_emphasis, target.prosodic_emphasis, prosodic_step), 3),
            vocal_energy=round(move(current.vocal_energy, target.vocal_energy, vocal_step), 3),
            breathing_cue=target.breathing_cue if kind is ControlDecisionKind.APPLY else target.breathing_cue,
            assistance_level=int(move(current.assistance_level, target.assistance_level, assistance_step)),
        ).clamped()
