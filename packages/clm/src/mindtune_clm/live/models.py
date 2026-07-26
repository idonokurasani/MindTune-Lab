"""Immutable data models for the CLM-04 live FC11 sensor gateway."""

from __future__ import annotations

from dataclasses import dataclass, field

from mindtune_clm.live.health import LiveGatewayHealth
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow


@dataclass(frozen=True)
class LivePacket:
    """A single live sensor packet as received from a provider-neutral source."""

    packet_index: int
    source_timestamp: float | None
    channel_values: dict[str, str | float | None]
    raw_quality: str | None = None
    parsed: bool = True
    parse_reason: str | None = None
    connection_epoch: int = 0


@dataclass(frozen=True)
class LiveConnectionReceipt:
    """Receipt returned when a live source connects, reconnects, or fails."""

    epoch: int
    connected_at: float
    source_id: str
    attempts: int
    exhausted: bool = False
    reason: str | None = None


@dataclass
class LiveGatewayResult:
    """Deterministic output of a live gateway execution.

    Converges on the same contracts as CLM-02B replay but stops at
    ``ObservationFrame`` without invoking SpeechGen or audio playback.
    """

    session_id: str
    source_id: str
    observation_frames: list[ObservationFrame] = field(default_factory=list)
    normalized_samples: list[NormalizedSensorSample] = field(default_factory=list)
    quality_assessments: list[QualityAssessment] = field(default_factory=list)
    windows: list[ReplayWindow] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)
    health: LiveGatewayHealth | None = None
    warnings: list[str] = field(default_factory=list)
