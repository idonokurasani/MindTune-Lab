"""Cross-process restart recovery using the restart_demo module."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

PYTHON = sys.executable


class RestartRecoveryTests(unittest.TestCase):
    def test_two_process_replay_verification(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "events.db")
            env = os.environ.copy()
            env["MPE_EVENT_STORE_PATH"] = db_path

            result_write = subprocess.run(
                [PYTHON, "-m", "mpe.persistence.restart_demo"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result_write.returncode, 0, result_write.stderr)
            self.assertIn("Session persisted", result_write.stdout)

            result_replay = subprocess.run(
                [PYTHON, "-m", "mpe.persistence.restart_demo"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result_replay.returncode, 0, result_replay.stderr)
            self.assertIn("Cross-process replay verified", result_replay.stdout)
