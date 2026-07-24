"""State machine transition tests."""

from __future__ import annotations

import unittest

from mpe.aggregates import RuntimeState
from mpe.enums import SessionStatus
from mpe.errors import IllegalStateTransitionError
from mpe.events import Event
from mpe.types import (
    BlockID,
    EventID,
    ProgramVersionID,
    ProtocolVersionID,
    SessionID,
    TrialID,
    make_id,
)


class StateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session_id = SessionID(str(make_id(SessionID)))
        self.protocol_version_id = ProtocolVersionID(str(make_id(ProtocolVersionID)))
        self.state = RuntimeState()

    def _event(self, event_type: str, seq: int, payload: dict, trial_id: TrialID | None = None, block_id: BlockID | None = None, provenance: list[EventID] | None = None) -> Event:
        return Event(
            event_id=make_id(EventID),
            event_type=event_type,
            schema_version="1.1",
            session_id=self.session_id,
            session_sequence_number=seq,
            protocol_version_id=self.protocol_version_id,
            timestamp=1.0 + (seq - 1) * 0.1,
            component="runtime",
            component_version="1.0.0",
            payload=payload,
            trial_id=trial_id,
            block_id=block_id,
            provenance=provenance or [],
        )

    def test_session_lifecycle_valid(self) -> None:
        self.state.apply(self._event("session_created", 1, {
            "session_id": str(self.session_id),
            "program_version_id": str(ProgramVersionID("pv")),
            "protocol_version_id": str(self.protocol_version_id),
            "learner_id": "l",
        }))
        self.assertEqual(self.state.session_status, SessionStatus.CREATED)

        self.state.apply(self._event("session_started", 2, {
            "session_id": str(self.session_id),
            "program_version_id": str(ProgramVersionID("pv")),
            "protocol_version_id": str(self.protocol_version_id),
            "learner_id": "l",
            "random_seed": "s",
        }))
        self.assertEqual(self.state.session_status, SessionStatus.STARTED)

        self.state.apply(self._event("session_completed", 3, {
            "session_id": str(self.session_id),
            "completed_at": 2.0,
        }))
        self.assertEqual(self.state.session_status, SessionStatus.COMPLETED)
        self.assertTrue(self.state.terminal)

    def test_session_completed_from_created_is_illegal(self) -> None:
        self.state.apply(self._event("session_created", 1, {
            "session_id": str(self.session_id),
            "program_version_id": str(ProgramVersionID("pv")),
            "protocol_version_id": str(self.protocol_version_id),
            "learner_id": "l",
        }))
        with self.assertRaises(IllegalStateTransitionError):
            self.state.apply(self._event("session_completed", 2, {
                "session_id": str(self.session_id),
                "completed_at": 2.0,
            }))

    def test_captured_response_without_window_is_illegal(self) -> None:
        self.state.apply(self._event("session_created", 1, {
            "session_id": str(self.session_id),
            "program_version_id": str(ProgramVersionID("pv")),
            "protocol_version_id": str(self.protocol_version_id),
            "learner_id": "l",
        }))
        with self.assertRaises(IllegalStateTransitionError):
            self.state.apply(self._event("captured_response_created", 2, {
                "captured_response_id": "cr",
                "response_window_id": "rw",
                "observation_ids": ["o"],
                "response_mode": "typed",
                "captured_payload": "x",
                "captured_at": 1.5,
            }))

    def test_evaluation_without_response_window_is_illegal(self) -> None:
        tid = TrialID(str(make_id(TrialID)))
        self.state.apply(self._event("session_created", 1, {
            "session_id": str(self.session_id),
            "program_version_id": str(ProgramVersionID("pv")),
            "protocol_version_id": str(self.protocol_version_id),
            "learner_id": "l",
        }))
        self.state.apply(self._event("trial_created", 2, {
            "trial_id": str(tid),
            "session_id": str(self.session_id),
            "trial_index": 1,
            "task_definition_id": "td",
            "content_item_ids": ["c"],
            "response_requirement": "required",
        }))
        with self.assertRaises(IllegalStateTransitionError):
            self.state.apply(self._event("evaluation_completed", 3, {
                "evaluation_id": "e",
                "trial_id": str(tid),
                "evaluator_id": "mock_evaluator",
                "evaluator_version": "1.0.0",
                "domain_normalized_response_id": "dnr",
                "expected_content_item_id": "c",
                "answer_status": "correct",
                "evaluation_status": "completed",
            }, trial_id=tid))
