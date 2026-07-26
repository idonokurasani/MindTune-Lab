"""Canonical CLM-01 event type constants and payload helpers."""

from __future__ import annotations


class CLM01EventType:
    """Event type names for the CLM-01 closed-loop mantra control slice."""

    OBSERVATION_FRAME_CREATED = "observation_frame_created"
    COGNITIVE_STATE_ESTIMATED = "cognitive_state_estimated"
    CONTROL_DECISION_MADE = "control_decision_made"
    ACTUATION_REQUESTED = "actuation_requested"
    ACTUATION_APPLIED = "actuation_applied"
    ADAPTED_STIMULUS_RENDERED = "adapted_stimulus_rendered"
    INTERVENTION_OUTCOME_EVALUATED = "intervention_outcome_evaluated"

    @classmethod
    def all(cls) -> frozenset[str]:
        return frozenset(
            [
                cls.OBSERVATION_FRAME_CREATED,
                cls.COGNITIVE_STATE_ESTIMATED,
                cls.CONTROL_DECISION_MADE,
                cls.ACTUATION_REQUESTED,
                cls.ACTUATION_APPLIED,
                cls.ADAPTED_STIMULUS_RENDERED,
                cls.INTERVENTION_OUTCOME_EVALUATED,
            ]
        )
