"""Tests for the Recognition protocol Gate 1 implementation (Phase 4C.2)."""

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
from mpe.enums import AnswerStatus, SessionStatus
from mpe.event_store import InMemoryEventStore
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.fixture_minimal import AdaptationRule
from mpe.protocol.fixture_recognition import (
    FixtureAsset,
    RecognitionFixture,
    RecognitionFixtureItem,
    make_minimal_recognition_fixture,
)
from mpe.protocol.recognition import RecognitionResult, run_recognition_session
from mpe.protocol.summary_recognition import derive_recognition_summary
from mpe.replay import Replay

REPO_ROOT = Path(__file__).resolve().parents[3]


class RecognitionRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = make_minimal_recognition_fixture()
        self.rule = AdaptationRule(repeat_cap=1, latency_bound=2.0)

    def _run(self, store: InMemoryEventStore | SQLiteEventStore) -> RecognitionResult:
        return run_recognition_session(
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
        # alpha + beta + beta repeat
        self.assertEqual(len(result.item_outcomes), 3)

    def test_choice_correctness_determined_by_selected_choice(self) -> None:
        result = self._run(InMemoryEventStore())
        alpha_outcomes = [o for o in result.item_outcomes if o.content_item_id == "item.alpha"]
        self.assertEqual(len(alpha_outcomes), 1)
        self.assertEqual(alpha_outcomes[0].answer_status, AnswerStatus.CORRECT.value)
        self.assertEqual(
            alpha_outcomes[0].selected_choice_index, alpha_outcomes[0].correct_choice_index
        )

        beta_outcomes = [o for o in result.item_outcomes if o.content_item_id == "item.beta"]
        self.assertEqual(len(beta_outcomes), 2)
        for outcome in beta_outcomes:
            self.assertEqual(outcome.answer_status, AnswerStatus.INCORRECT.value)
            self.assertNotEqual(outcome.selected_choice_index, outcome.correct_choice_index)

    def test_latency_does_not_determine_correctness(self) -> None:
        # alpha has fast latency and is correct; beta has slow latency but is still
        # incorrect because the wrong choice is selected. Latency only triggers the
        # bounded repeat.
        result = self._run(InMemoryEventStore())
        alpha = next(o for o in result.item_outcomes if o.content_item_id == "item.alpha")
        beta = next(o for o in result.item_outcomes if o.content_item_id == "item.beta")
        self.assertEqual(alpha.answer_status, AnswerStatus.CORRECT.value)
        self.assertEqual(beta.answer_status, AnswerStatus.INCORRECT.value)

    def test_repeat_cap_enforced(self) -> None:
        result = self._run(InMemoryEventStore())
        beta_trials = [
            e
            for e in result.events
            if e.event_type == "trial_created"
            and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        self.assertEqual(beta_trials[0].payload.get("repeat_count"), 0)
        self.assertEqual(beta_trials[1].payload.get("repeat_count"), 1)
        self.assertEqual(beta_trials[1].payload.get("cap"), 1)

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
        summary = derive_recognition_summary(result.events, repeat_cap=self.rule.repeat_cap)
        self.assertEqual(summary.session_id, str(result.runtime.state.session_id))
        self.assertEqual(summary.fixture_id, "minimal-recognition")
        self.assertEqual(summary.protocol_id, self.fixture.protocol_version_id)
        self.assertEqual(summary.event_count, len(result.events))
        self.assertEqual(summary.item_count, 2)
        self.assertEqual(summary.total_repeats, 1)
        self.assertEqual(summary.correct_count, 1)

        alpha = next(i for i in summary.items if i.content_item_id == "item.alpha")
        self.assertEqual(alpha.outcome, "correct")
        self.assertEqual(alpha.repeats_used, 0)
        self.assertEqual(alpha.selected_choice_index, 0)
        self.assertEqual(alpha.correct_choice_index, 0)

        beta = next(i for i in summary.items if i.content_item_id == "item.beta")
        self.assertEqual(beta.outcome, "incorrect")
        self.assertEqual(beta.repeats_used, 1)
        self.assertEqual(beta.selected_choice_index, 0)
        self.assertEqual(beta.correct_choice_index, 1)
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
            role = event.payload["asset_role"]
            self.assertTrue(role.startswith("choice_"))

    def test_no_provider_access(self) -> None:
        result = self._run(InMemoryEventStore())
        for event in result.events:
            if event.component == "renderer":
                self.assertEqual(event.payload.get("renderer_id"), "fixture_recognition_renderer")
            if event.event_type == "observation_received":
                self.assertEqual(event.payload.get("provider_id"), "fixture_recognition_choice")
                self.assertEqual(event.payload.get("observation_type"), "touch_input")

    def test_no_eeg_influence(self) -> None:
        result = self._run(InMemoryEventStore())
        for event in result.events:
            self.assertNotEqual(event.payload.get("observation_type"), "eeg_burst")
            payload_str = json.dumps(event.as_dict())
            self.assertNotIn("eeg", payload_str.lower())

    def test_adaptation_source_recorded(self) -> None:
        result = self._run(InMemoryEventStore())
        beta_trials = [
            e
            for e in result.events
            if e.event_type == "trial_created"
            and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        initial, repeat = beta_trials
        self.assertEqual(initial.payload.get("repeat_count"), 0)
        self.assertNotIn("adaptation_source", initial.payload)
        self.assertEqual(repeat.payload.get("repeat_count"), 1)
        self.assertEqual(repeat.payload.get("cap"), 1)
        # Beta is wrong, so the adaptation source is behavior, not latency.
        self.assertEqual(repeat.payload.get("adaptation_source"), "behavior")

    def _fixture_with_beta(self, beta: RecognitionFixtureItem) -> RecognitionFixture:
        alpha = self.fixture.items[0]
        return RecognitionFixture(
            fixture_id="minimal-recognition",
            protocol_id=self.fixture.protocol_id,
            protocol_version_id=self.fixture.protocol_version_id,
            program_id=self.fixture.program_id,
            program_version_id=self.fixture.program_version_id,
            task_definition_id=self.fixture.task_definition_id,
            block_id=self.fixture.block_id,
            block_type=self.fixture.block_type,
            items=[alpha, beta],
        )

    def test_wrong_fast_choice_causes_repeat(self) -> None:
        # Wrong choice with fast latency still triggers the bounded repeat.
        beta = RecognitionFixtureItem(
            content_item_id="item.beta",
            correct_choice_index=1,
            selected_choice_index=0,
            latency=0.5,
            assets={
                "choice_0": FixtureAsset(
                    "item.beta.choice_0", "choice_0", "fixture://item.beta/choice_0", "v1.0.0"
                ),
                "choice_1": FixtureAsset(
                    "item.beta.choice_1", "choice_1", "fixture://item.beta/choice_1", "v1.0.0"
                ),
            },
        )
        fixture = self._fixture_with_beta(beta)
        result = run_recognition_session(InMemoryEventStore(), fixture=fixture, rule=self.rule)
        beta_trials = [
            e
            for e in result.events
            if e.event_type == "trial_created"
            and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        repeat_trial = beta_trials[1]
        self.assertEqual(repeat_trial.payload.get("adaptation_source"), "behavior")
        self.assertEqual(repeat_trial.payload.get("cap"), 1)

    def test_correct_slow_choice_does_not_change_correctness(self) -> None:
        # Correct choice with slow latency triggers a repeat, but the outcome
        # remains correct and is never marked incorrect.
        beta = RecognitionFixtureItem(
            content_item_id="item.beta",
            correct_choice_index=1,
            selected_choice_index=1,
            latency=5.0,
            assets={
                "choice_0": FixtureAsset(
                    "item.beta.choice_0", "choice_0", "fixture://item.beta/choice_0", "v1.0.0"
                ),
                "choice_1": FixtureAsset(
                    "item.beta.choice_1", "choice_1", "fixture://item.beta/choice_1", "v1.0.0"
                ),
            },
        )
        fixture = self._fixture_with_beta(beta)
        result = run_recognition_session(InMemoryEventStore(), fixture=fixture, rule=self.rule)
        beta_trials = [
            e
            for e in result.events
            if e.event_type == "trial_created"
            and e.payload.get("content_item_ids") == ["item.beta"]
        ]
        self.assertEqual(len(beta_trials), 2)
        repeat_trial = beta_trials[1]
        self.assertEqual(repeat_trial.payload.get("adaptation_source"), "latency")

        beta_evaluations = [
            e
            for e in result.events
            if e.event_type == "evaluation_completed"
            and e.payload.get("expected_content_item_id") == "item.beta"
        ]
        for ev in beta_evaluations:
            self.assertEqual(ev.payload.get("answer_status"), AnswerStatus.CORRECT.value)

        summary = derive_recognition_summary(result.events, repeat_cap=self.rule.repeat_cap)
        beta_summary = next(i for i in summary.items if i.content_item_id == "item.beta")
        self.assertEqual(beta_summary.outcome, "correct")
        self.assertEqual(beta_summary.correct, True)
        self.assertEqual(beta_summary.repeats_used, 1)


class RecognitionCLITests(unittest.TestCase):
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
            ["--store-path", str(self.store_path), "run-recognition", "--format", "json"]
        )
        self.assertEqual(code, 0, msg=f"stderr: {err}")
        result = json.loads(out)
        self.assertEqual(result["fixture_id"], "minimal-recognition")
        self.assertEqual(result["item_count"], 2)
        self.assertEqual(result["total_repeats"], 1)
        self.assertEqual(result["correct_count"], 1)

    def test_cli_show_summary(self) -> None:
        session_id = "rec-cli-session"
        code, out, _err = self._run(
            [
                "--store-path",
                str(self.store_path),
                "run-recognition",
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
                "show-recognition-summary",
                session_id,
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["fixture_id"], "minimal-recognition")
        self.assertEqual(result["total_repeats"], 1)

    def test_cli_unknown_session_exits_three(self) -> None:
        self._run(["--store-path", str(self.store_path), "run-recognition"])
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "show-recognition-summary", "missing-session"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(out, "")
        self.assertIn("missing-session", err)

    def test_cli_invalid_session_id_exits_two(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "show-recognition-summary", ""]
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("invalid session ID", err)

    def test_cli_directory_path_exits_usage(self) -> None:
        dir_path = Path(self._td.name) / "a_directory"
        dir_path.mkdir()
        code, out, err = self._run(["--store-path", str(dir_path), "run-recognition"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("directory", err)

    def test_cli_json_success_single_document(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "run-recognition", "--format", "json"]
        )
        self.assertEqual(code, 0)
        self.assertIsNotNone(json.loads(out))
        self.assertNotIn("Traceback", out)
        self.assertNotIn("error:", out)


class RecognitionProcessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = Path(self._td.name) / "events.db"

    def _run_process(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "mpe", "--store-path", str(self.store_path)] + argv
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "packages" / "mpe" / "src")
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), env=env)

    def test_python_mpe_invocation(self) -> None:
        run = self._run_process(["run-recognition", "--format", "json"])
        self.assertEqual(run.returncode, 0, msg=run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["item_count"], 2)
        self.assertEqual(result["total_repeats"], 1)

        replay = self._run_process(
            ["show-recognition-summary", result["session_id"], "--format", "json"]
        )
        self.assertEqual(replay.returncode, 0, msg=replay.stderr)
        summary = json.loads(replay.stdout)
        self.assertEqual(summary["total_repeats"], 1)


if __name__ == "__main__":
    unittest.main()
