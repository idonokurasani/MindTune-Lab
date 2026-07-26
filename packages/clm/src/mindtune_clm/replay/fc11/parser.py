"""Versioned FC11 recorded EEG CSV parser for CLM-02B."""

from __future__ import annotations

import csv
from io import StringIO

from mindtune_clm.replay.models import SensorSample
from mindtune_clm.replay.parser import SensorSourceParser
from mindtune_clm.replay.source import RecordedSensorSource


class FC11CSVParser(SensorSourceParser):
    """Parse the FC11 EEG CSV export paired with an FC11 metadata sidecar."""

    parser_id: str = "mindtune_clm.replay.fc11_csv.v1"
    version: str = "1.0.0"

    def supported_formats(self) -> list[str]:
        return ["fc11_eeg_csv_v1"]

    def parse(self, source: RecordedSensorSource, content: str) -> list[SensorSample]:  # noqa: C901
        samples: list[SensorSample] = []
        reader = csv.reader(StringIO(content))
        header: list[str] | None = None
        row_index = 1
        previous_timestamp: float | None = None
        seen_timestamps: set[float] = set()

        quality_col = source.metadata.get("quality_column", "signal_quality")
        required_channels = set(source.channel_names) - {quality_col}

        for raw_row in reader:
            if not raw_row:
                continue
            if header is None:
                header = [h.strip() for h in raw_row]
                if "timestamp" not in header:
                    return []
                continue

            source_timestamp: float | None = None
            channel_values: dict[str, str | float | None] = {}
            raw_quality: str | None = None
            parsed = True
            parse_reason: str | None = None

            cells = [c.strip() for c in raw_row]
            if len(cells) != len(header):
                parsed = False
                parse_reason = "fc11_malformed_record"

            for i, key in enumerate(header):
                if i >= len(cells):
                    break
                cell = cells[i]
                if key == "timestamp":
                    if cell == "":
                        source_timestamp = None
                    else:
                        try:
                            source_timestamp = float(cell)
                        except ValueError:
                            parsed = False
                            parse_reason = "fc11_malformed_record"
                            source_timestamp = None
                elif key == quality_col:
                    raw_quality = cell if cell else None
                else:
                    channel_values[key] = cell if cell else None

            if parsed and source_timestamp is None:
                parsed = False
                parse_reason = "fc11_missing_timestamp"

            if parsed and source_timestamp is not None:
                if previous_timestamp is not None and source_timestamp < previous_timestamp:
                    parsed = False
                    parse_reason = "fc11_timestamp_regression"
                elif source_timestamp in seen_timestamps:
                    parsed = False
                    parse_reason = "fc11_duplicate_timestamp"
                else:
                    seen_timestamps.add(source_timestamp)
                    previous_timestamp = source_timestamp

            missing = required_channels - set(channel_values.keys())
            for ch in source.channel_names:
                if ch not in channel_values:
                    channel_values[ch] = None

            if parsed and missing:
                parsed = False
                parse_reason = "fc11_missing_required_channel"

            if parsed and any(channel_values.get(ch) in (None, "") for ch in required_channels):
                parsed = False
                parse_reason = "fc11_missing_required_channel"

            samples.append(
                SensorSample(
                    source_sample_index=row_index - 1,
                    source_timestamp=source_timestamp,
                    channel_values=channel_values,
                    raw_quality=raw_quality,
                    parsed=parsed,
                    parse_reason=parse_reason,
                )
            )
            row_index += 1

        return samples
