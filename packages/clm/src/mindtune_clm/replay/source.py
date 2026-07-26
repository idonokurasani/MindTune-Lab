"""Immutable recorded sensor source contract for CLM-02."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RecordedSensorSource:
    """A recorded sensor source with immutable identity and metadata.

    The source does not contain the recording bytes; it identifies the source
    and carries a checksum so that any mutation is detectable.  Replay runners
    read the actual content from a fixture root provided at run time.
    """

    source_id: str
    source_format: str
    fixture_handle: str
    content_checksum: str
    source_sampling_rate_hz: float
    source_start_timestamp: float
    channel_names: list[str]
    recording_id: str | None = None
    sensor_type: str = "eeg"
    metadata_version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_source_from_text(
    source_id: str,
    fixture_handle: str,
    text: str,
    channel_names: list[str],
    source_sampling_rate_hz: float = 10.0,
    source_start_timestamp: float = 0.0,
    sensor_type: str = "eeg",
    source_format: str = "csv_v1",
    recording_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[RecordedSensorSource, str]:
    """Return a source and content loaded from an in-memory fixture string."""
    checksum = _sha256_hex(text.encode("utf-8"))
    source = RecordedSensorSource(
        source_id=source_id,
        source_format=source_format,
        fixture_handle=fixture_handle,
        content_checksum=checksum,
        source_sampling_rate_hz=source_sampling_rate_hz,
        source_start_timestamp=source_start_timestamp,
        channel_names=list(channel_names),
        recording_id=recording_id,
        sensor_type=sensor_type,
        metadata=metadata or {},
    )
    return source, text


def load_source_from_file(
    fixture_root: Path,
    fixture_handle: str,
    source_id: str | None = None,
    sensor_type: str = "eeg",
    source_format: str = "csv_v1",
    recording_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[RecordedSensorSource, str]:
    """Return a source and content loaded from a fixture root path.

    ``fixture_handle`` must be a relative path inside ``fixture_root``.
    No absolute personal paths are stored in the returned source.
    """
    path = Path(fixture_root) / fixture_handle
    content = path.read_text(encoding="utf-8")
    checksum = _sha256_hex(content.encode("utf-8"))
    source = RecordedSensorSource(
        source_id=source_id or fixture_handle,
        source_format=source_format,
        fixture_handle=fixture_handle,
        content_checksum=checksum,
        source_sampling_rate_hz=10.0,
        source_start_timestamp=0.0,
        channel_names=[],
        recording_id=recording_id,
        sensor_type=sensor_type,
        metadata=metadata or {},
    )
    return source, content
