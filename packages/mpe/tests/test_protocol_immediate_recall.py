"""Tests for the Immediate Recall protocol vertical slice (Phase 4C.1)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from mpe.cli import main
from mpe.cli_helpers import normalize_state_dict
from mpe.enums import SessionStatus
from mpe.event_store import InMemoryEventStore
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.fixture_minimal import (
    AdaptationRule,
    FixtureAsset,
    FixtureItem,
    ImmediateRecallFixture,
    make_minimal_fixture,
)
from mpe.protocol.immediate_recall import ImmediateRecallResult, run_immediate_recall_session
from mpe.protocol.summary import derive_protocol_summary
from mpe.replay import Replay


class ImmediateRecallRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = make_minimal_fixture()
        self.rule = AdaptationRule(repeat_cap=1, latency_bound=2.0)

    def _run(self, store: InMemoryEventStore | SQLiteEventStore) -> ImmediateRecallResult:
        return run_immediate_recall_session(
            store,
            fixture=self.fixture,
            rule=self.rule,
            learner_id="learner_001",
            random_seed="seed_0",
        )

    def test_successful_execution(self) -> None:
        result = self._run(InMemoryEventStore())
        self.assertEqual(result.state.session_status, SessionStatus.COMPLETED)
        self.assertTrue(result.state.terminal)
        self.assertEqual(len(result.item_outcomes), 3)  # alpha + beta + beta repeat

    def test_repeat_on_negative_confirmation(self) -> None:
        result = self._run(InMemoryEventStore())
        beta_outcomes = [o for o in result.item_outcomes if o.content_item_id == "item.beta"]
        self.assertEqual(len(beta_outcomes), 2)
        self.assertEqual(beta_outcomes[0].self_confirmation, "negative")
        self.assertEqual(beta_outcomes[1].self_confirmation, "negative")

    def test_no_repeat_on_positive_confirmation(self) -> None:
        result = self._run(InMemoryEventStore())
        alpha_outcomes = [o for o in result.item_outcomes if o.content_item_id == "item.alpha"]
        self.assertEqual(len(alpha_outcomes), 1)
        self.assertEqual(alpha_outcomes[0].self_confirmation, "positive")
        self.assertEqual(alpha_outcomes[0].repeats_used, 0)

    def test_repeat_cap_enforced(self) -> None:
        result = self._run(InMemoryEventStore())
        beta_trials = [
            e for e in result.events if e.event_type == "trial_created" and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)

    def test_deterministic_event_order(self) -> None:
        store1 = InMemoryEventStore()
        store2 = InMemoryEventStore()
        result1 = self._run(store1)
        result2 = self._run(store2)
        types1 = [e.event_type for e in result1.events]
        types2 = [e.event_type for e in result2.events]
        self.assertEqual(types1, types2)
        seqs1 = [e.session_sequence_number for e in result1.events]
        seqs2 = [e.session_sequence_number for e in result2.events]
        self.assertEqual(seqs1, list(range(1, len(seqs1) + 1)))
        self.assertEqual(seqs1, seqs2)

    def test_persistence_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            result1 = self._run(store1)

            store2 = SQLiteEventStore(path)
            session_id = result1.runtime.state.session_id
            assert session_id is not None
            events = store2.read(session_id)
            self.assertEqual(len(events), len(result1.events))
            self.assertEqual([e.event_type for e in events], [e.event_type for e in result1.events])

    def test_replay_equality(self) -> None:
        store = InMemoryEventStore()
        result = self._run(store)
        session_id = result.runtime.state.session_id
        assert session_id is not None
        replayed_state = Replay(store).replay(session_id)
        self.assertEqual(
            normalize_state_dict(result.state.as_dict()),
            normalize_state_dict(replayed_state.as_dict()),
        )

    def test_summary_derivation(self) -> None:
        result = self._run(InMemoryEventStore())
        summary = derive_protocol_summary(result.events, repeat_cap=self.rule.repeat_cap)
        self.assertEqual(summary.session_id, str(result.runtime.state.session_id))
        self.assertEqual(summary.fixture_id, "minimal")
        self.assertEqual(summary.protocol_id, self.fixture.protocol_version_id)
        self.assertEqual(summary.event_count, len(result.events))
        self.assertEqual(summary.item_count, 2)
        self.assertEqual(summary.total_repeats, 1)

        alpha = next(i for i in summary.items if i.content_item_id == "item.alpha")
        self.assertEqual(alpha.outcome, "positive")
        self.assertEqual(alpha.repeats_used, 0)

        beta = next(i for i in summary.items if i.content_item_id == "item.beta")
        self.assertEqual(beta.outcome, "unresolved")
        self.assertEqual(beta.repeats_used, 1)
        self.assertEqual(beta.self_confirmation, "negative")
        self.assertEqual(beta.latency, 5.0)

    def test_asset_version_pin_retained(self) -> None:
        result = self._run(InMemoryEventStore())
        ready_events = [e for e in result.events if e.event_type == "stimulus_ready"]
        self.assertTrue(ready_events)
        for event in ready_events:
            self.assertIn("asset_version", event.payload)
            self.assertIn("media_handle", event.payload)
            self.assertTrue(event.payload["media_handle"].startswith("fixture://"))
            self.assertIn("asset_role", event.payload)

    def test_eeg_observation_is_emitted(self) -> None:
        result = self._run(InMemoryEventStore())
        eeg_events = [
            e
            for e in result.events
            if e.event_type == "observation_received"
            and e.payload.get("observation_type") == "eeg_burst"
        ]
        self.assertTrue(eeg_events, "EEG observations must be emitted during the trial")
        for event in eeg_events:
            self.assertEqual(event.payload.get("provider_id"), "mock_eeg")
            self.assertIn("cognitive_load_index", event.payload.get("payload", {}))

    def test_low_quality_eeg_is_ignored(self) -> None:
        positive = self.fixture.items[0]
        bad_eeg_item = FixtureItem(
            content_item_id="item.bad_eeg",
            expected_relation=positive.expected_relation,
            self_confirmation="negative",
            latency=5.0,
            assets=positive.assets,
            eeg_load=0.9,
            eeg_quality_flags=["artifact"],
        )
        fixture = ImmediateRecallFixture(
            fixture_id="minimal",
            protocol_id=self.fixture.protocol_id,
            protocol_version_id=self.fixture.protocol_version_id,
            program_id=self.fixture.program_id,
            program_version_id=self.fixture.program_version_id,
            task_definition_id=self.fixture.task_definition_id,
            block_id=self.fixture.block_id,
            block_type=self.fixture.block_type,
            items=[bad_eeg_item],
        )
        result = run_immediate_recall_session(
            InMemoryEventStore(),
            fixture=fixture,
            rule=AdaptationRule(repeat_cap=0, latency_bound=2.0),
        )
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        # A single incorrect sample with poor-signal EEG: behavioral load is 1.0,
        # but hysteresis requires two consecutive high samples to leave baseline.
        # The discarded EEG must not be the sole cause of any intervention.
        self.assertTrue(decisions)
        self.assertEqual(decisions[-1].payload["proposed_value"], 10.0)

    def test_eeg_does_not_override_behavior(self) -> None:
        positive = self.fixture.items[0]
        good_behavior_high_eeg = FixtureItem(
            content_item_id="item.good_behavior_high_eeg",
            expected_relation=positive.expected_relation,
            self_confirmation="positive",
            latency=0.5,
            assets=positive.assets,
            eeg_load=0.9,
            eeg_quality_flags=[],
        )
        fixture = ImmediateRecallFixture(
            fixture_id="minimal",
            protocol_id=self.fixture.protocol_id,
            protocol_version_id=self.fixture.protocol_version_id,
            program_id=self.fixture.program_id,
            program_version_id=self.fixture.program_version_id,
            task_definition_id=self.fixture.task_definition_id,
            block_id=self.fixture.block_id,
            block_type=self.fixture.block_type,
            items=[good_behavior_high_eeg, good_behavior_high_eeg],
        )
        result = run_immediate_recall_session(
            InMemoryEventStore(),
            fixture=fixture,
            rule=AdaptationRule(repeat_cap=0, latency_bound=2.0),
        )
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        self.assertTrue(decisions)
        # Behavioral correctness must keep the deadline at baseline even when EEG
        # reports high cognitive load.
        for decision in decisions:
            self.assertEqual(decision.payload["proposed_value"], 10.0)
            self.assertEqual(decision.payload["decision"], "NO_CHANGE_INSUFFICIENT_EVIDENCE")

    def test_adaptation_source_recorded(self) -> None:
        result = self._run(InMemoryEventStore())
        beta_trials = [
            e for e in result.events
            if e.event_type == "trial_created" and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        initial, repeat = beta_trials
        self.assertEqual(initial.payload.get("repeat_count"), 0)
        self.assertNotIn("adaptation_source", initial.payload)
        self.assertEqual(repeat.payload.get("repeat_count"), 1)
        self.assertEqual(repeat.payload.get("cap"), 1)
        self.assertEqual(repeat.payload.get("adaptation_source"), "behavior")

    def _fixture_with_beta(self, beta: FixtureItem) -> ImmediateRecallFixture:
        alpha = self.fixture.items[0]
        return ImmediateRecallFixture(
            fixture_id="minimal",
            protocol_id=self.fixture.protocol_id,
            protocol_version_id=self.fixture.protocol_version_id,
            program_id=self.fixture.program_id,
            program_version_id=self.fixture.program_version_id,
            task_definition_id=self.fixture.task_definition_id,
            block_id=self.fixture.block_id,
            block_type=self.fixture.block_type,
            items=[alpha, beta],
        )

    def test_negative_normal_latency_causes_repeat(self) -> None:
        # Negative self-confirmation with normal latency still triggers the bounded repeat.
        beta = FixtureItem(
            content_item_id="item.beta",
            expected_relation="associate(item.beta.prompt, item.beta.target)",
            self_confirmation="negative",
            latency=0.5,
            assets={
                "prompt": FixtureAsset("item.beta.prompt", "prompt", "fixture://item.beta/prompt", "v1.0.0"),
                "confirmation": FixtureAsset("item.beta.confirmation", "confirmation", "fixture://item.beta/confirmation", "v1.0.0"),
            },
        )
        fixture = self._fixture_with_beta(beta)
        result = run_immediate_recall_session(InMemoryEventStore(), fixture=fixture, rule=self.rule)
        beta_trials = [
            e for e in result.events
            if e.event_type == "trial_created" and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        repeat_trial = beta_trials[1]
        self.assertEqual(repeat_trial.payload.get("adaptation_source"), "behavior")
        self.assertEqual(repeat_trial.payload.get("cap"), 1)
        summary = derive_protocol_summary(result.events, repeat_cap=self.rule.repeat_cap)
        beta_summary = next(i for i in summary.items if i.content_item_id == "item.beta")
        self.assertEqual(beta_summary.outcome, "unresolved")
        self.assertEqual(beta_summary.self_confirmation, "negative")

    def test_positive_slow_latency_does_not_change_correctness(self) -> None:
        # Positive self-confirmation with slow latency triggers a repeat, but the
        # outcome remains positive and is never marked incorrect.
        beta = FixtureItem(
            content_item_id="item.beta",
            expected_relation="associate(item.beta.prompt, item.beta.target)",
            self_confirmation="positive",
            latency=5.0,
            assets={
                "prompt": FixtureAsset("item.beta.prompt", "prompt", "fixture://item.beta/prompt", "v1.0.0"),
                "confirmation": FixtureAsset("item.beta.confirmation", "confirmation", "fixture://item.beta/confirmation", "v1.0.0"),
            },
        )
        fixture = self._fixture_with_beta(beta)
        result = run_immediate_recall_session(InMemoryEventStore(), fixture=fixture, rule=self.rule)
        beta_trials = [
            e for e in result.events
            if e.event_type == "trial_created" and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        repeat_trial = beta_trials[1]
        self.assertEqual(repeat_trial.payload.get("adaptation_source"), "latency")

        beta_evaluations = [
            e for e in result.events
            if e.event_type == "evaluation_completed"
            and e.payload.get("expected_content_item_id") == "item.beta"
        ]
        for ev in beta_evaluations:
            self.assertEqual(ev.payload.get("answer_status"), "correct")

        summary = derive_protocol_summary(result.events, repeat_cap=self.rule.repeat_cap)
        beta_summary = next(i for i in summary.items if i.content_item_id == "item.beta")
        self.assertEqual(beta_summary.outcome, "positive")
        self.assertEqual(beta_summary.self_confirmation, "positive")
        self.assertEqual(beta_summary.repeats_used, 1)

    def test_latency_proxy_triggers_repeat(self) -> None:
        # Slow positive response triggers one bounded repeat, but no further repeats.
        beta = FixtureItem(
            content_item_id="item.beta",
            expected_relation="associate(item.beta.prompt, item.beta.target)",
            self_confirmation="positive",
            latency=5.0,
            assets={
                "prompt": FixtureAsset("item.beta.prompt", "prompt", "fixture://item.beta/prompt", "v1.0.0"),
                "confirmation": FixtureAsset("item.beta.confirmation", "confirmation", "fixture://item.beta/confirmation", "v1.0.0"),
            },
        )
        fixture = self._fixture_with_beta(beta)
        result = run_immediate_recall_session(InMemoryEventStore(), fixture=fixture, rule=self.rule)
        beta_outcomes = [o for o in result.item_outcomes if o.content_item_id == "item.beta"]
        self.assertEqual(len(beta_outcomes), 2)
        self.assertEqual(beta_outcomes[0].self_confirmation, "positive")
        self.assertEqual(beta_outcomes[1].self_confirmation, "positive")

    def test_adaptation_changes_next_executable_trial(self) -> None:
        # A negative behavioral observation re-queues the same item as the next trial.
        result = self._run(InMemoryEventStore())
        trials = [e for e in result.events if e.event_type == "trial_created"]
        self.assertEqual(
            [e.payload["content_item_ids"] for e in trials],
            [["item.alpha"], ["item.beta"], ["item.beta"]],
        )
        initial_beta, repeat_beta = [
            e for e in trials if e.payload["content_item_ids"] == ["item.beta"]
        ]
        self.assertNotIn("adaptation_source", initial_beta.payload)
        self.assertEqual(repeat_beta.payload["repeat_count"], 1)
        self.assertEqual(repeat_beta.payload["cap"], 1)
        self.assertEqual(repeat_beta.payload["adaptation_source"], "behavior")

    def test_adapted_session_is_replayable(self) -> None:
        # Adaptation decisions are persisted and reproducible by replay.
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            result1 = self._run(store1)
            session_id = result1.runtime.state.session_id
            assert session_id is not None

            store2 = SQLiteEventStore(path)
            replayed = Replay(store2).replay(session_id)
            events2 = store2.read(session_id)
            self.assertEqual(replayed.session_status, SessionStatus.COMPLETED)
            beta_trials = [
                e for e in events2
                if e.event_type == "trial_created"
                and e.payload.get("content_item_ids") == ["item.beta"]
            ]
            self.assertEqual(len(beta_trials), 2)
            self.assertEqual(beta_trials[1].payload["adaptation_source"], "behavior")

    def _make_adaptation_item(
        self,
        item_id: str,
        self_confirmation: str,
        latency: float,
        eeg_load: float = 0.0,
        eeg_quality_flags: list[str] | None = None,
    ) -> FixtureItem:
        if eeg_quality_flags is None:
            eeg_quality_flags = []
        return FixtureItem(
            content_item_id=item_id,
            expected_relation=f"associate({item_id}.prompt, {item_id}.target)",
            self_confirmation=self_confirmation,
            latency=latency,
            assets={
                "prompt": FixtureAsset(
                    f"{item_id}.prompt",
                    "prompt",
                    f"fixture://{item_id}/prompt",
                    "v1.0.0",
                ),
                "confirmation": FixtureAsset(
                    f"{item_id}.confirmation",
                    "confirmation",
                    f"fixture://{item_id}/confirmation",
                    "v1.0.0",
                ),
            },
            eeg_load=eeg_load,
            eeg_quality_flags=eeg_quality_flags,
        )

    def test_response_deadline_escalates_and_recovers(self) -> None:
        """Sustained deterioration extends the next response window; sustained recovery
        restores it to baseline in gradual steps.
        """
        fixture = ImmediateRecallFixture(
            fixture_id="adaptation-fixture",
            protocol_id=self.fixture.protocol_id,
            protocol_version_id=self.fixture.protocol_version_id,
            program_id=self.fixture.program_id,
            program_version_id=self.fixture.program_version_id,
            task_definition_id=self.fixture.task_definition_id,
            block_id=self.fixture.block_id,
            block_type=self.fixture.block_type,
            items=[
                self._make_adaptation_item("item.1", "positive", 0.5),
                self._make_adaptation_item("item.2", "negative", 5.0, eeg_load=0.8),
                self._make_adaptation_item("item.3", "negative", 5.0, eeg_load=0.8),
                self._make_adaptation_item("item.4", "negative", 5.0, eeg_load=0.8),
                self._make_adaptation_item("item.5", "positive", 0.5),
                self._make_adaptation_item("item.6", "positive", 0.5),
                self._make_adaptation_item("item.7", "positive", 0.5),
                self._make_adaptation_item("item.8", "positive", 0.5),
                self._make_adaptation_item("item.9", "positive", 0.5),
            ],
        )
        result = run_immediate_recall_session(
            InMemoryEventStore(),
            fixture=fixture,
            rule=AdaptationRule(repeat_cap=0, latency_bound=2.0),
        )
        durations = [
            e.payload["deadline_at"] - e.payload["opened_at"]
            for e in result.events
            if e.event_type == "response_window_opened"
        ]
        # Baseline -> no change for the first two trials, then assistance grows.
        self.assertEqual(durations[0], 10.0)
        self.assertEqual(durations[1], 10.0)
        self.assertGreater(durations[3], durations[2])
        self.assertGreaterEqual(durations[4], durations[3])
        # One good response is not enough to reverse assistance (hysteresis).
        self.assertGreaterEqual(durations[5], durations[4])
        # Sustained recovery gradually restores baseline.
        self.assertLess(durations[6], durations[5])
        self.assertEqual(durations[-1], 10.0)

        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        apply_decisions = [d for d in decisions if d.payload["decision"] == "APPLY"]
        no_change_decisions = [
            d for d in decisions if d.payload["decision"] == "NO_CHANGE_INSUFFICIENT_EVIDENCE"
        ]
        self.assertTrue(apply_decisions)
        self.assertTrue(no_change_decisions)
        # The final baseline restoration is explicit.
        self.assertEqual(decisions[-1].payload["proposed_value"], 10.0)

    def test_interrupted_recovery_returns_to_assistance(self) -> None:
        """A good response during recovery is not enough; a new deterioration
        re-enters the elevated assistance regime.
        """
        fixture = ImmediateRecallFixture(
            fixture_id="adaptation-fixture",
            protocol_id=self.fixture.protocol_id,
            protocol_version_id=self.fixture.protocol_version_id,
            program_id=self.fixture.program_id,
            program_version_id=self.fixture.program_version_id,
            task_definition_id=self.fixture.task_definition_id,
            block_id=self.fixture.block_id,
            block_type=self.fixture.block_type,
            items=[
                self._make_adaptation_item("item.1", "negative", 5.0, eeg_load=0.8),
                self._make_adaptation_item("item.2", "negative", 5.0, eeg_load=0.8),
                self._make_adaptation_item("item.3", "positive", 0.5),
                self._make_adaptation_item("item.4", "negative", 5.0, eeg_load=0.8),
            ],
        )
        result = run_immediate_recall_session(
            InMemoryEventStore(),
            fixture=fixture,
            rule=AdaptationRule(repeat_cap=0, latency_bound=2.0),
        )
        durations = [
            e.payload["deadline_at"] - e.payload["opened_at"]
            for e in result.events
            if e.event_type == "response_window_opened"
        ]
        # Trial 1 baseline, trial 2 still baseline (one sample), trial 3 assistance.
        self.assertEqual(durations[0], 10.0)
        self.assertEqual(durations[1], 10.0)
        self.assertGreater(durations[2], durations[1])
        # The brief good response on item.3 should not drop the deadline yet;
        # the renewed deterioration on item.4 keeps assistance elevated.
        self.assertGreaterEqual(durations[3], durations[2])


class ImmediateRecallCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = Path(self._td.name) / "events.db"

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue().strip(), err.getvalue().strip()

    def test_cli_run_success(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "run-immediate-recall", "--format", "json"]
        )
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["fixture_id"], "minimal")
        self.assertEqual(result["item_count"], 2)
        self.assertEqual(result["total_repeats"], 1)
        self.assertEqual(result["unresolved_count"], 1)

    def test_cli_show_summary(self) -> None:
        session_id = "ir-cli-session"
        code, out, _err = self._run(
            [
                "--store-path",
                str(self.store_path),
                "run-immediate-recall",
                "--session-id",
                session_id,
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0)

        code, out, err = self._run(
            [
                "--store-path",
                str(self.store_path),
                "show-protocol-summary",
                session_id,
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["fixture_id"], "minimal")
        self.assertEqual(result["total_repeats"], 1)

    def test_cli_unknown_session_exits_three(self) -> None:
        self._run(["--store-path", str(self.store_path), "run-immediate-recall"])
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "show-protocol-summary", "missing-session"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(out, "")
        self.assertIn("missing-session", err)

    def test_cli_invalid_session_id_exits_two(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "show-protocol-summary", ""]
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("invalid session ID", err)

    def test_cli_directory_path_exits_usage(self) -> None:
        dir_path = Path(self._td.name) / "a_directory"
        dir_path.mkdir()
        code, out, err = self._run(
            ["--store-path", str(dir_path), "run-immediate-recall"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("directory", err)

    def test_cli_json_success_single_document(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "run-immediate-recall", "--format", "json"]
        )
        self.assertEqual(code, 0)
        self.assertIsNotNone(json.loads(out))
        self.assertNotIn("Traceback", out)
        self.assertNotIn("error:", out)


class ImmediateRecallProcessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = Path(self._td.name) / "events.db"

    def _run_process(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "mpe", "--store-path", str(self.store_path)] + argv
        env = dict(os.environ)
        env["PYTHONPATH"] = "packages/mpe/src"
        repo_root = Path(__file__).resolve().parents[3]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root), env=env)

    def test_python_mpe_invocation(self) -> None:
        run = self._run_process(["run-immediate-recall", "--format", "json"])
        self.assertEqual(run.returncode, 0)
        result = json.loads(run.stdout)
        self.assertEqual(result["item_count"], 2)

        replay = self._run_process(["show-protocol-summary", result["session_id"], "--format", "json"])
        self.assertEqual(replay.returncode, 0)
        summary = json.loads(replay.stdout)
        self.assertEqual(summary["total_repeats"], 1)


if __name__ == "__main__":
    unittest.main()
