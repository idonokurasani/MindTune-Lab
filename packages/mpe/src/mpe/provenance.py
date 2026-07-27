"""Software-revision resolution and the discriminated provenance model.

Two things live here, both required by ADR-0001 sec. 2.8:

1. `resolve_software_revision()`, the deployment-safe resolver. A deployed
   container, a wheel install, or a read-only image has no `.git` directory, so
   `git rev-parse` is the development fallback and never the primary source.
2. `ProvenanceReference`, the discriminated model every derived result carries,
   so that no result is *silently* unprovenanced: a schema-1.2 result must name
   its `session_provenance_recorded` event, and a schema-1.1 result must declare
   that provenance is unavailable because the stream predates it.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from mpe.errors import ValidationError
from mpe.integrity import is_chained_schema
from mpe.types import EventID

REVISION_SOURCE_BUILD_METADATA = "build_metadata"
REVISION_SOURCE_ENVIRONMENT = "environment"
REVISION_SOURCE_PACKAGE_METADATA = "package_metadata"
REVISION_SOURCE_GIT = "git"
REVISION_SOURCE_UNKNOWN = "unknown"

REVISION_ENVIRONMENT_VARIABLE = "MPE_SOFTWARE_REVISION"

PROVENANCE_RECORDED = "recorded"
PROVENANCE_UNAVAILABLE_LEGACY = "unavailable_legacy"


@dataclass(frozen=True)
class ResolvedRevision:
    """A software revision together with how strong its source is.

    `revision` is `None` only for `source: "unknown"`: an unresolved revision is
    recorded as an explicit unknown, never as an empty string or a fabricated
    version. `dirty` is only meaningful for the `git` source.
    """

    revision: str | None
    source: str
    dirty: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "source": self.source,
            "dirty": self.dirty,
        }


def _from_build_metadata() -> ResolvedRevision | None:
    try:
        from mpe import _build_info  # type: ignore[attr-defined]
    except ImportError:
        return None
    revision = getattr(_build_info, "REVISION", None)
    if not revision:
        return None
    return ResolvedRevision(str(revision), REVISION_SOURCE_BUILD_METADATA)


def _from_environment() -> ResolvedRevision | None:
    revision = os.environ.get(REVISION_ENVIRONMENT_VARIABLE, "").strip()
    if not revision:
        return None
    return ResolvedRevision(revision, REVISION_SOURCE_ENVIRONMENT)


def _from_package_metadata() -> ResolvedRevision | None:
    from importlib import metadata

    for distribution in ("mpe", "mindtune-console"):
        try:
            version = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            continue
        if version:
            return ResolvedRevision(f"{distribution}-{version}", REVISION_SOURCE_PACKAGE_METADATA)
    return None


def _from_git() -> ResolvedRevision | None:
    """Development fallback only: requires a working tree with a `.git` dir."""
    root = Path(__file__).resolve().parents[4]
    if not (root / ".git").exists():
        return None
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if not revision:
        return None
    return ResolvedRevision(revision, REVISION_SOURCE_GIT, dirty=bool(status))


@lru_cache(maxsize=1)
def resolve_software_revision() -> ResolvedRevision:
    """Resolve the writer's revision through the ordered, deployment-safe chain.

    Build metadata, then an environment-provided revision, then installed
    package metadata, then git in a development checkout, then an explicit
    unknown. Never raises and never blocks session start; a caller that gets
    `source: "unknown"` has a valid session that downstream reports must flag.
    """
    for resolver in (
        _from_build_metadata,
        _from_environment,
        _from_package_metadata,
        _from_git,
    ):
        try:
            resolved = resolver()
        except Exception:  # noqa: BLE001 - resolution must never break a session
            resolved = None
        if resolved is not None:
            return resolved
    return ResolvedRevision(None, REVISION_SOURCE_UNKNOWN)


@dataclass(frozen=True)
class ProvenanceReference:
    """How a derived result is bound to the provenance of its session.

    Validated on construction (ADR-0001 sec. 2.8.1): `recorded` requires an
    event id and schema 1.2; `unavailable_legacy` requires `None` and schema
    1.1. There is no third case, so a result cannot be silently unprovenanced.
    """

    status: str
    event_id: EventID | None
    schema_version: str

    def __post_init__(self) -> None:
        chained = is_chained_schema(self.schema_version)
        if self.status == PROVENANCE_RECORDED:
            if self.event_id is None:
                raise ValidationError("provenance_status 'recorded' requires a provenance_event_id")
            if not chained:
                raise ValidationError(
                    f"provenance_status 'recorded' is not permitted for schema "
                    f"{self.schema_version}"
                )
        elif self.status == PROVENANCE_UNAVAILABLE_LEGACY:
            if self.event_id is not None:
                raise ValidationError(
                    "provenance_status 'unavailable_legacy' requires no " "provenance_event_id"
                )
            if chained:
                raise ValidationError(
                    f"provenance_status 'unavailable_legacy' is not permitted for "
                    f"schema {self.schema_version}"
                )
        else:
            raise ValidationError(f"Unknown provenance_status: {self.status!r}")

    @classmethod
    def recorded(cls, event_id: EventID, schema_version: str) -> ProvenanceReference:
        return cls(PROVENANCE_RECORDED, event_id, schema_version)

    @classmethod
    def unavailable_legacy(cls, schema_version: str) -> ProvenanceReference:
        return cls(PROVENANCE_UNAVAILABLE_LEGACY, None, schema_version)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provenance_status": self.status,
            "provenance_event_id": str(self.event_id) if self.event_id else None,
        }
