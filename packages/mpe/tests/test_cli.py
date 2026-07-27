"""CLI tests for the MPE command-line interface."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from mpe.cli import main
from mpe.cli_helpers import make_in_memory_reference_state, normalize_state_dict
from mpe.errors import ConcurrencyError
from mpe.types import SessionID


class CLITests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = Path(self._td.name) / "events.db"

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        """Run the CLI with the given argv and return (exit_code, stdout, stderr)."""
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue().strip(), err.getvalue().strip()

    def test_run_mock_session_persists_23_events(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "run-mock-session", "--format", "json"]
        )
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["event_count"], 23)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["terminal"])
        self.assertIn("session_id", result)

    def test_run_and_replay_match(self) -> None:
        session_id = "replay-match-session"
        run_argv = [
            "--store-path",
            str(self.store_path),
            "run-mock-session",
            "--session-id",
            session_id,
            "--format",
            "json",
        ]
        code, out, _err = self._run(run_argv)
        self.assertEqual(code, 0)

        replay_argv = [
            "--store-path",
            str(self.store_path),
            "replay",
            session_id,
            "--format",
            "json",
        ]
        code, out, _err = self._run(replay_argv)
        self.assertEqual(code, 0)
        replayed = json.loads(out)

        reference = make_in_memory_reference_state(
            session_id=SessionID(session_id),
            learner_id="learner_001",
            random_seed="seed_0",
        )
        reference_dict = normalize_state_dict(reference.as_dict())
        replayed_dict = normalize_state_dict(replayed)
        self.assertEqual(replayed_dict, reference_dict)

    def test_replay_missing_session_fails(self) -> None:
        # First create an empty store by running a session, so the store exists.
        self._run(["--store-path", str(self.store_path), "run-mock-session", "--session-id", "s1"])
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "replay", "missing-session", "--format", "json"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(out, "")
        self.assertIn("missing-session", err)

    def test_list_sessions(self) -> None:
        self._run(
            ["--store-path", str(self.store_path), "run-mock-session", "--session-id", "session_b"]
        )
        self._run(
            ["--store-path", str(self.store_path), "run-mock-session", "--session-id", "session_a"]
        )

        code, out, err = self._run(
            ["--store-path", str(self.store_path), "list-sessions", "--format", "json"]
        )
        self.assertEqual(code, 0)
        sessions = json.loads(out)
        self.assertEqual(len(sessions), 2)
        ids = [s["session_id"] for s in sessions]
        self.assertEqual(ids, sorted(ids))
        for s in sessions:
            self.assertEqual(s["event_count"], 23)
            self.assertEqual(s["last_sequence"], 23)

    def test_validate_store_passes(self) -> None:
        self._run(["--store-path", str(self.store_path), "run-mock-session", "--session-id", "s1"])
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "validate-store", "--format", "json"]
        )
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertTrue(result["valid"])
        self.assertEqual(result["event_count"], 23)
        self.assertEqual(result["session_count"], 1)
        self.assertIsNone(result["error"])

    def test_validate_store_fails_on_corrupt_row(self) -> None:
        self._run(["--store-path", str(self.store_path), "run-mock-session", "--session-id", "s1"])
        # Corrupt the first event's payload to an empty dict.
        conn = sqlite3.connect(str(self.store_path))
        conn.execute("UPDATE events SET payload = ? WHERE session_sequence_number = 1", ("{}",))
        conn.commit()
        conn.close()

        code, out, err = self._run(
            ["--store-path", str(self.store_path), "validate-store", "--format", "json"]
        )
        self.assertEqual(code, 4)
        result = json.loads(out)
        self.assertFalse(result["valid"])
        self.assertIsNotNone(result["error"])

    def test_store_path_env_var(self) -> None:
        env_path = Path(self._td.name) / "env_events.db"
        old = os.environ.get("MPE_EVENT_STORE_PATH")
        os.environ["MPE_EVENT_STORE_PATH"] = str(env_path)
        try:
            code, out, _err = self._run(["run-mock-session", "--format", "json"])
            self.assertEqual(code, 0)
            result = json.loads(out)
            self.assertEqual(result["event_count"], 23)
            self.assertTrue(env_path.exists())
        finally:
            if old is None:
                os.environ.pop("MPE_EVENT_STORE_PATH", None)
            else:
                os.environ["MPE_EVENT_STORE_PATH"] = old

    def test_format_json_for_all_commands(self) -> None:
        self._run(["--store-path", str(self.store_path), "run-mock-session", "--session-id", "s1"])
        for command in [
            ["--store-path", str(self.store_path), "replay", "s1", "--format", "json"],
            ["--store-path", str(self.store_path), "list-sessions", "--format", "json"],
            ["--store-path", str(self.store_path), "validate-store", "--format", "json"],
        ]:
            with self.subTest(command=command):
                code, out, _err = self._run(command)
                self.assertEqual(code, 0)
                # Must be valid JSON and no extra stdout.
                parsed = json.loads(out)
                self.assertIsNotNone(parsed)

    def test_verbose_writes_to_stderr_not_stdout(self) -> None:
        code, out, err = self._run(
            ["--store-path", str(self.store_path), "-v", "run-mock-session", "--format", "json"]
        )
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["event_count"], 23)
        # Diagnostic lines belong on stderr.
        self.assertIn("Resolved store path", err)
        self.assertIn("Created new event store", err)

    def test_read_only_commands_do_not_create_store(self) -> None:
        missing_path = Path(self._td.name) / "does_not_exist.db"
        for command in [
            ["--store-path", str(missing_path), "list-sessions"],
            ["--store-path", str(missing_path), "validate-store"],
            ["--store-path", str(missing_path), "replay", "s1"],
        ]:
            with self.subTest(command=command):
                code, out, err = self._run(command)
                self.assertEqual(code, 3)
                self.assertFalse(missing_path.exists())
                self.assertEqual(out, "")
                self.assertIn("not found", err)

    def test_human_list_sessions_format(self) -> None:
        self._run(["--store-path", str(self.store_path), "run-mock-session", "--session-id", "s1"])
        code, out, _err = self._run(["--store-path", str(self.store_path), "list-sessions"])
        self.assertEqual(code, 0)
        parts = out.split()
        self.assertEqual(parts[1], "23")
        self.assertEqual(parts[2], "23")

    def test_invalid_session_id_exits_usage(self) -> None:
        # Create a store so missing store does not mask the usage error.
        self._run(["--store-path", str(self.store_path), "run-mock-session", "--session-id", "s1"])
        code, out, err = self._run(["--store-path", str(self.store_path), "replay", ""])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("invalid session ID", err)

    def test_directory_path_exits_usage(self) -> None:
        dir_path = Path(self._td.name) / "a_directory"
        dir_path.mkdir()
        code, out, err = self._run(["--store-path", str(dir_path), "run-mock-session"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("directory", err)

    def _ensure_store_file_exists(self) -> None:
        from mpe.cli_helpers import open_store

        with open_store(self.store_path) as store:
            store.list_sessions()

    def test_concurrency_error_maps_to_exit_five(self) -> None:
        self._ensure_store_file_exists()
        with patch("mpe.cli.open_store") as mock_open:
            mock_open.side_effect = ConcurrencyError("database is locked")
            code, out, err = self._run(["--store-path", str(self.store_path), "list-sessions"])
        self.assertEqual(code, 5)
        self.assertEqual(out, "")
        self.assertIn("database is locked", err)

    def test_unexpected_error_maps_to_exit_one(self) -> None:
        self._ensure_store_file_exists()
        with patch("mpe.cli.open_store") as mock_open:
            mock_open.side_effect = RuntimeError("unexpected boom")
            code, out, err = self._run(["--store-path", str(self.store_path), "list-sessions"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("unexpected boom", err)

    def test_provider_failure_maps_to_exit_six(self) -> None:
        from mpe.cli_helpers import build_mock_providers
        from mpe.providers import MockScheduler

        scheduler = MockScheduler()
        scheduler.fail = True
        providers = build_mock_providers()
        providers.scheduler = scheduler  # type: ignore[misc]
        with patch("mpe.cli_helpers.build_mock_providers") as mock_providers:
            mock_providers.return_value = providers
            code, out, err = self._run(
                ["--store-path", str(self.store_path), "run-mock-session", "--format", "json"]
            )
        self.assertEqual(code, 6)
        self.assertEqual(out, "")
        self.assertIn("forced failure", err)


class CLIProcessTests(unittest.TestCase):
    """Process-level invocation tests using the installed console entry point."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = Path(self._td.name) / "events.db"

    def _run_process(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "mpe", "--store-path", str(self.store_path)] + argv
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

    def test_python_mpe_invocation(self) -> None:
        run = self._run_process(["run-mock-session", "--format", "json"])
        self.assertEqual(run.returncode, 0)
        result = json.loads(run.stdout)
        self.assertEqual(result["event_count"], 23)

        replay = self._run_process(["replay", result["session_id"], "--format", "json"])
        self.assertEqual(replay.returncode, 0)
        replayed = json.loads(replay.stdout)
        self.assertEqual(replayed["session_status"], "completed")

    def test_installed_console_entry_point(self) -> None:
        # The console script lives next to the interpreter in an editable install.
        mpe_path = Path(sys.executable).with_name("mpe")
        if not mpe_path.exists():
            self.skipTest(f"console script not found: {mpe_path}")
        proc = subprocess.run(
            [str(mpe_path), "--version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("mpe", proc.stdout)

    def test_cross_process_replay(self) -> None:
        run = self._run_process(["run-mock-session", "--session-id", "x-proc", "--format", "json"])
        self.assertEqual(run.returncode, 0)

        replay = self._run_process(["replay", "x-proc", "--format", "json"])
        self.assertEqual(replay.returncode, 0)
        replayed = json.loads(replay.stdout)
        self.assertTrue(replayed["terminal"])


if __name__ == "__main__":
    unittest.main()
