"""Property-based determinism and interchange invariants (SR-M1 WP-4).

These properties are the ones reproducibility rests on: replay is a pure fold
over the history, the canonical encoder is stable, and a stream survives a
round trip through the supported interchange unchanged.
"""

from __future__ import annotations

import json
import unittest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from mpe.event_store import InMemoryEventStore
from mpe.integrity import (
    INTEGRITY_VERIFIED,
    canonical_digest_bytes,
    canonical_record_bytes,
    compute_content_digest,
    verify_stream,
)
from mpe.persistence.interchange import (
    event_from_record,
    export_stream,
    import_stream,
)
from mpe.protocol.recognition import run_recognition_session
from mpe.protocol.summary_recognition import derive_recognition_summary
from mpe.replay import Replay
from mpe.types import SessionID

PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

learner_ids = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=12
)
seeds = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=12
)


def _session(learner_id: str, seed: str) -> tuple[InMemoryEventStore, SessionID]:
    store = InMemoryEventStore()
    result = run_recognition_session(store, learner_id=learner_id, random_seed=seed)
    session_id = result.state.session_id
    assert session_id is not None
    return store, session_id


class DeterminismProperties(unittest.TestCase):
    @PROPERTY_SETTINGS
    @given(learner_ids, seeds)
    def test_replay_reproduces_live_state(self, learner_id: str, seed: str) -> None:
        store, session_id = _session(learner_id, seed)
        first = Replay(store).replay(session_id).as_dict()
        second = Replay(store).replay(session_id).as_dict()
        self.assertEqual(first, second)

    @PROPERTY_SETTINGS
    @given(learner_ids, seeds)
    def test_the_chain_verifies_and_provenance_is_second(self, learner_id: str, seed: str) -> None:
        store, session_id = _session(learner_id, seed)
        events = store.read(session_id)
        self.assertEqual(verify_stream(events), INTEGRITY_VERIFIED)
        self.assertEqual(events[1].event_type, "session_provenance_recorded")
        self.assertEqual(
            [e.session_sequence_number for e in events],
            list(range(1, len(events) + 1)),
        )

    @PROPERTY_SETTINGS
    @given(learner_ids, seeds)
    def test_the_canonical_encoders_are_stable_and_distinct(
        self, learner_id: str, seed: str
    ) -> None:
        store, session_id = _session(learner_id, seed)
        for event in store.read(session_id):
            self.assertEqual(canonical_digest_bytes(event), canonical_digest_bytes(event))
            self.assertEqual(canonical_record_bytes(event), canonical_record_bytes(event))
            self.assertNotEqual(canonical_digest_bytes(event), canonical_record_bytes(event))
            self.assertEqual(compute_content_digest(event), event.content_digest)

    @PROPERTY_SETTINGS
    @given(learner_ids, seeds)
    def test_a_record_round_trip_preserves_the_event(self, learner_id: str, seed: str) -> None:
        store, session_id = _session(learner_id, seed)
        for event in store.read(session_id):
            rebuilt = event_from_record(json.loads(canonical_record_bytes(event)))
            self.assertEqual(rebuilt, event)

    @PROPERTY_SETTINGS
    @given(learner_ids, seeds)
    def test_rebuild_from_empty_preserves_state_and_summary(
        self, learner_id: str, seed: str
    ) -> None:
        store, session_id = _session(learner_id, seed)
        exported = list(export_stream(store, session_id))

        target = InMemoryEventStore()
        import_stream(target, exported)

        self.assertEqual(list(export_stream(target, session_id)), exported)
        self.assertEqual(
            Replay(target).replay(session_id).as_dict(),
            Replay(store).replay(session_id).as_dict(),
        )
        self.assertEqual(
            derive_recognition_summary(target.read(session_id)).as_dict(),
            derive_recognition_summary(store.read(session_id)).as_dict(),
        )


if __name__ == "__main__":
    unittest.main()
