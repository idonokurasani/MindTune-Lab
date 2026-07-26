"""Typed FC11 recorded-data contracts for CLM-02B."""

from __future__ import annotations

from dataclasses import dataclass

from mindtune_clm.replay.source import RecordedSensorSource


@dataclass(frozen=True)
class FC11RecordedSource(RecordedSensorSource):
    """Immutable source contract for a recorded FC11 EEG export.

    Extends the generic RecordedSensorSource with FC11-specific provenance
    without breaking the generic replay pipeline.
    """

    capture_software_version: str | None = None
    firmware_version: str | None = None
    protocol_version: str | None = None
    samples_per_packet: int = 1
    metadata_checksum: str = ""


@dataclass(frozen=True)
class FC11Metadata:
    """Parsed contents of an FC11 sidecar metadata file."""

    source_format: str
    source_format_version: str
    sample_rate_hz: float
    samples_per_packet: int
    gain: float | None
    scale_factor: float | None
    session_id: str
    recording_id: str
    start_timestamp: float
    time_unit: str
    channel_names: list[str]
    quality_field_names: list[str]
    artifact_field_names: list[str]
    parser_id: str
    parser_version: str
    capture_software_version: str | None
    firmware_version: str | None
    protocol_version: str | None
    provenance: dict[str, str]

    @property
    def sample_interval(self) -> float:
        return 1.0 / max(1.0, self.sample_rate_hz)
