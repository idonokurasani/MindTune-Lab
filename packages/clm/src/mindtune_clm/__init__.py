"""CLM-01 closed-loop mantra control vertical slice."""

from __future__ import annotations

from mpe.control.actuator import ActuationReceipt, MantraActuator
from mpe.control.decision import ControlDecision, ControlDecisionKind
from mpe.control.events import CLM01EventType
from mpe.control.fixture_clm01 import make_clm01_fixture
from mpe.control.loop import ControlCycleResult, ControlLoop, ControlLoopResult
from mpe.control.observations import ObservationFrame, fuse_observation
from mpe.control.policy import ControlPolicy
from mpe.control.state import CognitiveStateEstimate, MantraControlState, StateEstimator

__all__ = [
    "ActuationReceipt",
    "MantraActuator",
    "ControlDecision",
    "ControlDecisionKind",
    "CLM01EventType",
    "make_clm01_fixture",
    "ControlCycleResult",
    "ControlLoop",
    "ControlLoopResult",
    "ObservationFrame",
    "fuse_observation",
    "ControlPolicy",
    "CognitiveStateEstimate",
    "MantraControlState",
    "StateEstimator",
]
