"""FC11 sidecar metadata parsing for CLM-02B."""

from __future__ import annotations

from typing import Any

from mindtune_clm.replay.fc11.schema import FC11Metadata


def fc11_metadata_from_dict(data: dict[str, Any]) -> FC11Metadata:
    """Parse an FC11 metadata sidecar into a typed contract."""
    provenance: dict[str, str] = {}
    raw_prov = data.get("provenance") or {}
    if isinstance(raw_prov, dict):
        provenance = {str(k): str(v) for k, v in raw_prov.items()}
    return FC11Metadata(
        source_format=str(data.get("source_format", "fc11_eeg_csv_v1")),
        source_format_version=str(data.get("source_format_version", "1.0.0")),
        sample_rate_hz=float(data.get("sample_rate_hz", 10.0)),
        samples_per_packet=int(data.get("samples_per_packet", 1)),
        gain=float(g) if (g := data.get("gain")) is not None else None,
        scale_factor=float(s) if (s := data.get("scale_factor")) is not None else None,
        session_id=str(data.get("session_id", "anonymous")),
        recording_id=str(data.get("recording_id", "anonymous")),
        start_timestamp=float(data.get("start_timestamp", 0.0)),
        time_unit=str(data.get("time_unit", "seconds")),
        channel_names=[str(c) for c in (data.get("channel_names") or [])],
        quality_field_names=[str(c) for c in (data.get("quality_field_names") or [])],
        artifact_field_names=[str(c) for c in (data.get("artifact_field_names") or [])],
        parser_id=str(data.get("parser_id", "fc11_csv_parser")),
        parser_version=str(data.get("parser_version", "1.0.0")),
        capture_software_version=data.get("capture_software_version"),
        firmware_version=data.get("firmware_version"),
        protocol_version=data.get("protocol_version"),
        provenance=provenance,
    )
