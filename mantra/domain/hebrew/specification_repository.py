"""Deterministic repository for Phase 4D Hebrew verb specifications.

The repository loads immutable JSON fixtures, validates schema versions,
detects duplicate entry IDs, and verifies SHA-256 content checksums. It does
not synthesize audio, mutate the filesystem, or fall back to unrelated lemmas.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from .specification import (
    HebrewVerbSpecification,
    SpecificationValidationResult,
    _normalize,
)


class HebrewSpecificationError(Exception):
    """Raised when a specification cannot be loaded or validated."""


class HebrewSpecificationRepository:
    """Deterministic loader for Hebrew verb specification fixtures."""

    SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0.0"})

    def __init__(self, data_dir: Path | str | None = None) -> None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[3] / "data/hebrew/specifications/v1"
        self._data_dir = Path(data_dir)

    def _path_for(self, verb_id: str) -> Path:
        return self._data_dir / f"{verb_id}.json"

    @staticmethod
    def _canonical_object(obj: Any) -> Any:
        """Recursively NFC-normalize strings for deterministic serialization."""
        if isinstance(obj, str):
            return _normalize(obj)
        if isinstance(obj, dict):
            return {k: HebrewSpecificationRepository._canonical_object(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [HebrewSpecificationRepository._canonical_object(v) for v in obj]
        return obj

    @classmethod
    def canonical_json(
        cls,
        obj: dict[str, Any],
        *,
        exclude_key: str | None = None,
    ) -> str:
        """Return deterministic canonical JSON for *obj*.

        The canonical form uses NFC-normalized strings, sorted object keys,
        no indentation, no ASCII escapes, and compact separators. This is the
        exact representation used for SHA-256 content checksums.
        """
        normalized = cls._canonical_object(obj)
        if exclude_key and isinstance(normalized, dict):
            normalized = {k: v for k, v in normalized.items() if k != exclude_key}
        return json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def compute_checksum(cls, data: dict[str, Any]) -> str:
        """Compute the SHA-256 checksum for *data* excluding any top-level checksum."""
        canonical = cls.canonical_json(data, exclude_key="content_checksum")
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def list_available(self) -> tuple[str, ...]:
        """Return the stable, sorted tuple of available verb IDs."""
        return tuple(sorted(path.stem for path in self._data_dir.glob("*.json") if path.is_file()))

    def has(self, verb_id: str) -> bool:
        """Return True when a fixture exists for *verb_id*."""
        return self._path_for(verb_id).is_file()

    def _load_raw(self, verb_id: str) -> dict[str, Any]:
        path = self._path_for(verb_id)
        if not path.is_file():
            raise HebrewSpecificationError(f"no specification for verb {verb_id!r}")
        text = path.read_text(encoding="utf-8")
        return cast(dict[str, Any], json.loads(text))

    def validate(self, verb_id: str) -> SpecificationValidationResult:
        """Validate the fixture for *verb_id* without caching or mutating files."""
        if not self.has(verb_id):
            return SpecificationValidationResult(
                valid=False,
                errors=(f"no specification for verb {verb_id!r}",),
                checksum_match=False,
                schema_version_supported=False,
            )

        raw = self._load_raw(verb_id)
        errors: list[str] = []

        schema_version = raw.get("schema_version", "")
        schema_version_supported = schema_version in self.SUPPORTED_SCHEMA_VERSIONS
        if not schema_version_supported:
            errors.append(f"unsupported schema version {schema_version!r}")

        stored_checksum = raw.get("content_checksum")
        computed_checksum = self.compute_checksum(raw)
        checksum_match = stored_checksum is not None and stored_checksum == computed_checksum
        if stored_checksum is None:
            errors.append("missing content_checksum")
        elif not checksum_match:
            errors.append("content checksum mismatch")

        entries = raw.get("entries", [])
        if not isinstance(entries, list):
            errors.append("entries must be a list")
        else:
            entry_ids = [e.get("entry_id") for e in entries if isinstance(e, dict)]
            if len(entry_ids) != len(set(entry_ids)):
                errors.append("duplicate entry IDs")

        # Domain-level validation: dataclass construction catches empty text,
        # language-routing errors, invalid enum values, and duplicate IDs.
        try:
            HebrewVerbSpecification.from_dict(copy.deepcopy(raw))
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"domain validation failed: {exc}")

        valid = not errors and checksum_match and schema_version_supported
        return SpecificationValidationResult(
            valid=valid,
            errors=tuple(errors),
            checksum_match=checksum_match,
            schema_version_supported=schema_version_supported,
        )

    def get(self, verb_id: str) -> HebrewVerbSpecification:
        """Return the validated specification for *verb_id*.

        Raises:
            HebrewSpecificationError: if the fixture is missing, has an
                unsupported schema version, an invalid checksum, or fails
                domain validation.
        """
        if not self.has(verb_id):
            raise HebrewSpecificationError(f"no specification for verb {verb_id!r}")

        result = self.validate(verb_id)
        if not result.valid:
            raise HebrewSpecificationError("; ".join(result.errors))

        raw = self._load_raw(verb_id)
        return HebrewVerbSpecification.from_dict(raw)
