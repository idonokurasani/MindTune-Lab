"""BrainLab coordinator."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from mlf.core.domain_adapter import DomainAdapter
from mlf.core.events import Event, EventStore, InMemoryEventStore, make_event
from mlf.core.experiment_engine import ExperimentEngine, MinimalProtocolRunner
from mlf.core.knowledge_graph import KnowledgeGraph, InMemoryKnowledgeGraph
from mlf.core.protocol import ProtocolSpec
from mlf.core.retest import Retest, RetestWindow
from mlf.core.scheduler import M0Scheduler, Recommendation, Scheduler
from mlf.core.scorer import Scorer
from mlf.core.session import LearningSession
from mlf.core.state import LearningState
from mlf.core.state_cache import StateCache
from mlf.core.student import Student
from mlf.core.transformation import LearningTransformation, M0Transformation
from mlf.core.trial import Response, Score, Trial
from mlf.core.unit import LearningUnit


def _default_experiment_engine() -> ExperimentEngine:
    runner = MinimalProtocolRunner()
    runner.register(ProtocolSpec(protocol_id="pilot-a", protocol_version="1.0", condition="NP"))
    return runner


class BrainLab:
    """Domain-agnostic learning coordinator.

    BrainLab owns the event store and coordinates the learning lifecycle. It
    does not implement scoring, state models, domain logic, or protocol
    statistics. It delegates to:

    - ExperimentEngine for protocol data and validation;
    - DomainAdapter for prompt generation and response normalization;
    - Scorer for scoring responses;
    - LearningTransformation for state derivation;
    - Scheduler for recommendations.
    """

    def __init__(
        self,
        store: Optional[EventStore] = None,
        transformation: Optional[LearningTransformation] = None,
        scheduler: Optional[Scheduler] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        domain_adapter: Optional[DomainAdapter] = None,
        scorer: Optional[Scorer] = None,
        experiment_engine: Optional[ExperimentEngine] = None,
        state_cache: Optional[StateCache] = None,
    ) -> None:
        self.store = store or InMemoryEventStore()
        self.transformation = transformation or M0Transformation()
        self.scheduler = scheduler or M0Scheduler()
        self.knowledge_graph = knowledge_graph or InMemoryKnowledgeGraph()
        self.domain_adapter = domain_adapter
        self.scorer = scorer
        self.experiment_engine = experiment_engine or _default_experiment_engine()
        self.state_cache = state_cache
        self._sessions: dict[UUID, LearningSession] = {}
        self._states: dict[tuple[UUID, UUID], LearningState] = {}
        self._session_states: dict[UUID, dict] = {}
        self._response_events: dict[UUID, UUID] = {}
        self._score_events: dict[UUID, UUID] = {}
        self._score_sequence: dict[UUID, int] = {}
        self._units: dict[UUID, LearningUnit] = {}
        self._last_monotonic_ns = self._max_store_monotonic_ns()
        self._load_event_indexes()

    def _max_store_monotonic_ns(self) -> int:
        return max((event.monotonic_ns for event in self.store.read()), default=0)

    def _load_event_indexes(self) -> None:
        """Repopulate in-memory response/score indexes from the store.

        This allows a BrainLab instance to resume an existing session and emit
        correct correction lineage.
        """
        for event in self.store.read():
            if event.event_type == "trial.response":
                trial_id = event.payload.get("trial_id")
                if trial_id:
                    self._response_events[UUID(trial_id)] = event.event_id
            elif event.event_type == "trial.score":
                trial_id = event.payload.get("trial_id")
                if trial_id:
                    self._score_events[UUID(trial_id)] = event.event_id
                    sequence = event.payload.get("correction_sequence") or 0
                    self._score_sequence[UUID(trial_id)] = sequence

    def _next_monotonic_ns(self) -> int:
        self._last_monotonic_ns += 1
        return self._last_monotonic_ns

    def _lineage_payload(
        self,
        session: LearningSession,
        trial: Trial,
        unit: Optional[LearningUnit] = None,
    ) -> dict[str, Any]:
        """Build the generic lineage envelope for a trial event.

        Values are optional and sourced from the configured DomainAdapter, Scorer,
        LearningUnit, and trial context metadata. Missing values are None.
        """
        adapter = self.domain_adapter
        scorer = self.scorer
        metadata = trial.metadata or {}

        domain_id: Optional[str] = None
        domain_version: Optional[str] = None
        domain_adapter_id: Optional[str] = None
        domain_adapter_version: Optional[str] = None
        curriculum_version: Optional[str] = None
        prompt_template_id: Optional[str] = None
        normalization_rules_version: Optional[str] = None

        if adapter is not None:
            domain_id = adapter.domain_id
            domain_version = adapter.domain_version
            domain_adapter_id = adapter.domain_adapter_id or adapter.domain_id
            domain_adapter_version = adapter.domain_adapter_version or adapter.domain_version
            curriculum_version = adapter.curriculum_version()
            prompt_template_id = adapter.prompt_template_version()
            normalization_rules_version = adapter.normalization_rules_version()

        learning_unit_id: Optional[str] = None
        learning_unit_version: Optional[str] = None
        if unit is not None:
            learning_unit_id = str(unit.unit_id)
            learning_unit_version = unit.version

        scorer_id: Optional[str] = None
        scorer_version: Optional[str] = None
        scoring_rules_version: Optional[str] = None
        if scorer is not None:
            scorer_id = scorer.scorer_id
            scorer_version = scorer.scorer_version
            scoring_rules_version = scorer.scoring_rules_version()

        return {
            "lineage_schema_version": "trial-lineage-1.0",
            "domain_id": domain_id,
            "domain_version": domain_version,
            "domain_adapter_id": domain_adapter_id,
            "domain_adapter_version": domain_adapter_version,
            "curriculum_version": curriculum_version,
            "learning_unit_id": learning_unit_id,
            "learning_unit_version": learning_unit_version,
            "knowledge_item_id": metadata.get("knowledge_item_id"),
            "knowledge_item_version": metadata.get("knowledge_item_version"),
            "skill_id": metadata.get("skill_id"),
            "prompt_template_id": prompt_template_id,
            "prompt_template_version": prompt_template_id,
            "prompt_instance_id": metadata.get("prompt_instance_id"),
            "normalization_rules_version": normalization_rules_version,
            "scorer_id": scorer_id,
            "scorer_version": scorer_version,
            "scoring_rules_version": scoring_rules_version,
            "protocol_id": session.protocol_id,
            "protocol_version": session.protocol_version,
            "randomization_ref": metadata.get("randomization_ref"),
            "app_version": "0.2.0",
            "event_schema_version": "mlf-core-0.2.0",
        }

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(
        self,
        student: Student,
        protocol_id: str = "pilot-a",
        condition: Optional[str] = None,
        baseline: Optional[dict[str, Any]] = None,
    ) -> LearningSession:
        """Start a session and emit session.start and session.baseline events."""
        protocol_spec = self.experiment_engine.resolve_protocol(protocol_id)
        session = LearningSession.create(
            student_id=student.student_id,
            condition=condition or protocol_spec.condition,
            baseline=baseline,
            protocol_id=protocol_spec.protocol_id,
            protocol_version=protocol_spec.protocol_version,
        )
        self._sessions[session.session_id] = session

        self._append(
            session,
            make_event(
                event_type="session.start",
                session_id=session.session_id,
                student_id=student.student_id,
                protocol_id=session.protocol_id,
                protocol_version=session.protocol_version,
                payload={
                    "condition": session.condition,
                    "protocol_id": session.protocol_id,
                    "protocol_version": session.protocol_version,
                },
            ),
        )
        if baseline:
            self._append(
                session,
                make_event(
                    event_type="session.baseline",
                    session_id=session.session_id,
                    student_id=student.student_id,
                    protocol_id=session.protocol_id,
                    protocol_version=session.protocol_version,
                    payload=baseline,
                ),
            )
        return session

    def close_session(self, session: LearningSession, end_of_session: Optional[dict[str, Any]] = None) -> LearningSession:
        """End a session and emit session.end."""
        session = session.close(end_of_session)
        self._sessions[session.session_id] = session
        self._append(
            session,
            make_event(
                event_type="session.end",
                session_id=session.session_id,
                student_id=session.student_id,
                protocol_id=session.protocol_id,
                protocol_version=session.protocol_version,
                payload={
                    **(end_of_session or {}),
                    "protocol_id": session.protocol_id,
                    "protocol_version": session.protocol_version,
                },
            ),
        )
        return session

    # ------------------------------------------------------------------
    # Trial lifecycle
    # ------------------------------------------------------------------

    def start_trial(
        self,
        session: LearningSession,
        unit: LearningUnit,
        trial_type: str,
        process_target: str,
        stimulus: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> Trial:
        """Emit trial.start and return a Trial handle."""
        self._units[unit.unit_id] = unit

        if stimulus is None:
            if self.domain_adapter is None:
                raise ValueError("stimulus is required when no domain_adapter is configured")
            stimulus = self.domain_adapter.generate_prompt(unit, trial_type, process_target, context)

        trial = Trial.create(
            session_id=session.session_id,
            unit_id=unit.unit_id,
            trial_type=trial_type,
            process_target=process_target,
            stimulus=stimulus,
            metadata=context or {},
        )
        self._emit_trial_start(session, trial, unit=unit)
        return trial

    def _emit_trial_start(self, session: LearningSession, trial: Trial, unit: Optional[LearningUnit] = None) -> None:
        """Emit trial.start for the given trial."""
        unit = unit or self._units.get(trial.unit_id)
        payload = self._lineage_payload(session, trial, unit)
        payload.update(
            {
                "trial_id": str(trial.trial_id),
                "trial_type": trial.trial_type,
                "process_target": trial.process_target,
                "stimulus": trial.stimulus,
                "trial_metadata": trial.metadata or {},
            }
        )
        self._append(
            session,
            make_event(
                event_type="trial.start",
                session_id=session.session_id,
                student_id=session.student_id,
                unit_id=trial.unit_id,
                protocol_id=session.protocol_id,
                protocol_version=session.protocol_version,
                payload=payload,
                monotonic_ns=trial.monotonic_start_ns,
            ),
        )

    def submit_response(
        self,
        session: LearningSession,
        trial: Trial,
        response: Response,
        monotonic_response_ns: int,
    ) -> Trial:
        """Emit trial.response."""
        response_event = make_event(
            event_type="trial.response",
            session_id=session.session_id,
            student_id=session.student_id,
            unit_id=trial.unit_id,
            protocol_id=session.protocol_id,
            protocol_version=session.protocol_version,
            payload={
                "trial_id": str(trial.trial_id),
                "response_raw": response.raw,
                "response_normalized": response.normalized,
                "response_human_judged": response.human_judged,
                "response_metadata": response.metadata or {},
            },
            monotonic_ns=monotonic_response_ns,
        )
        self._append(session, response_event)
        self._response_events[trial.trial_id] = response_event.event_id

        trial = trial.with_response(response, monotonic_response_ns)
        return trial

    def score_trial(
        self,
        session: LearningSession,
        trial: Trial,
        score: Optional[Score] = None,
        context: Optional[dict[str, Any]] = None,
        unit: Optional[LearningUnit] = None,
    ) -> Trial:
        """Emit trial.score and update state.

        If `score` is not provided, BrainLab delegates to the configured Scorer.
        """
        if score is None:
            if self.scorer is None:
                raise ValueError("score is required when no scorer is configured")
            unit = unit or self._units.get(trial.unit_id)
            if unit is None:
                raise ValueError("unit is required when scoring via scorer")
            response = trial.response
            if response is None:
                raise ValueError("trial has no response to score")
            score = self.scorer.score(unit, response, trial, context)

        response_event_id = self._response_events.get(trial.trial_id)
        if response_event_id is not None and score.source_response_event_id is None:
            score = replace(score, source_response_event_id=response_event_id)

        previous_score_event_id = self._score_events.get(trial.trial_id)
        previous_sequence = self._score_sequence.get(trial.trial_id, 0)
        correction_of_event_id = score.correction_of_event_id
        correction_sequence = score.correction_sequence
        if previous_score_event_id is not None and correction_of_event_id is None:
            correction_of_event_id = previous_score_event_id
            correction_sequence = previous_sequence + 1
        if correction_sequence is None:
            correction_sequence = 0
        score = replace(
            score,
            correction_of_event_id=correction_of_event_id,
            correction_sequence=correction_sequence,
        )

        trial = trial.with_score(score)
        scoring_rules_version = score.scoring_rules_version
        if scoring_rules_version is None and self.scorer is not None:
            scoring_rules_version = self.scorer.scoring_rules_version()
        score_event = make_event(
            event_type="trial.score",
            session_id=session.session_id,
            student_id=session.student_id,
            unit_id=trial.unit_id,
            protocol_id=session.protocol_id,
            protocol_version=session.protocol_version,
            payload={
                "trial_id": str(trial.trial_id),
                "trial_type": trial.trial_type,
                "outcome": score.outcome,
                "latency_ms": score.latency_ms,
                "error_tags": score.error_tags,
                "scorer": score.scorer,
                "scoring_version": score.scoring_version,
                "scorer_id": score.scorer,
                "scorer_version": score.scoring_version,
                "scoring_rules_version": scoring_rules_version,
                "source_response_event_id": str(score.source_response_event_id) if score.source_response_event_id else None,
                "correction_of_event_id": str(score.correction_of_event_id) if score.correction_of_event_id else None,
                "correction_sequence": score.correction_sequence,
                "correction_reason": score.correction_reason,
                "correction_source": score.correction_source,
                "score_metadata": score.metadata or {},
            },
        )
        self._append(session, score_event)
        self._score_events[trial.trial_id] = score_event.event_id
        self._score_sequence[trial.trial_id] = score.correction_sequence or 0
        self._update_state(session.student_id, trial.unit_id)
        return trial

    def trigger_retest(
        self,
        session: LearningSession,
        trial: Trial,
        horizon: str,
        scheduled_at: Optional[datetime] = None,
        window: Optional[RetestWindow] = None,
    ) -> Retest:
        """Emit a ``retest.triggered`` event for a scored trial.

        The scheduler computes the explicit, versioned completion window.
        Retests are idempotent by the pair ``(triggering_score_event_id, horizon)``.
        """
        score_event_id = self._score_events.get(trial.trial_id)
        if score_event_id is None:
            raise ValueError("trial has no score event; cannot trigger retest")

        unit = self._units.get(trial.unit_id)
        if unit is None:
            raise ValueError("unit not found for retest")

        idempotency_key = f"retest:trigger:{score_event_id}:{horizon}"
        existing = self.store.read_by_idempotency_key(idempotency_key)
        if existing is not None:
            return Retest.from_event(existing)

        scheduled = self.scheduler.schedule_retest(
            student_id=session.student_id,
            unit_id=trial.unit_id,
            unit_version=unit.version,
            origin_session_id=session.session_id,
            triggered_by_event_id=score_event_id,
            horizon=horizon,
            scheduled_at=scheduled_at,
            window=window,
        )

        retest_id = uuid4()
        scheduled = scheduled.with_event_id(retest_id)
        event = make_event(
            event_type="retest.triggered",
            session_id=session.session_id,
            student_id=session.student_id,
            unit_id=trial.unit_id,
            protocol_id=session.protocol_id,
            protocol_version=session.protocol_version,
            payload=scheduled.to_event_payload(),
            idempotency_key=idempotency_key,
            event_id=retest_id,
        )
        self._append(session, event)
        return scheduled

    def complete_retest(
        self,
        session: LearningSession,
        retest_id: UUID,
        completed_at: Optional[datetime] = None,
    ) -> Event:
        """Emit a ``retest.completed`` event for a previously triggered retest."""
        trigger_event = self.store.get(retest_id)
        if trigger_event is None or trigger_event.event_type != "retest.triggered":
            raise ValueError("retest_id does not refer to a retest.triggered event")
        unit_id = trigger_event.unit_id
        if unit_id is None:
            raise ValueError("retest.triggered event is missing unit_id")

        idempotency_key = f"retest:completed:{retest_id}"
        existing = self.store.read_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        completed_at = completed_at or datetime.now(timezone.utc)
        event = make_event(
            event_type="retest.completed",
            session_id=session.session_id,
            student_id=session.student_id,
            unit_id=unit_id,
            protocol_id=session.protocol_id,
            protocol_version=session.protocol_version,
            payload={
                "retest_id": str(retest_id),
                "unit_id": str(unit_id),
                "completed_session_id": str(session.session_id),
                "completed_at": completed_at.isoformat(),
            },
            idempotency_key=idempotency_key,
        )
        self._append(session, event)
        return event

    def give_feedback(self, session: LearningSession, trial: Trial, feedback_type: str, feedback_content: str = "") -> Trial:
        """Emit trial.feedback."""
        self._append(
            session,
            make_event(
                event_type="trial.feedback",
                session_id=session.session_id,
                student_id=session.student_id,
                unit_id=trial.unit_id,
                protocol_id=session.protocol_id,
                protocol_version=session.protocol_version,
                payload={
                    "trial_id": str(trial.trial_id),
                    "feedback_type": feedback_type,
                    "feedback_content": feedback_content,
                },
            ),
        )
        return trial

    def submit_trial(
        self,
        session: LearningSession,
        trial: Trial,
        response: Response,
        score: Score,
        monotonic_response_ns: int,
        feedback_type: str = "none",
        feedback_content: str = "",
    ) -> Trial:
        """Convenience method for a complete trial.

        Emits trial.start, trial.response, trial.score, and trial.feedback.
        """
        unit = self._units.get(trial.unit_id)
        self._emit_trial_start(session, trial, unit=unit)
        trial = self.submit_response(session, trial, response, monotonic_response_ns)
        trial = self.score_trial(session, trial, score)
        trial = self.give_feedback(session, trial, feedback_type, feedback_content)
        return trial

    # ------------------------------------------------------------------
    # State and recommendation
    # ------------------------------------------------------------------

    def get_state(self, student_id: UUID, unit_id: UUID) -> LearningState:
        """Derive state from the event stream, optionally using a cache."""
        if self.state_cache is not None:
            cached = self.state_cache.get(student_id, unit_id, self.transformation)
            if cached is not None:
                return cached
            state = self._recompute_state(student_id, unit_id)
            self.state_cache.put(student_id, unit_id, self.transformation, state)
            return state

        key = (student_id, unit_id)
        if key in self._states:
            return self._states[key]

        state = self._recompute_state(student_id, unit_id)
        self._states[key] = state
        return state

    def recommend(self, student: Student, units: list[LearningUnit], context: Optional[dict] = None) -> Recommendation:
        """Ask the scheduler for a recommendation."""
        unit_states = {unit.unit_id: self.get_state(student.student_id, unit.unit_id) for unit in units}
        return self.scheduler.recommend(student, unit_states, units, context or {})

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append(self, session: LearningSession, event: Event) -> None:
        """Validate event against the protocol and append it to the store."""
        if event.monotonic_ns == 0:
            event = replace(event, monotonic_ns=self._next_monotonic_ns())
        else:
            self._last_monotonic_ns = max(self._last_monotonic_ns, event.monotonic_ns)
        session_state = self._session_states.get(session.session_id)
        if session_state is None:
            session_state = self.experiment_engine.session_state(session_id=session.session_id)
        valid, reason = self.experiment_engine.validate_event(event, session_state)
        if not valid:
            deviation = self.experiment_engine.record_deviation(session, event, reason)
            self.store.append(deviation)
            self._session_states[session.session_id] = self.experiment_engine.session_state(
                session_id=session.session_id,
                events=list(self.store.read(session_id=session.session_id)),
            )
            raise ValueError(f"Protocol violation: {reason}")
        self.store.append(event)
        self._session_states[session.session_id] = self.experiment_engine.session_state(
            session_id=session.session_id,
            events=list(self.store.read(session_id=session.session_id)),
        )

    def _recompute_state(self, student_id: UUID, unit_id: UUID) -> LearningState:
        """Recompute state from the event stream."""
        events = self.store.read(student_id=student_id, unit_id=unit_id)
        state = self.transformation.initial_state(unit_id)
        for event in events:
            state = self.transformation.apply(state, event)
        return state

    def _update_state(self, student_id: UUID, unit_id: UUID) -> None:
        """Recompute state after a new event and update the cache."""
        state = self._recompute_state(student_id, unit_id)
        if self.state_cache is not None:
            self.state_cache.put(student_id, unit_id, self.transformation, state)
        else:
            self._states[(student_id, unit_id)] = state

    def get_event_stream(self, student_id: Optional[UUID] = None, session_id: Optional[UUID] = None, unit_id: Optional[UUID] = None) -> Any:
        """Return a read view of the event stream."""
        return self.store.read(student_id=student_id, session_id=session_id, unit_id=unit_id)
