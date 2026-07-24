"""Adapter for the Java Verb Inflector."""
from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..exceptions import InflectorError
from ..morphology import binyan_from_pattern, parse_morphology_tag
from ..normalization import normalize_hebrew, standard_unvocalized, strip_niqqud


class VerbInflectorAdapter:
    """Invoke the Verb Inflector JAR to generate conjugations."""

    def __init__(self, jar_path: Path | None = None, java_bin: str | None = None):
        self.jar_path = jar_path or self._default_jar_path()
        self.java_bin = java_bin or self._find_java()

    @staticmethod
    def _find_java() -> str:
        candidates = [
            "/opt/homebrew/opt/openjdk/bin/java",
        ]
        for c in candidates:
            if shutil.which(c):
                return c
        # Fall back to JAVA_HOME or PATH
        java = shutil.which("java")
        if java:
            return java
        return "java"

    @staticmethod
    def _default_jar_path() -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "data"
            / "hebrew"
            / "resources"
            / "verb_inflector"
            / "VerbInflector.jar"
        )

    def _write_input_csv(
        self,
        base_form: str,
        pattern: str,
        table_number: int,
        path: Path,
    ) -> None:
        # Ensure apostrophe is preserved for sin/shin encoding in the index.
        line = f"{base_form},{pattern},{table_number}\n"
        path.write_text(line, encoding="utf-8")

    def generate(
        self,
        base_form: str,
        pattern: str,
        table_number: int,
        timeout: int = 120,
    ) -> list[dict[str, Any]]:
        """Generate inflected forms for one base form + table."""
        if not self.jar_path.exists():
            raise InflectorError(f"Verb Inflector JAR not found: {self.jar_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = Path(tmpdir) / "input.csv"
            self._write_input_csv(base_form, pattern, table_number, input_csv)

            cmd = [
                self.java_bin,
                "-jar",
                str(self.jar_path),
                "generate",
                str(input_csv),
            ]
            try:
                result = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding="utf-8",
                )
            except subprocess.TimeoutExpired as exc:
                raise InflectorError(f"Verb Inflector timed out: {exc}") from exc

            if result.returncode != 0:
                raise InflectorError(
                    f"Verb Inflector failed: {result.stderr or result.stdout}"
                )

            output_path = Path(tmpdir) / "Generated Inflections.txt"
            if not output_path.exists():
                raise InflectorError("Verb Inflector did not produce output file")

            return self._parse_output(output_path, base_form)

    def _parse_output(self, output_path: Path, base_form: str) -> list[dict[str, Any]]:
        """Parse the generated inflections file."""
        rows: list[dict[str, Any]] = []
        text = output_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) != 5:
                continue
            pattern, table_str, surface, morph, base_out = parts
            surface = normalize_hebrew(surface)
            features = parse_morphology_tag(morph, pattern, int(table_str))
            rows.append(
                {
                    "pattern": pattern,
                    "table_number": int(table_str),
                    "surface_vocalized": surface,
                    "surface_plain": standard_unvocalized(surface),
                    "morphology": morph,
                    "base_form_vocalized": normalize_hebrew(base_out),
                    "base_form_plain": standard_unvocalized(base_out),
                    "binyan": binyan_from_pattern(pattern),
                    "features": features.as_dict(),
                }
            )
        return rows

    def generate_conjugations(
        self,
        infinitive_plain: str,
        root: str | None = None,
        binyan: str | None = None,
        pattern: str | None = None,
        table_number: int | None = None,
    ) -> list[dict[str, Any]]:
        """Higher-level wrapper that looks up pattern/table from TheVerbIndex."""
        # For the three target verbs, derive base form by stripping infinitive prefix.
        base_form = infinitive_plain
        if base_form.startswith("ל"):
            base_form = base_form[1:]

        if not pattern or not table_number:
            pattern, table_number = self._resolve_pattern_table(base_form, binyan)

        return self.generate(base_form, pattern, table_number)

    def _resolve_pattern_table(
        self, base_form: str, binyan: str | None = None
    ) -> tuple[str, int]:
        """Resolve pattern and table number from TheVerbIndex.csv."""
        index_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "hebrew"
            / "resources"
            / "eran_tomer"
            / "TheVerbIndex.csv"
        )
        base_plain = strip_niqqud(base_form)
        with index_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if strip_niqqud(row["base_form"]) == base_plain:
                    return row["pattern_1"], int(row["table_number_1"])
        raise InflectorError(
            f"Could not resolve pattern/table for base form {base_form}"
        )
