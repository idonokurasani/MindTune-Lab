"""Closed-loop mantra control orchestrator and fixture runner for CLM-01."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.actuator import ActuationReceipt, MantraActuator
from mindtune_clm.decision import ControlDecision
from mindtune_clm.events import CLM01EventType
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.policy import ControlPolicy
from mindtune_clm.state import CognitiveStateEstimate, MantraControlState, StateEstimator
from mpe.enums import DataClassification
from mpe.event_store import EventStore, InMemoryEventStore
from mpe.events import Event
from mpe.providers import (
    MockDomainNormalizer,
    MockEvaluator,
    MockKeyboardObservationProvider,
    MockRenderer,
    MockResponseInterpreter,
    MockScheduler,
    ProviderSet,
)
from mpe.runtime import Clock, Runtime
from mpe.types import (
    CorrelationID,
    EventID,
    ProgramVersionID,
    ProtocolVersionID,
    RenderedStimulusID,
    SessionID,
    make_id,
)


@dataclass
class ControlCycleResult:
    """Result of one control cycle plus its rendered output."""

    control_cycle_id: str
    render_cycle_id: str
    observation_frame: ObservationFrame
    estimate: CognitiveStateEstimate
    decision: ControlDecision
    receipt: ActuationReceipt
    rendered_event: Event
    rendered_control_state: MantraControlState


@dataclass
class ControlLoopResult:
    """Complete deterministic result of running the CLM-01 fixture."""

    session_id: SessionID
    events: list[Event]
    cycles: list[ControlCycleResult]
    final_control_state: MantraControlState


@dataclass
class ControlLoop:
    """Domain-neutral closed-loop mantra controller.

    Uses the existing MPE ``Runtime`` for event emission and the existing
    ``InMemoryEventStore`` for persistence.  The actuator is in-memory and
    does not generate audio; the rendered stimulus contains the exact control
    parameters that a future audio renderer would receive.

    Execution model:
      - six observation/decision control cycles;
      - one initial baseline render (render_cycle_id = rc-1);
      - one subsequent render after each control cycle (rc-2 ... rc-7);
      - seven rendered mantra cycles in total.
    """

    store: EventStore = field(default_factory=InMemoryEventStore)
    clock: Clock = field(default_factory=Clock)
    estimator: StateEstimator = field(default_factory=StateEstimator)
    policy: ControlPolicy = field(default_factory=ControlPolicy)
    actuator: MantraActuator = field(default_factory=MantraActuator)
    protocol_version_id: ProtocolVersionID = field(default_factory=lambda: ProtocolVersionID("clm-01-v1.0.0"))
    program_version_id: ProgramVersionID = field(default_factory=lambda: ProgramVersionID("clm-01-program-v1.0.0"))
    learner_id: str = "learner_clm01"

    runtime: Runtime = field(init=False)
    session_id: SessionID = field(init=False)

    def __post_init__(self) -> None:
        self.runtime = Runtime(self.store, self._providers(), self.clock)
        self.session_id = SessionID(str(make_id(SessionID)))

    def _providers(self) -> ProviderSet:
        return ProviderSet(
            renderer=MockRenderer(),
            observation=MockKeyboardObservationProvider(),
            interpreter=MockResponseInterpreter(),
            normalizer=MockDomainNormalizer(),
            evaluator=MockEvaluator(),
            scheduler=MockScheduler(),
            eeg=None,
        )

    def run_session(self, frames: list[ObservationFrame]) -> ControlLoopResult:
        """Execute the control loop for every observation frame."""
        self.runtime.create_session(
            program_version_id=self.program_version_id,
            protocol_version_id=self.protocol_version_id,
            learner_id=self.learner_id,
            session_id=self.session_id,
        )
        self.runtime.start_session(
            random_seed="clm01_seed_0",
            start_parameters={"control_loop": "clm-01", "control_cycle_count": len(frames)},
        )

        # Initial baseline render for the first mantra cycle.
        last_event = self.runtime.state.events[-1]
        self._render_stimulus(
            self.actuator.current_state,
            None,
            [last_event.event_id],
            render_cycle_id="rc-1",
        )

        cycles: list[ControlCycleResult] = []
        for cycle_index, frame in enumerate(frames, start=1):
            cycles.append(self._run_cycle(frame, cycle_index))

        events = self.store.read(self.session_id)
        return ControlLoopResult(
            session_id=self.session_id,
            events=events,
            cycles=cycles,
            final_control_state=self.actuator.current_state,
        )

    def _run_cycle(self, frame: ObservationFrame, cycle_index: int) -> ControlCycleResult:
        render_cycle_id = f"rc-{cycle_index + 1}"
        control_cycle_id = frame.control_cycle_id

        obs_event = self._emit_observation(frame)
        estimate = self.estimator.estimate(frame)
        est_event = self._emit_estimate(estimate, [obs_event.event_id])

        timestamp = self.runtime.clock.now()
        decision_id = f"decision-{self.session_id}-{cycle_index}"
        decision = self.policy.decide(
            estimate,
            self.actuator.current_state,
            decision_timestamp=timestamp,
            decision_id=decision_id,
        )
        decision_event = self._emit_decision(decision, [est_event.event_id])

        act_request_event = self._emit_actuation_requested(decision, [decision_event.event_id])
        receipt = self.actuator.apply(
            decision,
            timestamp=self.runtime.clock.now(),
            command_id=f"actuate-{self.session_id}-{cycle_index}",
        )
        act_applied_event = self._emit_actuation_applied(receipt, [act_request_event.event_id])

        rendered = self._render_stimulus(
            receipt.applied_state,
            receipt,
            [act_applied_event.event_id],
            render_cycle_id=render_cycle_id,
        )
        self._emit_intervention_outcome(
            estimate,
            decision,
            receipt,
            rendered,
            [rendered.event_id],
        )

        return ControlCycleResult(
            control_cycle_id=control_cycle_id,
            render_cycle_id=render_cycle_id,
            observation_frame=frame,
            estimate=estimate,
            decision=decision,
            receipt=receipt,
            rendered_event=rendered,
            rendered_control_state=receipt.applied_state,
        )

    def _emit_observation(self, frame: ObservationFrame) -> Event:
        provenance = [self.runtime.state.events[-1].event_id]
        return self.runtime.emit(
            CLM01EventType.OBSERVATION_FRAME_CREATED,
            {
                "observation_frame_id": frame.observation_frame_id,
                "control_cycle_id": frame.control_cycle_id,
                "session_id": frame.session_id,
                "sequence_number": frame.sequence_number,
                "observation_timestamp": frame.observation_timestamp,
                "behavioral_latency_ms": frame.behavioral_latency_ms,
                "hesitation_score": frame.hesitation_score,
                "error_score": frame.error_score,
                "eeg_stability": frame.eeg_stability,
                "eeg_quality": frame.eeg_quality,
                "respiration_stability": frame.respiration_stability,
                "voice_stability": frame.voice_stability,
                "available_modalities": list(frame.available_modalities),
                "source_event_ids": list(frame.source_event_ids),
            },
            component="clm01_control",
            component_version="1.0.0",
            provenance=provenance,
            data_classification=DataClassification.INTERNAL,
        )

    def _emit_estimate(self, estimate: CognitiveStateEstimate, provenance: list[EventID]) -> Event:
        return self.runtime.emit(
            CLM01EventType.COGNITIVE_STATE_ESTIMATED,
            {
                "estimate_id": estimate.estimate_id,
                "source_observation_frame_id": estimate.source_observation_frame_id,
                "source_control_cycle_id": estimate.source_control_cycle_id,
                "cognitive_state": estimate.cognitive_state.value,
                "attention_stability": estimate.attention_stability,
                "cognitive_load": estimate.cognitive_load,
                "fatigue_probability": estimate.fatigue_probability,
                "recovery_probability": estimate.recovery_probability,
                "confidence": estimate.confidence,
                "trend": estimate.trend,
                "validity_horizon": estimate.validity_horizon,
                "evidence_used": list(estimate.evidence_used),
                "evidence_rejected": list(estimate.evidence_rejected),
                "reason_codes": list(estimate.reason_codes),
            },
            component="clm01_control",
            component_version="1.0.0",
            provenance=provenance,
            data_classification=DataClassification.INTERNAL,
        )

    def _emit_decision(self, decision: ControlDecision, provenance: list[EventID]) -> Event:
        return self.runtime.emit(
            CLM01EventType.CONTROL_DECISION_MADE,
            decision.as_dict(),
            component="clm01_control",
            component_version="1.0.0",
            provenance=provenance,
            data_classification=DataClassification.INTERNAL,
        )

    def _emit_actuation_requested(
        self, decision: ControlDecision, provenance: list[EventID]
    ) -> Event:
        return self.runtime.emit(
            CLM01EventType.ACTUATION_REQUESTED,
            {
                "decision_id": decision.decision_id,
                "requested_control_state_id": decision.proposed_control_state.control_state_id,
                "requested_state": decision.proposed_control_state.as_dict(),
                "safe_application_boundary": decision.safe_application_boundary,
            },
            component="clm01_control",
            component_version="1.0.0",
            provenance=provenance,
            data_classification=DataClassification.INTERNAL,
        )

    def _emit_actuation_applied(
        self, receipt: ActuationReceipt, provenance: list[EventID]
    ) -> Event:
        return self.runtime.emit(
            CLM01EventType.ACTUATION_APPLIED,
            receipt.as_dict(),
            component="clm01_control",
            component_version="1.0.0",
            provenance=provenance,
            data_classification=DataClassification.INTERNAL,
        )

    def _render_stimulus(
        self,
        control_state: MantraControlState,
        receipt: ActuationReceipt | None,
        provenance: list[EventID],
        render_cycle_id: str,
    ) -> Event:
        rendered_stimulus_id = str(make_id(RenderedStimulusID))
        media_handle = f"fixture://clm01/render/{render_cycle_id}"
        payload: dict[str, Any] = {
            "render_cycle_id": render_cycle_id,
            "rendered_stimulus_id": rendered_stimulus_id,
            "media_handle": media_handle,
            "control_state": control_state.as_dict(),
            "applied_control_state_id": control_state.control_state_id,
            "audio_generated": False,
        }
        if receipt is not None:
            payload["actuation_receipt_id"] = receipt.command_id
        return self.runtime.emit(
            CLM01EventType.ADAPTED_STIMULUS_RENDERED,
            payload,
            component="clm01_renderer",
            component_version="1.0.0",
            provenance=provenance,
            correlation_id=CorrelationID(rendered_stimulus_id),
            data_classification=DataClassification.INTERNAL,
        )

    def _emit_intervention_outcome(
        self,
        estimate: CognitiveStateEstimate,
        decision: ControlDecision,
        receipt: ActuationReceipt,
        rendered: Event,
        provenance: list[EventID],
    ) -> Event:
        return self.runtime.emit(
            CLM01EventType.INTERVENTION_OUTCOME_EVALUATED,
            {
                "outcome_id": f"outcome-{self.session_id}-{rendered.payload['render_cycle_id']}",
                "render_cycle_id": rendered.payload["render_cycle_id"],
                "rendered_stimulus_id": rendered.payload["rendered_stimulus_id"],
                "actuation_receipt_id": receipt.command_id,
                "applied_control_state_id": receipt.applied_control_state_id,
                "decision_id": decision.decision_id,
                "estimate_id": estimate.estimate_id,
                "cognitive_state": estimate.cognitive_state.value,
                "control_state": receipt.applied_state.as_dict(),
                "cognitive_load": estimate.cognitive_load,
                "assistance_level": receipt.applied_state.assistance_level,
                "improvement_observed": estimate.trend == "recovering",
            },
            component="clm01_control",
            component_version="1.0.0",
            provenance=provenance,
            data_classification=DataClassification.INTERNAL,
        )
