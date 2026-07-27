"""Hebrew adaptive session orchestrator."""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

from mindtune_clm.audio.playback import PlaybackScheduler
from mindtune_clm.audio.renderer import AudioRenderer
from mindtune_clm.hebrew_slice.adaptation import HebrewAdaptationPolicy
from mindtune_clm.hebrew_slice.asset_resolution import (
    HebrewAssetError,
    HebrewAssetResolver,
)
from mindtune_clm.hebrew_slice.events import HebrewEventLog, HebrewSliceEventType
from mindtune_clm.hebrew_slice.learning_state import (
    HebrewItemLearningState,
    summarize_learning_state,
    update_learning_state,
)
from mindtune_clm.hebrew_slice.models import (
    HebrewAdaptiveEvent,
    HebrewAdaptiveItem,
    HebrewPedagogicalDecision,
    HebrewResponse,
    HebrewScore,
    HebrewTrial,
)
from mindtune_clm.hebrew_slice.scoring import score_response
from mindtune_clm.hebrew_slice.trial_factory import HebrewTrialFactory
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.policy import ControlPolicy
from mindtune_clm.state import MantraControlState, StateEstimator
from mpe.domains.hebrew.normalization import (
    normalize_hebrew_response,
)


class HebrewSessionError(Exception):
    """Raised when a Hebrew session cannot continue safely."""

    def __init__(self, message: str, abort_reason: str = ""):
        super().__init__(message)
        self.abort_reason = abort_reason


class HebrewAdaptiveSession:
    """A bounded Hebrew adaptive vertical-slice session."""

    def __init__(
        self,
        session_id: str,
        items: list[HebrewAdaptiveItem],
        asset_registry,
        *,
        max_trials: int = 20,
        max_duration_seconds: float = 300.0,
        clock: Callable[[], float] = time.time,
        estimator: StateEstimator | None = None,
        control_policy: ControlPolicy | None = None,
        renderer: AudioRenderer | None = None,
        scheduler: PlaybackScheduler | None = None,
        trial_factory: HebrewTrialFactory | None = None,
        asset_resolver: HebrewAssetResolver | None = None,
        adaptation_policy: HebrewAdaptationPolicy | None = None,
    ) -> None:
        self.session_id = session_id
        self.items = list(items)
        self.max_trials = max_trials
        self.max_duration_seconds = max_duration_seconds
        self.clock = clock
        self.event_log = HebrewEventLog(session_id=session_id)
        self.estimator = estimator or StateEstimator()
        self.control_policy = control_policy or ControlPolicy()
        self.renderer = renderer or AudioRenderer(asset_registry)
        self.scheduler = scheduler or PlaybackScheduler()
        self.trial_factory = trial_factory or HebrewTrialFactory()
        self.asset_resolver = asset_resolver or HebrewAssetResolver(asset_registry)
        self.adaptation_policy = adaptation_policy or HebrewAdaptationPolicy()

        self.learning_states: dict[str, HebrewItemLearningState] = {}
        self.current_trial: HebrewTrial | None = None
        self.current_item: HebrewAdaptiveItem | None = None
        self.current_control_state = MantraControlState.baseline()
        self.trial_index = 0
        self.recent_item_ids: list[str] = []
        self.response_ids: set[str] = set()
        self.last_score: HebrewScore | None = None
        self.last_response: HebrewResponse | None = None
        self.completed = False
        self.aborted = False
        self.sensor_failure_count = 0
        self.max_sensor_failures = 3
        self.start_time = 0.0
        self._current_decision_id: str = ""
        self._current_render_cycle_id: str = ""

    def start(self) -> HebrewTrial:
        """Start the session and prepare the first trial."""
        self.start_time = self.clock()
        self.event_log.emit(
            HebrewSliceEventType.HEBREW_SESSION_STARTED,
            {
                "session_id": self.session_id,
                "max_trials": self.max_trials,
                "max_duration_seconds": self.max_duration_seconds,
                "control_state": self.current_control_state.as_dict(),
            },
        )
        self._init_learning_states()
        self.current_item = self._select_initial_item()
        self.trial_index = 1
        self.recent_item_ids.append(self.current_item.item_id)
        self.current_trial = self._prepare_trial(self.current_item)
        return self.current_trial

    def _init_learning_states(self) -> None:
        for item in self.items:
            self.learning_states[item.item_id] = HebrewItemLearningState(
                item_id=item.item_id,
                linguistic_validation_status=item.linguistic_validation_status,
                reference_only=item.linguistic_validation_status not in ("approved", "validated"),
            )

    def _select_initial_item(self) -> HebrewAdaptiveItem:
        eligible = [i for i in self.items if i.linguistic_validation_status in ("approved", "validated")]
        return eligible[0] if eligible else self.items[0]

    def _prepare_trial(self, item: HebrewAdaptiveItem) -> HebrewTrial:
        trial = self.trial_factory.make_trial(
            item,
            trial_type="italian_to_hebrew",
            sequence=self.trial_index,
            control_state=self.current_control_state,
            direction="italian_to_hebrew",
        )
        self.event_log.emit(
            HebrewSliceEventType.HEBREW_TRIAL_PREPARED,
            {
                "trial_id": trial.trial_id,
                "item_id": item.item_id,
                "trial_type": trial.trial_type,
                "control_state_id": self.current_control_state.control_state_id,
            },
            provenance=[self.session_id],
        )
        return trial

    def respond(
        self,
        raw_response: str,
        *,
        response_time_ms: float = 1500.0,
        confidence: int = 5,
        hint_used: bool = False,
        replay_count: int = 0,
        audio_assistance_level: float | None = None,
        response_id: str | None = None,
        sensor_disconnect: bool = False,
    ) -> dict[str, Any]:
        """Submit a response, run scoring, CLM loop, and prepare the next trial."""
        if self.completed or self.aborted:
            raise HebrewSessionError("session already ended")
        if self.current_trial is None or self.current_item is None:
            raise HebrewSessionError("no active trial")

        trial = self.current_trial
        item = self.current_item
        response_id = response_id or f"resp-{uuid.uuid4().hex[:12]}"
        if response_id in self.response_ids:
            return self._duplicate_response_result(response_id)
        self.response_ids.add(response_id)

        normalized = normalize_hebrew_response(raw_response)
        response = HebrewResponse(
            response_id=response_id,
            trial_id=trial.trial_id,
            item_id=item.item_id,
            prompt_id=trial.prompt_id,
            presentation_id=trial.presentation_id,
            raw_response=raw_response,
            normalized_response=normalized,
            response_semantic_timestamp=self.clock(),
            response_time_ms=response_time_ms,
            confidence=confidence,
            hint_used=hint_used,
            replay_count=replay_count,
            audio_assistance_level=audio_assistance_level or self.current_control_state.assistance_level,
        )

        score = score_response(item, response)
        self.last_response = response
        self.last_score = score

        self.event_log.emit(
            HebrewSliceEventType.HEBREW_RESPONSE_SUBMITTED,
            response.as_dict(),
            provenance=[trial.trial_id],
        )
        scored_event = self.event_log.emit(
            HebrewSliceEventType.HEBREW_RESPONSE_SCORED,
            score.as_dict(),
            provenance=[response_id],
        )
        if score.error_codes:
            self.event_log.emit(
                HebrewSliceEventType.HEBREW_ERROR_CLASSIFIED,
                {"response_id": response_id, "error_codes": score.error_codes},
                provenance=[scored_event.event_id],
            )

        # Learning-state update (not inferred from EEG).
        state = self.learning_states[item.item_id]
        updated = update_learning_state(state, response, score, response.response_semantic_timestamp)
        self.learning_states[item.item_id] = updated
        self.event_log.emit(
            HebrewSliceEventType.HEBREW_LEARNING_STATE_UPDATED,
            summarize_learning_state(updated),
            provenance=[scored_event.event_id],
        )

        # CLM observation from behavioral + optional sensor evidence.
        self._handle_sensor(sensor_disconnect)
        frame = self._build_observation(response, score, sensor_disconnect)
        estimate = self.estimator.estimate(frame)

        decision_id = f"dec-{self.session_id}-{self.trial_index}"
        self._current_decision_id = decision_id
        control_decision = self.control_policy.decide(
            estimate,
            self.current_control_state,
            self.clock(),
            decision_id,
        )
        self.current_control_state = control_decision.proposed_control_state
        self.event_log.emit(
            HebrewSliceEventType.HEBREW_ASSISTANCE_CHANGED,
            {
                "decision_id": decision_id,
                "cognitive_state": estimate.cognitive_state.value,
                "control_state": self.current_control_state.as_dict(),
            },
            provenance=[estimate.estimate_id],
        )

        # Resolve cached assets and render audio for the *next* cycle.
        render_cycle_id = f"rc-{self.session_id}-{self.trial_index}"
        self._current_render_cycle_id = render_cycle_id
        playback_receipt: dict[str, Any] | None = None
        try:
            resolved = self.asset_resolver.resolve(item)
            self.event_log.emit(
                HebrewSliceEventType.HEBREW_AUDIO_ASSET_RESOLVED,
                resolved.as_dict(),
                provenance=[decision_id],
            )
            artifact = self.renderer.render(
                self.current_control_state,
                actuation_receipt_id=resolved.hebrew_asset_id,
                decision_id=decision_id,
                render_cycle_id=render_cycle_id,
            )
            playback_receipt = self.scheduler.schedule(
                artifact,
                render_cycle_id=render_cycle_id,
                semantic_start_timestamp=self.clock(),
                safe_boundary=control_decision.safe_application_boundary,
                control_state_id=self.current_control_state.control_state_id,
                source_receipt_id=resolved.hebrew_asset_id,
            ).as_dict()
        except HebrewAssetError as exc:
            playback_receipt = {"error": str(exc), "missing_assets": exc.missing_assets, "fallback_triggered": exc.fallback_triggered}

        # Pedagogical adaptation decision.
        learning_state = self.learning_states[item.item_id]
        decision = self.adaptation_policy.decide(
            current_item=item,
            score=score,
            learning_state=learning_state,
            control_state=self.current_control_state,
            recent_item_ids=self.recent_item_ids,
            trial_index=self.trial_index,
        )
        adaptation_event = self.event_log.emit(
            HebrewSliceEventType.HEBREW_PEDAGOGICAL_ADAPTATION_DECIDED,
            decision.as_dict(),
            provenance=[scored_event.event_id, decision_id],
        )

        self._advance(decision, item, adaptation_event)
        return {
            "response": response.as_dict(),
            "score": score.as_dict(),
            "cognitive_state": estimate.cognitive_state.value,
            "control_state": self.current_control_state.as_dict(),
            "playback_receipt": playback_receipt,
            "pedagogical_decision": decision.as_dict(),
            "next_trial": self.current_trial.as_dict() if self.current_trial else None,
        }

    def _handle_sensor(self, sensor_disconnect: bool) -> None:
        if sensor_disconnect:
            self.sensor_failure_count += 1
        else:
            self.sensor_failure_count = 0
        if self.sensor_failure_count >= self.max_sensor_failures:
            self.aborted = True
            self.event_log.emit(
                HebrewSliceEventType.HEBREW_SESSION_ABORTED,
                {"reason": "repeated_sensor_disconnect", "count": self.sensor_failure_count},
            )
            raise HebrewSessionError("repeated sensor disconnect", abort_reason="repeated_sensor_disconnect")

    def _build_observation(self, response: HebrewResponse, score: HebrewScore, sensor_disconnect: bool) -> ObservationFrame:
        eeg_stability: float | None = 0.8
        eeg_quality: str | None = "5"
        if sensor_disconnect:
            eeg_stability = None
            eeg_quality = "poor_signal,artifact"
        error_score = 1.0 if score.overall in ("incorrect", "invalid", "not_answered") else 0.0
        return ObservationFrame(
            observation_frame_id=f"obs-{self.session_id}-{self.trial_index}",
            control_cycle_id=f"cc-{self.session_id}-{self.trial_index}",
            session_id=self.session_id,
            sequence_number=self.trial_index,
            observation_timestamp=response.response_semantic_timestamp,
            behavioral_latency_ms=response.response_time_ms,
            hesitation_score=1.0 - min(1.0, response.confidence / 5.0),
            error_score=error_score,
            eeg_stability=eeg_stability,
            eeg_quality=eeg_quality,
            available_modalities=["behavioral"] if sensor_disconnect else ["behavioral", "eeg"],
            source_event_ids=[response.response_id],
        )

    def _advance(self, decision: HebrewPedagogicalDecision, previous_item: HebrewAdaptiveItem, adaptation_event: HebrewAdaptiveEvent) -> None:
        self.trial_index += 1
        if self.adaptation_policy.stop_requested(self.learning_states, self.trial_index, self.max_trials):
            self.completed = True
            self.event_log.emit(
                HebrewSliceEventType.HEBREW_SESSION_COMPLETED,
                self.summary(),
                provenance=[adaptation_event.event_id],
            )
            self.current_trial = None
            return

        next_item_id = decision.next_item_id or previous_item.item_id
        if decision.interleave_item_id and decision.interleave_item_id != previous_item.item_id:
            self.event_log.emit(
                HebrewSliceEventType.HEBREW_ITEM_INTERLEAVED,
                {"from_item": previous_item.item_id, "to_item": decision.interleave_item_id},
                provenance=[adaptation_event.event_id],
            )
        if decision.repeat_same_item:
            self.event_log.emit(
                HebrewSliceEventType.HEBREW_TRIAL_REPEATED,
                {"item_id": next_item_id, "reasons": decision.reason_codes},
                provenance=[adaptation_event.event_id],
            )

        if next_item_id not in {i.item_id for i in self.items}:
            next_item_id = self.items[0].item_id
        next_item = next((i for i in self.items if i.item_id == next_item_id), self.items[0])
        self.current_item = next_item
        self.recent_item_ids.append(next_item.item_id)
        self.current_trial = self._prepare_trial(next_item)

    def _duplicate_response_result(self, response_id: str) -> dict[str, Any]:
        return {
            "response_id": response_id,
            "duplicate": True,
            "score": self.last_score.as_dict() if self.last_score else None,
            "message": "response already processed; not double-scored",
        }

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serializable session summary."""
        return {
            "session_id": self.session_id,
            "trial_index": self.trial_index,
            "completed": self.completed,
            "aborted": self.aborted,
            "current_control_state": self.current_control_state.as_dict(),
            "learning_states": {k: summarize_learning_state(v) for k, v in self.learning_states.items()},
            "event_count": len(self.event_log.events),
            "causal_graph": self.event_log.causal_graph(),
        }

    def stop(self, reason: str = "user_stop") -> dict[str, Any]:
        """Gracefully stop the session."""
        self.completed = True
        self.current_trial = None
        self.event_log.emit(
            HebrewSliceEventType.HEBREW_SESSION_COMPLETED,
            {"reason": reason, "summary": self.summary()},
        )
        return self.summary()
