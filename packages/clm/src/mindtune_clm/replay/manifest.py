"""Replay manifest and checksum for CLM-02."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.replay.source import RecordedSensorSource


def _canonical_json(obj: Any) -> str:
    """Stable JSON with sorted keys and no extra whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ReplayManifest:
    """Everything required to reproduce a deterministic replay."""

    replay_id: str
    source_id: str
    source_checksum: str
    parser_id: str
    parser_version: str
    normalization_policy_id: str
    normalization_policy_version: str
    quality_policy_id: str
    quality_policy_version: str
    window_policy_id: str
    window_policy_version: str
    clm_policy_id: str
    clm_policy_version: str
    deterministic_seed: str
    replay_clock_config: dict[str, Any]
    requested_time_interval: tuple[float, float] | None
    creation_timestamp: float
    manifest_checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)


def make_manifest(
    replay_id: str,
    source: RecordedSensorSource,
    parser_id: str,
    parser_version: str,
    normalization_policy_id: str,
    normalization_policy_version: str,
    quality_policy_id: str,
    quality_policy_version: str,
    window_policy_id: str,
    window_policy_version: str,
    clm_policy_id: str,
    clm_policy_version: str,
    replay_clock_config: dict[str, Any],
    deterministic_seed: str,
    requested_time_interval: tuple[float, float] | None,
    creation_timestamp: float,
    metadata: dict[str, Any] | None = None,
) -> ReplayManifest:
    """Build a manifest with a self-checksum that excludes the checksum field."""
    payload = {
        "replay_id": replay_id,
        "source_id": source.source_id,
        "source_checksum": source.content_checksum,
        "parser_id": parser_id,
        "parser_version": parser_version,
        "normalization_policy_id": normalization_policy_id,
        "normalization_policy_version": normalization_policy_version,
        "quality_policy_id": quality_policy_id,
        "quality_policy_version": quality_policy_version,
        "window_policy_id": window_policy_id,
        "window_policy_version": window_policy_version,
        "clm_policy_id": clm_policy_id,
        "clm_policy_version": clm_policy_version,
        "deterministic_seed": deterministic_seed,
        "replay_clock_config": replay_clock_config,
        "requested_time_interval": requested_time_interval,
        "creation_timestamp": creation_timestamp,
        "metadata": metadata or {},
    }
    canonical = _canonical_json(payload)
    checksum = _sha256_hex(canonical.encode("utf-8"))
    return ReplayManifest(
        replay_id=replay_id,
        source_id=source.source_id,
        source_checksum=source.content_checksum,
        parser_id=parser_id,
        parser_version=parser_version,
        normalization_policy_id=normalization_policy_id,
        normalization_policy_version=normalization_policy_version,
        quality_policy_id=quality_policy_id,
        quality_policy_version=quality_policy_version,
        window_policy_id=window_policy_id,
        window_policy_version=window_policy_version,
        clm_policy_id=clm_policy_id,
        clm_policy_version=clm_policy_version,
        deterministic_seed=deterministic_seed,
        replay_clock_config=replay_clock_config,
        requested_time_interval=requested_time_interval,
        creation_timestamp=creation_timestamp,
        manifest_checksum=checksum,
        metadata=metadata or {},
    )


def verify_manifest(manifest: ReplayManifest) -> bool:
    """Recompute the manifest checksum and confirm it matches."""
    payload = {
        "replay_id": manifest.replay_id,
        "source_id": manifest.source_id,
        "source_checksum": manifest.source_checksum,
        "parser_id": manifest.parser_id,
        "parser_version": manifest.parser_version,
        "normalization_policy_id": manifest.normalization_policy_id,
        "normalization_policy_version": manifest.normalization_policy_version,
        "quality_policy_id": manifest.quality_policy_id,
        "quality_policy_version": manifest.quality_policy_version,
        "window_policy_id": manifest.window_policy_id,
        "window_policy_version": manifest.window_policy_version,
        "clm_policy_id": manifest.clm_policy_id,
        "clm_policy_version": manifest.clm_policy_version,
        "deterministic_seed": manifest.deterministic_seed,
        "replay_clock_config": manifest.replay_clock_config,
        "requested_time_interval": manifest.requested_time_interval,
        "creation_timestamp": manifest.creation_timestamp,
        "metadata": dict(manifest.metadata),
    }
    canonical = _canonical_json(payload)
    checksum = _sha256_hex(canonical.encode("utf-8"))
    return checksum == manifest.manifest_checksum
