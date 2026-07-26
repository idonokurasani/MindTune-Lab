"""Regression tests ensuring Citizen Café and Streetwise Hebrew references are gone."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

CONSOLE_DIR = Path(__file__).resolve().parents[1]

# Case-insensitive tokens that identify the two legacy commercial sources,
# plus Azure Speech, which is not part of the approved Hebrew audio architecture.
FORBIDDEN_SOURCE_PATTERNS = [
    re.compile(r"citizen\s*cafe", re.IGNORECASE),
    re.compile(r"citizen_cafe", re.IGNORECASE),
    re.compile(r"streetwise\s*hebrew", re.IGNORECASE),
    re.compile(r"streetwise_hebrew", re.IGNORECASE),
]
AZURE_SPEECH_PATTERNS = [
    re.compile(r"azure_speech", re.IGNORECASE),
    re.compile(r"azure speech", re.IGNORECASE),
]

# Files and directories that legitimately contain these names because they
# are the legacy artifacts themselves or backups of them. They must not exist
# in the repository anymore, but if they are present we should not treat them
# as accidental references.
EXCLUDED_PATHS: set[str] = {
    ".git",
    ".venv",
    ".venv_phonikud",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "data/citizen_cafe_all_courses",
    "data/citizen_cafe_consolidation",
    "data/hebrew_enrichment/streetwise_hebrew",
    "data/backups/quizlet_hebrew_audit_before_blue_purple_20260703.csv",
    "data/backups/quizlet_hebrew_seed_before_blue_purple_20260703.json",
    "data/quizlet_hebrew_seed.json",
}

# Historical reports, audits, READMEs and evaluation artifacts may cite the
# old provider names for provenance. The regression test focuses on active
# runtime and data files.
EXCLUDED_PREFIXES: tuple[str, ...] = (
    "tests/test_forbidden_legacy_sources.py",
    "tests/test_hebrew_recovery.py",
    "HEBREW_SOURCE_CLEANUP_REPORT.md",
    "HELP_INTEGRATION.md",
    "scripts/generate_phonikud_comparison_audio.py",
    "scripts/build_mantra_phase1.py",
    "scripts/generate_mantra_audio.py",
    "data/mantra/",
    "data/phonikud_eval/",
    "docs/audits/",
    "docs/project/",
    "docs/implementation/phase4b1/",
)


def _iter_text_files():
    for path in CONSOLE_DIR.rglob("*"):
        if any(part in EXCLUDED_PATHS for part in path.parts):
            continue
        rel = str(path.relative_to(CONSOLE_DIR))
        if rel.startswith(EXCLUDED_PREFIXES):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pyc", ".pyo", ".so", ".dylib", ".wav", ".mp3", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".ttf", ".woff", ".woff2", ".db", ".sqlite", ".sqlite3", ".pdf", ".zip", ".xml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        yield path, text


class ForbiddenLegacySourceReferencesTests(unittest.TestCase):
    def test_no_citizen_cafe_or_streetwise_references_in_code(self) -> None:
        hits: list[str] = []
        for path, text in _iter_text_files():
            for pattern in FORBIDDEN_SOURCE_PATTERNS:
                if pattern.search(text):
                    hits.append(f"{path.relative_to(CONSOLE_DIR)} matches {pattern.pattern!r}")
        if hits:
            self.fail("Found forbidden legacy source references:\n" + "\n".join(hits))

    def test_no_azure_speech_references_in_code(self) -> None:
        hits: list[str] = []
        for path, text in _iter_text_files():
            for pattern in AZURE_SPEECH_PATTERNS:
                if pattern.search(text):
                    hits.append(f"{path.relative_to(CONSOLE_DIR)} matches {pattern.pattern!r}")
        if hits:
            self.fail("Found Azure Speech references:\n" + "\n".join(hits))

    def test_legacy_data_directories_are_removed(self) -> None:
        for relative in {
            "data/citizen_cafe_all_courses",
            "data/citizen_cafe_consolidation",
            "data/hebrew_enrichment/streetwise_hebrew",
        }:
            self.assertFalse(
                (CONSOLE_DIR / relative).exists(),
                f"Legacy data directory still exists: {relative}",
            )

    def test_azure_speech_module_is_removed(self) -> None:
        for name in {"azure_speech.py", "tests/test_azure_speech.py"}:
            self.assertFalse((CONSOLE_DIR / name).exists(), f"Azure Speech file still exists: {name}")


if __name__ == "__main__":
    unittest.main()
