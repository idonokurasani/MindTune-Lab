"""Guard against accidental reintroduction of secrets or credentials into Git."""

import json
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class SecretContainmentTests(unittest.TestCase):
    """Regression tests for secret and credential containment."""

    def test_oura_credentials_not_tracked(self) -> None:
        """.oura_credentials must never be tracked by Git."""
        result = subprocess.run(
            ["git", "ls-files", ".oura_credentials"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.stdout.strip(),
            "",
            ".oura_credentials is tracked; remove it from Git and rotate the credential",
        )

    def test_oura_credentials_in_gitignore(self) -> None:
        """.gitignore must ignore .oura_credentials."""
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".oura_credentials", gitignore.splitlines())

    def test_no_real_client_secret_in_tracked_files(self) -> None:
        """Tracked JSON files must not contain a non-placeholder client_secret."""
        tracked = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD", "--name-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        tracked_files = [p for p in tracked.stdout.splitlines() if p.endswith(".json")]

        placeholder_pattern = re.compile(r"^(YOUR_|example|placeholder|XXX|TODO$)", re.I)
        for path in tracked_files:
            full = REPO_ROOT / path
            try:
                data = json.loads(full.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for key, value in _flatten(data).items():
                if "secret" not in key.lower():
                    continue
                if isinstance(value, str) and value and not placeholder_pattern.match(value):
                    self.fail(f"{path}: tracked non-placeholder value for {key}")

    def test_no_oura_credentials_in_tracked_root(self) -> None:
        """Only the placeholder example may live at the repository root."""
        for p in REPO_ROOT.glob(".oura_credentials*"):
            self.assertEqual(
                p.name,
                ".oura_credentials.example",
                f"Unexpected Oura credential file at {p.name}; remove or rename",
            )


def _flatten(obj: object, prefix: str = "") -> dict[str, object]:
    """Flatten a JSON-like object into dotted keys."""
    result: dict[str, object] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                result.update(_flatten(v, key))
            else:
                result[key] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)):
                result.update(_flatten(v, key))
            else:
                result[key] = v
    else:
        result[prefix] = obj
    return result


if __name__ == "__main__":
    unittest.main()
