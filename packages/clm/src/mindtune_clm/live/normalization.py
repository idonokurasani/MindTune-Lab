"""Live sensor normalization reusing CLM-02B FC11 normalization."""

from __future__ import annotations

from dataclasses import dataclass, field

from mindtune_clm.live.models import LivePacket
from mindtune_clm.replay.fc11.normalization import FC11NormalizationPolicy
from mindtune_clm.replay.models import NormalizedSensorSample, SensorSample
from mindtune_clm.replay.source import RecordedSensorSource


@dataclass(frozen=True)
class LiveNormalizationPolicy(FC11NormalizationPolicy):
    """FC11 normalization adapted for the live packet stream.

    Reuses the exact scaling, timestamp, and provenance logic from
    ``mindtune_clm.replay.fc11.normalization.FC11NormalizationPolicy``.
    """

    policy_id: str = "mindtune_clm.live.fc11.normalization.v1"
    version: str = "1.0.0"
    required_channels: list[str] = field(default_factory=lambda: ["eeg_scaled"])

    def normalize_live(
        self,
        packets: list[LivePacket],
        source: RecordedSensorSource,
    ) -> list[NormalizedSensorSample]:
        """Convert buffered live packets into normalized samples."""
        raw = [
            SensorSample(
                source_sample_index=p.packet_index,
                source_timestamp=p.source_timestamp,
                channel_values=p.channel_values,
                raw_quality=p.raw_quality,
                parsed=p.parsed,
                parse_reason=p.parse_reason,
            )
            for p in packets
        ]
        return self.normalize(raw, source)
