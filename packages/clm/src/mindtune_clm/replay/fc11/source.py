"""FC11 source loading helpers for CLM-02B."""

from __future__ import annotations

import hashlib
import json

from mindtune_clm.replay.fc11.metadata import fc11_metadata_from_dict
from mindtune_clm.replay.fc11.schema import FC11RecordedSource


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_fc11_source_from_text(
    source_id: str,
    fixture_handle: str,
    csv_text: str,
    metadata_text: str,
    recording_id: str,
    metadata_path_name: str = "metadata.json",
) -> tuple[FC11RecordedSource, str, str]:
    """Load an FC11 source and its sidecar metadata from in-memory strings.

    Returns (source, csv_content, metadata_json).
    """
    content_checksum = _sha256_hex(csv_text.encode("utf-8"))
    metadata_checksum = _sha256_hex(metadata_text.encode("utf-8"))
    meta_dict = json.loads(metadata_text)
    meta = fc11_metadata_from_dict(meta_dict)
    source = FC11RecordedSource(
        source_id=source_id,
        source_format=meta.source_format,
        fixture_handle=fixture_handle,
        content_checksum=content_checksum,
        metadata_checksum=metadata_checksum,
        source_sampling_rate_hz=meta.sample_rate_hz,
        source_start_timestamp=meta.start_timestamp,
        channel_names=list(meta.channel_names),
        recording_id=recording_id,
        sensor_type="eeg",
        metadata_version=meta.source_format_version,
        metadata={"metadata": meta_dict, "metadata_checksum": metadata_checksum},
        capture_software_version=meta.capture_software_version,
        firmware_version=meta.firmware_version,
        protocol_version=meta.protocol_version,
        samples_per_packet=meta.samples_per_packet,
    )
    return source, csv_text, metadata_text
