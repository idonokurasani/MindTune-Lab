"""Progressive control policy that maps cognitive-state estimates to mantra decisions."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mindtune_clm.decision import ControlDecision, ControlDecisionKind
from mindtune_clm.state import CognitiveStateEstimate, MantraControlState
from mpe.enums import CognitiveState


def _states_close(a: MantraControlState, b: MantraControlState) -> bool:
    """Approximate equality for control-state value fields."""
    return (
        math.isclose(a.tempo_ratio, b.tempo_ratio, rel_tol=1e-6)
        and a.pre_stimulus_pause_ms == b.pre_stimulus_pause_ms
        and a.post_stimulus_pause_ms == b.post_stimulus_pause_ms
        and a.repetition_count == b.repetition_count
        and math.isclose(a.prosodic_emphasis, b.prosodic_emphasis, rel_tol=1e-6)
        and math.isclose(a.vocal_energy, b.vocal_energy, rel_tol=1e-6)
        and a.breathing_cue == b.breathing_cue
        and math.isclose(a.assistance_level, b.assistance_level, rel_tol=1e-6)
    )


def _move(current: float, target: float, step: float) -> float:
    """Move current one bounded step toward target."""
    if target > current:
        return min(target, current + step)
    if target < current:
        return max(target, current - step)
    return current


@dataclass
class ControlPolicy:
    """Deterministic progressive hysteresis policy for mantra control parameters.

    The policy applies a *first intervention* that changes at most four
    dimensions by bounded deltas. Sustained recovery-required cycles trigger
    an *escalation* stage that may introduce additional dimensions. Recovery
    withdraws assistance at a rate that is at most the escalation rate.
    """

    baseline: MantraControlState = field(default_factory=MantraControlState.baseline)
    first_intervention: MantraControlState = field(
        default_factory=lambda: MantraControlState(
            tempo_ratio=0.95,
            post_stimulus_pause_ms=300,
            prosodic_emphasis=0.1,
            assistance_level=0.2,
            control_state_id="first_intervention",
        )
    )
    escalation: MantraControlState = field(
        default_factory=lambda: MantraControlState(
            tempo_ratio=0.8,
            post_stimulus_pause_ms=800,
            prosodic_emphasis=0.3,
            assistance_level=0.6,
            vocal_energy=0.3,
            breathing_cue=True,
            repetition_count=2,
            control_state_id="escalation",
        )
    )

    # Safety limits per decision.
    max_tempo_delta: float = 0.05
    max_post_delta_ms: int = 300
    max_prosodic_delta: float = 0.1
    max_assistance_delta: float = 0.2
    max_vocal_delta: float = 0.3
    max_repetition_delta: int = 1
    max_total_assistance: float = 1.0
    max_dimensions_first_intervention: int = 4
    min_cycles_before_escalation: int = 3
    withdrawal_rate: float = 0.5

    safe_application_boundary: str = "between_mantra_cycles"

    intervention_cycle_count: int = 0

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
            self.intervention_cycle_count += 1
            if _states_close(previous, self.baseline):
                kind = ControlDecisionKind.APPLY
                target = self.first_intervention
            elif _states_close(previous, self.first_intervention):
                if self.intervention_cycle_count >= self.min_cycles_before_escalation:
                    kind = ControlDecisionKind.APPLY
                    target = self.escalation
                else:
                    kind = ControlDecisionKind.MAINTAIN
                    target = previous
            elif _states_close(previous, self.escalation):
                kind = ControlDecisionKind.MAINTAIN
                target = previous
            else:
                # Intermediate state (between first and escalation): continue escalation.
                kind = ControlDecisionKind.APPLY
                target = self.escalation
        elif state is CognitiveState.RECOVERING:
            self.intervention_cycle_count = 0
            kind = ControlDecisionKind.MAINTAIN
            target = previous
        elif state is CognitiveState.POSSIBLE_DRIFT:
            self.intervention_cycle_count = 0
            kind = ControlDecisionKind.ABSTAIN
            target = previous
        else:  # STABLE
            self.intervention_cycle_count = 0
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
            estimate_id=estimate.estimate_id,
            source_observation_frame_id=estimate.source_observation_frame_id,
            source_control_cycle_id=estimate.source_control_cycle_id,
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

        is_first_apply = (
            kind is ControlDecisionKind.APPLY
            and _states_close(target, self.first_intervention)
        )

        # Withdrawals move more slowly than interventions.
        rate = self.withdrawal_rate if kind is ControlDecisionKind.WITHDRAW else 1.0

        # Clamp assistance to the maximum total assistance level.
        target_assistance = min(target.assistance_level, self.max_total_assistance)

        if is_first_apply:
            # First intervention changes at most four dimensions; repetition,
            # breathing, and vocal energy are intentionally left unchanged.
            return MantraControlState(
                tempo_ratio=round(
                    _move(current.tempo_ratio, target.tempo_ratio, self.max_tempo_delta * rate), 3
                ),
                pre_stimulus_pause_ms=current.pre_stimulus_pause_ms,
                post_stimulus_pause_ms=int(
                    _move(current.post_stimulus_pause_ms, target.post_stimulus_pause_ms, self.max_post_delta_ms * rate)
                ),
                repetition_count=current.repetition_count,
                prosodic_emphasis=round(
                    _move(current.prosodic_emphasis, target.prosodic_emphasis, self.max_prosodic_delta * rate), 3
                ),
                vocal_energy=current.vocal_energy,
                breathing_cue=current.breathing_cue,
                assistance_level=round(
                    _move(current.assistance_level, target_assistance, self.max_assistance_delta * rate), 3
                ),
            ).clamped()

        # Escalation or withdrawal: all dimensions may move.
        return MantraControlState(
            tempo_ratio=round(
                _move(current.tempo_ratio, target.tempo_ratio, self.max_tempo_delta * rate), 3
            ),
            pre_stimulus_pause_ms=current.pre_stimulus_pause_ms,
            post_stimulus_pause_ms=int(
                _move(current.post_stimulus_pause_ms, target.post_stimulus_pause_ms, self.max_post_delta_ms * rate)
            ),
            repetition_count=int(
                _move(current.repetition_count, target.repetition_count, self.max_repetition_delta * rate)
            ),
            prosodic_emphasis=round(
                _move(current.prosodic_emphasis, target.prosodic_emphasis, self.max_prosodic_delta * rate), 3
            ),
            vocal_energy=round(
                _move(current.vocal_energy, target.vocal_energy, self.max_vocal_delta * rate), 3
            ),
            breathing_cue=target.breathing_cue if current.breathing_cue != target.breathing_cue else current.breathing_cue,
            assistance_level=round(
                _move(current.assistance_level, target_assistance, self.max_assistance_delta * rate), 3
            ),
        ).clamped()
