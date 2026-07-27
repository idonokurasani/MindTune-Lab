"""Tests for session provenance (SR-M1 WP-3, ADR-0001 sec. 2.8)."""

from __future__ import annotations

import unittest
from unittest import mock

from mpe.aggregates import RuntimeState
from mpe.errors import IllegalStateTransitionError, ValidationError
from mpe.event_store import InMemoryEventStore
from mpe.events import Event
from mpe.protocol.recognition import run_recognition_session
from mpe.protocol.summary import ProtocolSummary
from mpe.protocol.summary_recognition import (
    derive_recognition_summary,
    derive_recognition_summary_legacy,
)
from mpe.protocol.summary_walk import walk_session, walk_session_legacy
from mpe.provenance import (
    PROVENANCE_RECORDED,
    PROVENANCE_UNAVAILABLE_LEGACY,
    REVISION_ENVIRONMENT_VARIABLE,
    REVISION_SOURCE_ENVIRONMENT,
    REVISION_SOURCE_UNKNOWN,
    ProvenanceReference,
    ResolvedRevision,
    resolve_software_revision,
)
from mpe.providers import (
    MockDomainNormalizer,
    MockEvaluator,
    MockKeyboardObservationProvider,
    MockRenderer,
    MockResponseInterpreter,
    MockScheduler,
    ProviderSet,
)
from mpe.runtime import Runtime
from mpe.types import EventID, ProtocolVersionID, make_id

RESOLVERS = "mpe.provenance"


def providers() -> ProviderSet:
    return ProviderSet(
        renderer=MockRenderer(),
        observation=MockKeyboardObservationProvider(),
        interpreter=MockResponseInterpreter(),
        normalizer=MockDomainNormalizer(),
        evaluator=MockEvaluator(),
        scheduler=MockScheduler(),
    )


def legacy_stream() -> list[Event]:
    """A historical schema-1.1 stream: no digests, no provenance event."""
    store = InMemoryEventStore()
    runtime = Runtime(store, providers())
    runtime.create_session(
        program_version_id="program_v1",
        protocol_version_id=ProtocolVersionID("protocol_v1"),
        learner_id="learner_1",
    )
    runtime.start_session()
    runtime.complete_session()
    events = store.read(runtime.state.session_id)
    return [
        Event(**{**event.as_dict(), "schema_version": "1.1"})
        for event in events
        if event.event_type != "session_provenance_recorded"
    ]


class RevisionResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        resolve_software_revision.cache_clear()
        self.addCleanup(resolve_software_revision.cache_clear)

    def test_environment_beats_package_metadata_and_git(self) -> None:
        with mock.patch.dict("os.environ", {REVISION_ENVIRONMENT_VARIABLE: "abc123"}):
            with mock.patch(f"{RESOLVERS}._from_build_metadata", return_value=None):
                resolved = resolve_software_revision()
        self.assertEqual(resolved.revision, "abc123")
        self.assertEqual(resolved.source, REVISION_SOURCE_ENVIRONMENT)

    def test_build_metadata_beats_the_environment(self) -> None:
        stamped = ResolvedRevision("built-sha", "build_metadata")
        with mock.patch.dict("os.environ", {REVISION_ENVIRONMENT_VARIABLE: "abc123"}):
            with mock.patch(f"{RESOLVERS}._from_build_metadata", return_value=stamped):
                resolved = resolve_software_revision()
        self.assertEqual(resolved.source, "build_metadata")

    def test_unresolvable_revision_is_an_explicit_unknown(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with (
                mock.patch(f"{RESOLVERS}._from_build_metadata", return_value=None),
                mock.patch(f"{RESOLVERS}._from_package_metadata", return_value=None),
                mock.patch(f"{RESOLVERS}._from_git", return_value=None),
            ):
                resolved = resolve_software_revision()
        self.assertIsNone(resolved.revision)
        self.assertEqual(resolved.source, REVISION_SOURCE_UNKNOWN)

    def test_resolution_never_raises(self) -> None:
        with mock.patch(f"{RESOLVERS}._from_build_metadata", side_effect=OSError("boom")):
            resolved = resolve_software_revision()
        self.assertIsInstance(resolved, ResolvedRevision)

    def test_git_is_never_consulted_when_an_earlier_source_answers(self) -> None:
        with mock.patch.dict("os.environ", {REVISION_ENVIRONMENT_VARIABLE: "abc123"}):
            with (
                mock.patch(f"{RESOLVERS}._from_build_metadata", return_value=None),
                mock.patch(f"{RESOLVERS}._from_git") as from_git,
            ):
                resolve_software_revision()
        from_git.assert_not_called()


class ProvenanceReferenceTests(unittest.TestCase):
    def test_recorded_requires_an_event_id(self) -> None:
        with self.assertRaises(ValidationError):
            ProvenanceReference(PROVENANCE_RECORDED, None, "1.2")

    def test_recorded_is_not_permitted_for_schema_11(self) -> None:
        with self.assertRaises(ValidationError):
            ProvenanceReference(PROVENANCE_RECORDED, make_id(EventID), "1.1")

    def test_unavailable_legacy_must_not_carry_an_event_id(self) -> None:
        with self.assertRaises(ValidationError):
            ProvenanceReference(PROVENANCE_UNAVAILABLE_LEGACY, make_id(EventID), "1.1")

    def test_unavailable_legacy_is_not_permitted_for_schema_12(self) -> None:
        with self.assertRaises(ValidationError):
            ProvenanceReference(PROVENANCE_UNAVAILABLE_LEGACY, None, "1.2")

    def test_there_is_no_third_status(self) -> None:
        with self.assertRaises(ValidationError):
            ProvenanceReference("none", None, "1.2")

    def test_the_two_valid_cases_serialize(self) -> None:
        event_id = make_id(EventID)
        self.assertEqual(
            ProvenanceReference.recorded(event_id, "1.2").as_dict(),
            {"provenance_status": "recorded", "provenance_event_id": str(event_id)},
        )
        self.assertEqual(
            ProvenanceReference.unavailable_legacy("1.1").as_dict(),
            {"provenance_status": "unavailable_legacy", "provenance_event_id": None},
        )


class RuntimeProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryEventStore()
        self.runtime = Runtime(self.store, providers())

    def _create(self, **kwargs: object) -> None:
        self.runtime.create_session(
            program_version_id="program_v1",
            protocol_version_id=ProtocolVersionID("protocol_v1"),
            learner_id="learner_1",
            **kwargs,  # type: ignore[arg-type]
        )

    def test_provenance_occupies_sequence_two(self) -> None:
        self._create()
        events = self.store.read(self.runtime.state.session_id)
        self.assertEqual(events[1].event_type, "session_provenance_recorded")
        self.assertEqual(events[1].session_sequence_number, 2)

    def test_no_event_can_be_emitted_before_provenance(self) -> None:
        self._create(record_provenance=False)
        with self.assertRaises(IllegalStateTransitionError):
            self.runtime.start_session()

    def test_provenance_cannot_be_recorded_twice(self) -> None:
        self._create()
        with self.assertRaises(IllegalStateTransitionError):
            self.runtime.record_provenance()

    def test_unsourced_fields_are_explicit_nulls(self) -> None:
        self._create()
        payload = self.store.read(self.runtime.state.session_id)[1].payload
        for field_name in (
            "curriculum_id",
            "curriculum_version",
            "experimental_condition",
            "stimulus_set_id",
            "scoring_policy_version",
            "rt_policy_version",
            "signal_processing_policy_version",
        ):
            self.assertIn(field_name, payload)
            self.assertIsNone(payload[field_name])

    def test_provider_versions_are_the_verified_map(self) -> None:
        self._create()
        payload = self.store.read(self.runtime.state.session_id)[1].payload
        self.assertEqual(payload["provider_versions"], providers().version_map())

    def test_the_software_revision_records_its_source(self) -> None:
        self._create()
        revision = self.store.read(self.runtime.state.session_id)[1].payload["software_revision"]
        self.assertIn("revision", revision)
        self.assertIn(
            revision["source"],
            {"build_metadata", "environment", "package_metadata", "git", "unknown"},
        )

    def test_events_carry_the_writer_revision(self) -> None:
        self._create()
        expected = resolve_software_revision().revision
        for event in self.store.read(self.runtime.state.session_id):
            self.assertEqual(event.writer_revision, expected)

    def test_state_exposes_the_provenance_record(self) -> None:
        self._create()
        state: RuntimeState = self.runtime.state
        self.assertIsNotNone(state.provenance_event_id)
        self.assertEqual(state.as_dict()["provenance_event_id"], state.provenance_event_id)

    def test_the_first_trial_event_names_the_provenance_event(self) -> None:
        store = InMemoryEventStore()
        result = run_recognition_session(store)
        events = store.read(result.state.session_id)
        provenance_id = events[1].event_id
        first_trial = next(e for e in events if e.event_type == "trial_created")
        self.assertIn(provenance_id, first_trial.provenance)


class DerivedResultProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryEventStore()
        self.result = run_recognition_session(self.store)
        self.events = self.store.read(self.result.state.session_id)

    def test_a_schema_12_result_names_its_provenance_event(self) -> None:
        summary = derive_recognition_summary(self.events)
        assert summary.provenance is not None
        self.assertEqual(summary.provenance.status, PROVENANCE_RECORDED)
        self.assertEqual(summary.as_dict()["provenance_event_id"], str(self.events[1].event_id))

    def test_a_schema_12_stream_without_provenance_yields_no_result(self) -> None:
        stripped = [
            event for event in self.events if event.event_type != "session_provenance_recorded"
        ]
        with self.assertRaises(ValidationError):
            derive_recognition_summary(stripped)

    def test_the_normal_api_refuses_a_legacy_stream(self) -> None:
        with self.assertRaises(ValidationError):
            walk_session(legacy_stream())

    def test_the_legacy_api_refuses_a_schema_12_stream(self) -> None:
        with self.assertRaises(ValidationError):
            walk_session_legacy(self.events)

    def test_a_legacy_result_declares_unavailable_provenance(self) -> None:
        summary = derive_recognition_summary_legacy(legacy_stream())
        assert summary.provenance is not None
        self.assertEqual(summary.provenance.status, PROVENANCE_UNAVAILABLE_LEGACY)
        self.assertIsNone(summary.as_dict()["provenance_event_id"])

    def test_no_result_is_silently_unprovenanced(self) -> None:
        """Every constructible result declares one of the two cases."""
        recorded = derive_recognition_summary(self.events).as_dict()
        legacy = derive_recognition_summary_legacy(legacy_stream()).as_dict()
        for result in (recorded, legacy):
            self.assertIn(
                result["provenance_status"],
                {PROVENANCE_RECORDED, PROVENANCE_UNAVAILABLE_LEGACY},
            )

    def test_a_summary_without_a_reference_is_only_reachable_by_construction(
        self,
    ) -> None:
        """The dataclass default exists for compatibility, not for the API."""
        bare = ProtocolSummary(
            session_id="s",
            protocol_id=None,
            fixture_id=None,
            status=None,
            event_count=0,
            item_count=0,
            completed_item_count=0,
            unresolved_count=0,
            total_repeats=0,
        )
        self.assertIsNone(bare.provenance)
        self.assertNotIn("provenance_status", bare.as_dict())


if __name__ == "__main__":
    unittest.main()
