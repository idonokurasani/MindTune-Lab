"""FC11 live source wraps the existing CSV parser and emits live packets."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO

from mindtune_clm.live.models import LivePacket
from mindtune_clm.live.source import LiveSensorSource
from mindtune_clm.replay.fc11.parser import FC11CSVParser
from mindtune_clm.replay.models import SensorSample
from mindtune_clm.replay.source import RecordedSensorSource


class FC11LiveSource(LiveSensorSource):
    """Wrap an FC11 EEG CSV fixture and emit the rows as live packets.

    Reuses ``FC11CSVParser`` for parsing, timestamp validation, and rejection
    marking.  Each (re)connect rewinds the packet cursor so the same fixture
    can exercise connection epochs deterministically.
    """

    def __init__(
        self,
        csv_text: str,
        source_id: str = "fc11_live",
        max_reconnect_attempts: int = 3,
    ) -> None:
        self._csv_text = csv_text
        self._samples: list[SensorSample] = []
        self._index = 0
        self._parser = FC11CSVParser()
        header: list[str] = []
        for raw in csv.reader(StringIO(csv_text)):
            if raw:
                header = [h.strip() for h in raw]
                break
        quality_col = "signal_quality"
        channel_names = [h for h in header if h != "timestamp"]
        content_checksum = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
        recorded_source = RecordedSensorSource(
            source_id=source_id,
            source_format="fc11_eeg_csv_v1",
            fixture_handle="live_fc11.csv",
            content_checksum=content_checksum,
            source_sampling_rate_hz=10.0,
            source_start_timestamp=0.0,
            channel_names=channel_names,
            sensor_type="eeg",
            metadata={"quality_column": quality_col},
        )
        super().__init__(
            source_id=source_id,
            channel_names=channel_names,
            source_sampling_rate_hz=10.0,
            source_start_timestamp=0.0,
            max_reconnect_attempts=max_reconnect_attempts,
        )
        self.recorded_source = recorded_source
        self._samples = self._parser.parse(self.recorded_source, csv_text)

    def connect(self) -> bool:
        """Rewind to the first packet on each (re)connect."""
        ok = super().connect()
        if ok:
            self._index = 0
        return ok

    def _next_packet(self) -> LivePacket | None:
        if self._index >= len(self._samples):
            return None
        sample = self._samples[self._index]
        self._index += 1
        return LivePacket(
            packet_index=sample.source_sample_index,
            source_timestamp=sample.source_timestamp,
            channel_values=sample.channel_values,
            raw_quality=sample.raw_quality,
            parsed=sample.parsed,
            parse_reason=sample.parse_reason,
        )
