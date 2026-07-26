"""Provider-neutral live sensor source abstraction and synthetic source."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from mindtune_clm.live.models import LivePacket
from mindtune_clm.replay.source import RecordedSensorSource


class LiveSensorSource(ABC):
    """Provider-neutral live sensor source contract for CLM-04.

    Concrete sources wrap a recorded fixture (FC11) or a deterministic
    generator (Synthetic).  They expose the same ``RecordedSensorSource``
    identity that CLM-02B normalization and windowing policies already expect.
    """

    def __init__(
        self,
        source_id: str,
        channel_names: list[str],
        source_sampling_rate_hz: float = 10.0,
        source_start_timestamp: float = 0.0,
        max_reconnect_attempts: int = 3,
    ) -> None:
        self.source_id = source_id
        self.channel_names = list(channel_names)
        self.source_sampling_rate_hz = source_sampling_rate_hz
        self.source_start_timestamp = source_start_timestamp
        self.max_reconnect_attempts = max_reconnect_attempts
        self._connected = False
        self._epoch = 0
        self._reconnect_attempts = 0
        self.recorded_source: RecordedSensorSource | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def epoch(self) -> int:
        return self._epoch

    @property
    def reconnect_attempts(self) -> int:
        return self._reconnect_attempts

    @abstractmethod
    def _next_packet(self) -> LivePacket | None:
        """Return the next live packet or ``None`` when the source ends."""

    def connect(self) -> bool:
        """Open the source, tracking epochs and bounded reconnect attempts."""
        if not self._connected and self._reconnect_attempts >= self.max_reconnect_attempts:
            return False
        if not self._connected:
            self._epoch += 1
            if self._epoch > 1:
                self._reconnect_attempts += 1
            self._connected = True
        return True

    def disconnect(self) -> None:
        """Close the current connection without resetting epoch history."""
        self._connected = False

    def reset(self) -> None:
        """Reset all connection state (used for tests and fresh sessions)."""
        self._connected = False
        self._epoch = 0
        self._reconnect_attempts = 0

    def receive(self) -> LivePacket | None:
        """Receive one packet, stamping it with the current connection epoch."""
        if not self._connected:
            return None
        pkt = self._next_packet()
        if pkt is None:
            self._connected = False
            return None
        return LivePacket(
            packet_index=pkt.packet_index,
            source_timestamp=pkt.source_timestamp,
            channel_values=pkt.channel_values,
            raw_quality=pkt.raw_quality,
            parsed=pkt.parsed,
            parse_reason=pkt.parse_reason,
            connection_epoch=self._epoch,
        )


class SyntheticLiveSource(LiveSensorSource):
    """Deterministic synthetic EEG source for reproducible live tests."""

    def __init__(
        self,
        source_id: str = "synthetic",
        duration: float = 10.0,
        packet_interval: float = 0.1,
        seed: int = 0,
        source_start_timestamp: float = 0.0,
        max_reconnect_attempts: int = 3,
    ) -> None:
        self.duration = duration
        self.packet_interval = packet_interval
        self.seed = seed
        self._sample_index = 0
        self._rng = random.Random(seed)
        channel_names = [
            "eeg_scaled",
            "attention_score_smoothed",
            "meditation_score_smoothed",
            "packet_index",
            "artifact_flag",
            "movement_flag",
            "packet_loss",
        ]
        super().__init__(
            source_id=source_id,
            channel_names=channel_names,
            source_sampling_rate_hz=1.0 / packet_interval,
            source_start_timestamp=source_start_timestamp,
            max_reconnect_attempts=max_reconnect_attempts,
        )
        self.recorded_source = RecordedSensorSource(
            source_id=source_id,
            source_format="synthetic_live",
            fixture_handle="synthetic.csv",
            content_checksum="",
            source_sampling_rate_hz=self.source_sampling_rate_hz,
            source_start_timestamp=self.source_start_timestamp,
            channel_names=list(self.channel_names),
            sensor_type="eeg",
            metadata={"synthetic": True, "seed": self.seed},
        )

    def _next_packet(self) -> LivePacket | None:
        t = self.source_start_timestamp + (self._sample_index * self.packet_interval)
        if t >= self.source_start_timestamp + self.duration:
            return None
        self._sample_index += 1
        noise = self._rng.uniform(-0.05, 0.05)
        return LivePacket(
            packet_index=self._sample_index - 1,
            source_timestamp=t,
            channel_values={
                "eeg_scaled": 78.5 + noise,
                "attention_score_smoothed": 48.0,
                "meditation_score_smoothed": 55.0,
                "packet_index": float(self._sample_index - 1),
                "artifact_flag": 0.0,
                "movement_flag": 0.0,
                "packet_loss": 0.0,
            },
            raw_quality="5",
            parsed=True,
        )
