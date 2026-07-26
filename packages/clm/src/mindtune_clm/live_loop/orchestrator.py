"""CLM-04B live closed-loop orchestrator."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from mindtune_clm.audio.assets import AudioAssetRegistry, AudioRole
from mindtune_clm.audio.playback import PlaybackScheduler
from mindtune_clm.audio.renderer import AudioRenderer, AudioRenderError
from mindtune_clm.events import CLM01EventType
from mindtune_clm.live.gateway import LiveGateway
from mindtune_clm.live_loop.control import LiveControlPipeline
from mindtune_clm.live_loop.events import LiveClosedLoopEventType
from mindtune_clm.live_loop.health import LiveClosedLoopHealth, LiveClosedLoopHealthStatus
from mindtune_clm.live_loop.latency import LatencyTracker
from mindtune_clm.live_loop.outcomes import InterventionOutcome
from mindtune_clm.live_loop.playback_backend import DeterministicPlaybackBackend, PlaybackBackend
from mindtune_clm.live_loop.receipts import LiveLoopCycleReceipt
from mindtune_clm.live_loop.safety import SafetyAction, SafetyController
from mindtune_clm.live_loop.state import LiveClosedLoopState, LiveLoopStatus
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.voice.cache import VoiceCache
from mindtune_clm.voice.fixture_clm03b import hebrew_form_request
from mindtune_clm.voice.models import PedagogicalVoiceRequest, SynthesisParameters
from mindtune_clm.voice.routing import build_speechgen_request_text, cache_key, route
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
from mpe.types import EventID, ProtocolVersionID, SessionID, make_id

_ORCHESTRATOR_VERSION = "clm04b-orchestrator.v1"


def _default_providers() -> ProviderSet:
    return ProviderSet(
        renderer=MockRenderer(),
        observation=MockKeyboardObservationProvider(),
        interpreter=MockResponseInterpreter(),
        normalizer=MockDomainNormalizer(),
        evaluator=MockEvaluator(),
        scheduler=MockScheduler(),
    )


def _default_voice_request() -> PedagogicalVoiceRequest:
    return hebrew_form_request()


@dataclass
class LiveClosedLoopOrchestrator:
    """Live closed-loop orchestrator for FC11 + Giuseppe/Aaron audio.

    Reuses CLM-04 gateway sensors, CLM-01 control, and CLM-03/03B audio.
    The fast loop never calls SpeechGen, Pealim, the Hebrew inflector, or the
    network; it resolves voice assets from a pre-populated ``VoiceCache``.
    """

    version: str = _ORCHESTRATOR_VERSION
    gateway: LiveGateway | None = None
    control: LiveControlPipeline = field(default_factory=LiveControlPipeline)
    cache: VoiceCache | None = None
    renderer: AudioRenderer | None = None
    scheduler: PlaybackScheduler | None = None
    playback_backend: PlaybackBackend = field(default_factory=DeterministicPlaybackBackend)
    safety: SafetyController = field(default_factory=SafetyController)
    latency: LatencyTracker = field(default_factory=LatencyTracker)
    health: LiveClosedLoopHealth = field(default_factory=lambda: LiveClosedLoopHealth(health_id="clm04b"))
    store: EventStore = field(default_factory=InMemoryEventStore)
    clock: Clock = field(default_factory=Clock)
    protocol_version_id: ProtocolVersionID = field(
        default_factory=lambda: ProtocolVersionID("clm-04b-v1.0.0")
    )
    program_version_id: Any = field(default_factory=lambda: "clm-04b-program-v1.0.0")
    learner_id: str = "learner_clm04b"
    asset_registry: AudioAssetRegistry | None = None
    voice_request_factory: Callable[[], PedagogicalVoiceRequest] | None = None
    safe_boundary: str = "between_mantra_cycles"

    session_id: SessionID | None = None
    runtime: Runtime = field(init=False)
    state: LiveClosedLoopState = field(default_factory=LiveClosedLoopState)

    def __post_init__(self) -> None:
        if self.session_id is None:
            self.session_id = SessionID(str(make_id(SessionID)))
        self.state.session_id = str(self.session_id)
        self.runtime = Runtime(self.store, _default_providers(), self.clock)
        if self.scheduler is None:
            self.scheduler = PlaybackScheduler(
                backend=self.playback_backend.play,
                backend_latency=0.0,
                safe_boundary=self.safe_boundary,
            )
        if self.voice_request_factory is None:
            self.voice_request_factory = _default_voice_request
        if self.asset_registry is None:
            self.asset_registry = AudioAssetRegistry()
        if self.renderer is None:
            self.renderer = AudioRenderer(asset_registry=self.asset_registry)
        # Ensure the renderer and orchestrator share the same registry.
        elif self.renderer.asset_registry is None:
            self.renderer.asset_registry = self.asset_registry

    def _emit_clm04b(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        provenance: list[EventID] | None = None,
        component: str = "clm04b_orchestrator",
        component_version: str | None = None,
        data_classification: DataClassification = DataClassification.INTERNAL,
    ) -> Event:
        """Emit a CLM-04B event to the MPE store without requiring a state handler."""
        component_version = component_version or self.version
        sid = self.session_id
        assert sid is not None, "session_id must be created before emitting events"
        last_seq = self.runtime.store.get_last_sequence(sid)
        timestamp = self.runtime.clock.now()
        self.runtime.clock.advance()
        prov: list[EventID] = []
        if provenance:
            prov = [EventID(str(p)) for p in provenance if p]
        elif self.state.last_event_id:
            prov = [EventID(str(self.state.last_event_id))]
        event = Event(
            event_id=make_id(EventID),
            event_type=event_type,
            schema_version="1.1",
            session_id=sid,
            session_sequence_number=last_seq + 1,
            protocol_version_id=self.protocol_version_id,
            timestamp=timestamp,
            component=component,
            component_version=component_version,
            provenance=prov,
            payload=payload,
            data_classification=data_classification,
        )
        self.runtime.store.append(event, expected_version=last_seq)
        self.state.last_event_id = str(event.event_id)
        return event

    def start(self) -> Event:
        """Create and start the MPE session."""
        self.runtime.create_session(
            program_version_id=self.program_version_id,
            protocol_version_id=self.protocol_version_id,
            learner_id=self.learner_id,
            session_id=self.session_id,
        )
        _ = self.runtime.start_session(
            random_seed="clm04b_seed_0",
            start_parameters={
                "orchestrator_version": self.version,
                "safety_version": self.safety.version,
                "playback_backend": self.playback_backend.version,
            },
        )
        self.state.status = LiveLoopStatus.RUNNING
        self.safety.start()
        self.health = self.health.transition(LiveClosedLoopHealthStatus.HEALTHY)
        started = self._emit_clm04b(
            LiveClosedLoopEventType.ORCHESTRATOR_STARTED,
            {
                "orchestrator_version": self.version,
                "safety_version": self.safety.version,
                "playback_backend_version": self.playback_backend.version,
                "session_id": str(self.session_id),
            },
            component="clm04b_orchestrator",
            component_version=self.version,
            data_classification=DataClassification.INTERNAL,
        )
        self.state.last_event_id = str(started.event_id)
        return started

    def pause(self) -> None:
        if self.state.status != LiveLoopStatus.RUNNING:
            return
        self.state.status = LiveLoopStatus.PAUSED
        self.safety.pause()
        self.health = self.health.transition(LiveClosedLoopHealthStatus.PAUSED)
        self._emit_clm04b(
            LiveClosedLoopEventType.ORCHESTRATOR_PAUSED,
            {"session_id": str(self.session_id)},
            component="clm04b_orchestrator",
            component_version=self.version,
        )

    def resume(self) -> None:
        if self.state.status != LiveLoopStatus.PAUSED:
            return
        self.state.status = LiveLoopStatus.RUNNING
        self.safety.resume()
        self.health = self.health.transition(LiveClosedLoopHealthStatus.HEALTHY)
        self._emit_clm04b(
            LiveClosedLoopEventType.ORCHESTRATOR_RESUMED,
            {"session_id": str(self.session_id)},
            component="clm04b_orchestrator",
            component_version=self.version,
        )

    def stop(self) -> None:
        if self.state.status in {LiveLoopStatus.STOPPED, LiveLoopStatus.KILLED}:
            return
        self._stop_backend()
        self.state.status = LiveLoopStatus.STOPPED
        self.safety.stop()
        self.health = self.health.transition(LiveClosedLoopHealthStatus.STOPPED)
        self._emit_clm04b(
            LiveClosedLoopEventType.ORCHESTRATOR_STOPPED,
            {"session_id": str(self.session_id), "status": self.state.status.value},
            component="clm04b_orchestrator",
            component_version=self.version,
        )

    def kill(self) -> None:
        """Immediate hard stop."""
        self._stop_backend()
        self.state.status = LiveLoopStatus.KILLED
        self.state.killed = True
        self.safety.kill()
        self.health = self.health.transition(LiveClosedLoopHealthStatus.KILLED)
        self._emit_clm04b(
            LiveClosedLoopEventType.ORCHESTRATOR_KILLED,
            {"session_id": str(self.session_id)},
            component="clm04b_orchestrator",
            component_version=self.version,
        )

    def _stop_backend(self) -> None:
        if self.playback_backend is not None:
            try:
                self.playback_backend.stop()
            except Exception:
                pass

    def run(self) -> LiveClosedLoopState:
        """Run the full live closed-loop from the attached gateway, if present."""
        self.start()
        if self.gateway is None:
            self.stop()
            return self.state
        gateway_result = self.gateway.run()
        for frame in gateway_result.observation_frames:
            if self.state.status in {LiveLoopStatus.STOPPED, LiveLoopStatus.KILLED}:
                break
            self.run_step(frame)
        self.stop()
        return self.state

    def _resolve_audio_asset(self, frame: ObservationFrame) -> bool:
        """Resolve a voice asset from the cache for the current mantra.

        Returns True when an asset was resolved and False on cache miss.
        The fast loop never calls SpeechGen; it only reads the cache.
        """
        if self.cache is None or self.asset_registry is None:
            return False
        if self.voice_request_factory is None:
            return False
        try:
            request = self.voice_request_factory()
            voice_route = route(request)
            tts_text = build_speechgen_request_text(request, voice_route)
            key = cache_key(voice_route, tts_text, SynthesisParameters())
            cached = self.cache.get(key)
            if cached is None:
                self.state.cache_misses += 1
                self.health = self.health.with_counters(cache_misses=1)
                self._emit_clm04b(
                    LiveClosedLoopEventType.CACHE_MISS,
                    {
                        "control_cycle_id": frame.control_cycle_id,
                        "cache_key": key,
                        "voice": voice_route.voice_display_name,
                    },
                    component="clm04b_voice",
                    component_version=self.version,
                    data_classification=DataClassification.INTERNAL,
                )
                return False
            audio = cached.to_audio_asset(
                asset_id="speech_segment",
                role=AudioRole.SPEECH_SEGMENT,
                label="resolved_from_cache",
            )
            self.asset_registry.register(audio)
            return True
        except Exception as exc:
            self._emit_clm04b(
                LiveClosedLoopEventType.CACHE_MISS,
                {
                    "control_cycle_id": frame.control_cycle_id,
                    "reason": str(exc),
                },
                component="clm04b_voice",
                component_version=self.version,
                data_classification=DataClassification.INTERNAL,
            )
            return False

    def run_step(self, frame: ObservationFrame) -> LiveLoopCycleReceipt:  # noqa: C901
        """Execute one closed-loop cycle for the supplied observation frame."""
        self.state.frame_count += 1
        timestamp = float(frame.observation_timestamp)

        # --- Observation ----------------------------------------------------
        obs_event = self.runtime.emit(
            CLM01EventType.OBSERVATION_FRAME_CREATED,
            {
                "observation_frame_id": frame.observation_frame_id,
                "control_cycle_id": frame.control_cycle_id,
                "session_id": frame.session_id,
                "sequence_number": frame.sequence_number,
                "observation_timestamp": frame.observation_timestamp,
                "available_modalities": list(frame.available_modalities),
                "source_event_ids": list(frame.source_event_ids),
            },
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[EventID(str(self.state.last_event_id))] if self.state.last_event_id else [],
            data_classification=DataClassification.INTERNAL,
        )
        self._emit_clm04b(
            LiveClosedLoopEventType.OBSERVATION_FRAME_CONSUMED,
            {
                "observation_frame_id": frame.observation_frame_id,
                "control_cycle_id": frame.control_cycle_id,
                "session_id": frame.session_id,
            },
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[obs_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        self.latency.start_frame(frame.observation_frame_id, timestamp)
        self.latency.start_render(frame.observation_frame_id, timestamp)

        # --- Control --------------------------------------------------------
        missing = not frame.available_modalities
        degraded = (
            frame.eeg_quality is not None
            and any(token in (frame.eeg_quality or "").lower() for token in ("poor", "artifact", "bad"))
        )
        estimate, raw_decision, _ = self.control.process(
            frame,
            timestamp,
            decision_id=f"decision-{frame.control_cycle_id}",
            command_id=f"actuate-{frame.control_cycle_id}",
        )
        est_event = self.runtime.emit(
            CLM01EventType.COGNITIVE_STATE_ESTIMATED,
            {
                "estimate_id": estimate.estimate_id,
                "source_observation_frame_id": frame.observation_frame_id,
                "source_control_cycle_id": frame.control_cycle_id,
                "cognitive_state": estimate.cognitive_state.value,
                "attention_stability": estimate.attention_stability,
                "cognitive_load": estimate.cognitive_load,
                "fatigue_probability": estimate.fatigue_probability,
                "recovery_probability": estimate.recovery_probability,
                "confidence": estimate.confidence,
                "trend": estimate.trend,
                "validity_horizon": estimate.validity_horizon,
            },
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[obs_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        # --- Safety ---------------------------------------------------------
        applied_state, action, safety_reasons, should_stop = self.safety.evaluate(
            timestamp,
            raw_decision.proposed_control_state,
            self.control.actuator.current_state,
            self.state,
            self.health,
            self.latency,
            latency_key=frame.observation_frame_id,
            missing_window=missing,
            degraded_window=degraded,
        )

        if action == SafetyAction.FREEZE:
            self.state.policy_frozen = True
        else:
            self.state.policy_frozen = False

        if safety_reasons and action in (SafetyAction.BASELINE, SafetyAction.FREEZE):
            self.state.baseline_forced = action == SafetyAction.BASELINE
            self._emit_clm04b(
                LiveClosedLoopEventType.SAFETY_ENVELOPE_VIOLATED,
                {
                    "control_cycle_id": frame.control_cycle_id,
                    "reason_codes": list(safety_reasons),
                    "action": action.value,
                },
                component="clm04b_safety",
                component_version=self.safety.version,
                provenance=[est_event.event_id],
                data_classification=DataClassification.INTERNAL,
            )

        if self.state.baseline_forced:
            self._emit_clm04b(
                LiveClosedLoopEventType.BASELINE_FALLBACK_ACTIVATED,
                {
                    "control_cycle_id": frame.control_cycle_id,
                    "reason_codes": list(safety_reasons),
                },
                component="clm04b_safety",
                component_version=self.safety.version,
                provenance=[est_event.event_id],
                data_classification=DataClassification.INTERNAL,
            )

        if action == SafetyAction.BASELINE or self.state.baseline_forced:
            from dataclasses import replace
            safe_decision = replace(raw_decision, proposed_control_state=applied_state)
        else:
            safe_decision = raw_decision

        receipt = self.control.actuator.apply(safe_decision, timestamp, f"actuate-{frame.control_cycle_id}")
        decision_event = self._emit_clm04b(
            LiveClosedLoopEventType.CONTROL_DECISION_MADE,
            safe_decision.as_dict(),
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[est_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )
        act_event = self._emit_clm04b(
            LiveClosedLoopEventType.ACTUATION_APPLIED,
            receipt.as_dict(),
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[decision_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        self.state.record_decision(timestamp, safe_decision.decision_id)
        self.health = self.health.with_counters(decision_count=1)
        if safety_reasons:
            self.health = self.health.with_counters(safety_violations=1)
        if self.state.baseline_forced:
            self.health = self.health.with_counters(baseline_fallback_count=1)

        # --- Voice cache resolution -----------------------------------------
        cache_miss = not self._resolve_audio_asset(frame)

        # --- Render ---------------------------------------------------------
        render_cycle_id = f"rc-{frame.control_cycle_id}"
        artifact: Any | None = None
        render_failed = False
        self.latency.start_render(frame.observation_frame_id, timestamp)
        if self.renderer is not None:
            try:
                artifact = self.renderer.render(
                    receipt.applied_state,
                    receipt.command_id,
                    safe_decision.decision_id,
                    render_cycle_id,
                    self.runtime,
                )
                self.state.render_count += 1
                self.health = self.health.with_counters(render_count=1)
            except AudioRenderError as exc:
                render_failed = True
                self.state.render_failures += 1
                self.health = self.health.with_counters(render_failures=1)
                self._emit_clm04b(
                    LiveClosedLoopEventType.RENDER_FAILED,
                    {
                        "render_cycle_id": render_cycle_id,
                        "control_cycle_id": frame.control_cycle_id,
                        "reason": exc.reason,
                    },
                    component="clm04b_audio",
                    component_version=self.version,
                    provenance=[act_event.event_id],
                    data_classification=DataClassification.INTERNAL,
                )

        self.latency.finish_render(frame.observation_frame_id, timestamp)

        # --- Playback / safe boundary ---------------------------------------
        playback_receipt: Any | None = None
        playback_failed = False

        if artifact is not None:
            if self.state.cycle.between_cycles(timestamp):
                # Activate any pending artifact first, then schedule current.
                if self.state.cycle.pending_artifact is not None:
                    self.state.cycle.activate_pending(timestamp)
                self._schedule(frame, artifact, timestamp, receipt)
                playback_receipt = self.state.cycle.current_playback_receipt
                playback_failed = not playback_receipt.accepted if playback_receipt is not None else True
            else:
                # Mid-cycle: queue as pending; current audio stays immutable.
                self.state.cycle.set_pending(artifact)
                playback_receipt = self.state.cycle.current_playback_receipt

        # --- Health updates -------------------------------------------------
        if playback_receipt is not None and not playback_receipt.accepted:
            playback_failed = True
            self.state.playback_failures += 1
            self.health = self.health.with_counters(playback_failures=1)
            self._emit_clm04b(
                LiveClosedLoopEventType.PLAYBACK_FAILED,
                {
                    "control_cycle_id": frame.control_cycle_id,
                    "playback_receipt_id": playback_receipt.playback_receipt_id,
                    "reason": playback_receipt.rejection_reason,
                },
                component="clm04b_audio",
                component_version=self.version,
                provenance=[act_event.event_id] if artifact is not None else [],
                data_classification=DataClassification.INTERNAL,
            )

        if render_failed:
            self.health = self.health.transition(LiveClosedLoopHealthStatus.DEGRADED)
        elif playback_failed:
            self.health = self.health.transition(LiveClosedLoopHealthStatus.DEGRADED)

        self.latency.finish_playback(frame.observation_frame_id, timestamp)
        latency_ok, latency_reasons = self.latency.check(frame.observation_frame_id)
        if not latency_ok and latency_reasons:
            self.health = self.health.with_counters(latency_violations=1)
            self._emit_clm04b(
                LiveClosedLoopEventType.LATENCY_EXCEEDED,
                {
                    "control_cycle_id": frame.control_cycle_id,
                    "reason_codes": list(latency_reasons),
                },
                component="clm04b_latency",
                component_version=self.version,
                provenance=[act_event.event_id],
                data_classification=DataClassification.INTERNAL,
            )

        # --- Outcome --------------------------------------------------------
        outcome = InterventionOutcome(
            outcome_id=f"outcome-{frame.control_cycle_id}-{uuid.uuid4()}",
            render_cycle_id=render_cycle_id,
            observation_frame_id=frame.observation_frame_id,
            control_cycle_id=frame.control_cycle_id,
            decision_id=safe_decision.decision_id,
            actuation_receipt_id=receipt.command_id,
            artifact_id=artifact.artifact_id if artifact is not None else None,
            playback_receipt_id=playback_receipt.playback_receipt_id if playback_receipt is not None else None,
            intended_control_state_id=safe_decision.proposed_control_state.control_state_id,
            observed_control_state_id=receipt.applied_state.control_state_id,
            cognitive_state=estimate.cognitive_state.value,
            assistance_level=receipt.applied_state.assistance_level,
            successful=not render_failed and not playback_failed,
            safety_fallback=self.state.baseline_forced,
            reason_codes=list(safety_reasons) + list(estimate.reason_codes),
        )

        outcome_event = self._emit_clm04b(
            LiveClosedLoopEventType.INTERVENTION_OUTCOME,
            outcome.as_dict(),
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[act_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )
        self.state.last_event_id = str(outcome_event.event_id)

        self.health = self.health.with_counters(frame_count=1)
        self._emit_clm04b(
            LiveClosedLoopEventType.HEALTH_CHANGED,
            self.health.as_dict(),
            component="clm04b_orchestrator",
            component_version=self.version,
            provenance=[outcome_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        if should_stop:
            self.stop()

        return LiveLoopCycleReceipt(
            control_cycle_id=frame.control_cycle_id,
            render_cycle_id=render_cycle_id,
            observation_frame_id=frame.observation_frame_id,
            estimate=estimate,
            actuation_receipt=receipt,
            artifact=artifact,
            playback_receipt=playback_receipt,
            outcome=outcome,
            safety_fallback=self.state.baseline_forced,
            safety_reason_codes=list(safety_reasons),
            render_failed=render_failed,
            playback_failed=playback_failed,
            cache_miss=cache_miss,
            killed=self.state.killed,
        )

    def _schedule(
        self,
        frame: ObservationFrame,
        artifact: Any,
        timestamp: float,
        receipt: Any,
    ) -> None:
        """Schedule playback for an artifact at a safe boundary."""
        assert self.scheduler is not None
        self.latency.start_playback(frame.observation_frame_id, timestamp)
        from_id = self.state.cycle.current_artifact_id or "none"
        self.scheduler.backend = self.playback_backend.play
        playback_receipt = self.scheduler.schedule(
            artifact,
            f"rc-{frame.control_cycle_id}",
            timestamp,
            self.safe_boundary,
            receipt.applied_state.control_state_id,
            receipt.command_id,
            self.runtime,
        )
        self.state.cycle.start_cycle(timestamp, artifact)
        self.state.cycle.current_playback_receipt = playback_receipt
        self.state.record_switch(timestamp, from_id, artifact.artifact_id)

    def complete(self) -> None:
        """Emit the completed session event and stop."""
        if self.state.status == LiveLoopStatus.STOPPED:
            return
        self.runtime.complete_session()
        self._emit_clm04b(
            LiveClosedLoopEventType.ORCHESTRATOR_COMPLETED,
            {
                "session_id": str(self.session_id),
                "final_status": self.state.status.value,
                "frame_count": self.state.frame_count,
                "decision_count": self.state.decision_count,
                "render_count": self.state.render_count,
                "playback_count": self.state.playback_count,
            },
            component="clm04b_orchestrator",
            component_version=self.version,
        )
        self.stop()
