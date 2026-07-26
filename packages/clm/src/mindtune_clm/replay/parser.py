"""Deterministic source parsers for CLM-02."""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import StringIO

from mindtune_clm.replay.models import SensorSample
from mindtune_clm.replay.source import RecordedSensorSource


class SensorSourceParser(ABC):
    """Provider contract for deterministic source parsers."""

    parser_id: str
    version: str

    @abstractmethod
    def parse(self, source: RecordedSensorSource, content: str) -> list[SensorSample]:
        """Parse source content into raw samples in original order."""

    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Return the source formats this parser supports."""


@dataclass(frozen=True)
class CSVParser(SensorSourceParser):
    """Parse a CSV recording with header ``timestamp`` plus named channels.

    An optional ``quality`` column may carry per-sample quality flags.
    """

    parser_id: str = "mindtune_clm.replay.csv.v1"
    version: str = "1.0.0"

    def supported_formats(self) -> list[str]:
        return ["csv_v1"]

    def parse(self, source: RecordedSensorSource, content: str) -> list[SensorSample]:  # noqa: C901
        samples: list[SensorSample] = []
        reader = csv.reader(StringIO(content))
        header: list[str] | None = None
        row_index = 0
        for raw_row in reader:
            if not raw_row:
                continue
            if header is None:
                header = [h.strip() for h in raw_row]
                if "timestamp" not in header:
                    # Entire source is malformed if the required header is missing.
                    return []
                continue
            source_timestamp: float | None = None
            channel_values: dict[str, str | float | None] = {}
            raw_quality: str | None = None
            parsed = True
            parse_reason: str | None = None
            for i, cell in enumerate(raw_row):
                if i >= len(header):
                    break
                key = header[i]
                cell = cell.strip()
                if key == "timestamp":
                    try:
                        source_timestamp = float(cell)
                    except ValueError:
                        parsed = False
                        parse_reason = "malformed_timestamp"
                elif key == "quality":
                    raw_quality = cell if cell else None
                else:
                    channel_values[key] = cell if cell else None
            for ch in source.channel_names:
                if ch not in channel_values:
                    channel_values[ch] = None
            samples.append(
                SensorSample(
                    source_sample_index=row_index,
                    source_timestamp=source_timestamp,
                    channel_values=channel_values,
                    raw_quality=raw_quality,
                    parsed=parsed,
                    parse_reason=parse_reason,
                )
            )
            row_index += 1
        return samples
