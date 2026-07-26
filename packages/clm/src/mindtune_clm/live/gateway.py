"""Live FC11 sensor gateway for CLM-04.

Converges on the same NormalizedSensorSample, QualityAssessment, ReplayWindow,
and ObservationFrame contracts as CLM-02B replay, then stops.  No SpeechGen,
audio playback, or separate live policy engine is invoked.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from mindtune_clm.live.buffer import PacketBuffer
from mindtune_clm.live.clock import LiveClock
from mindtune_clm.live.events import LiveEventType
from mindtune_clm.live.health import LiveGatewayHealth, LiveHealthStatus
from mindtune_clm.live.models import LiveGatewayResult, LivePacket
from mindtune_clm.live.normalization import LiveNormalizationPolicy
from mindtune_clm.live.quality import LiveQualityPolicy
from mindtune_clm.live.receipts import PacketReceipt
from mindtune_clm.live.source import LiveSensorSource
from mindtune_clm.live.windows import LiveWindowingPolicy
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.replay.adapter import to_observation_frame
from mindtune_clm.replay.features import FeaturePolicy
from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow
from mindtune_clm.replay.windows import WindowPolicy
from mpe.enums import DataClassification
from mpe.event_store import InMemoryEventStore
from mpe.events import Event
from mpe.types import EventID, ProtocolVersionID, SessionID, make_id


@dataclass
class LiveGateway:
    """Provider-neutral live gateway that materializes ObservationFrames."""

    source: LiveSensorSource
    normalizer: LiveNormalizationPolicy = field(default_factory=LiveNormalizationPolicy)
    quality: LiveQualityPolicy = field(default_factory=LiveQualityPolicy)
    windowing: LiveWindowingPolicy = field(
        default_factory=lambda: LiveWindowingPolicy(
            WindowPolicy(
                policy_id="live_fc11_window.v1",
                version="1.0.0",
                window_duration_s=2.0,
                step_duration_s=1.0,
                min_accepted_sample_count=12,
                partial_final_window=True,
                feature_policy=FeaturePolicy(
                    policy_id="live_fc11_features.v1",
                    version="1.0.0",
                    primary_channel="eeg_scaled",
                    normalization_mode="coefficient_of_variation",
                ),
            )
        )
    )
    buffer: PacketBuffer = field(default_factory=PacketBuffer)
    clock: LiveClock = field(default_factory=LiveClock)
    store: InMemoryEventStore = field(default_factory=InMemoryEventStore)
    gateway_id: str = field(default_factory=lambda: f"clm04-{uuid.uuid4()}")
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    health: LiveGatewayHealth = field(init=False)
    _state: str = field(default="stopped", init=False, repr=False)
    _seq: int = field(default=0, init=False, repr=False)
    _last_event_id: EventID | None = field(default=None, init=False, repr=False)
    _samples: list[NormalizedSensorSample] = field(default_factory=list, init=False, repr=False)
    _assessments: list[QualityAssessment] = field(
        default_factory=list, init=False, repr=False
    )
    _frames: list[ObservationFrame] = field(default_factory=list, init=False, repr=False)
    _frame_counter: int = field(default=0, init=False, repr=False)
    _warnings: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.health = LiveGatewayHealth(health_id=f"health-{self.gateway_id}")

    # ------------------------------------------------------------------ #
    # Session lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> bool:
        """Connect the source, reset state, and begin the live session."""
        if self._state in {"running", "paused"}:
            return True
        if not self.source.connect():
            self.health = (
                self.health.transition(LiveHealthStatus.ERROR)
                .add_warning("reconnect attempts exhausted")
            )
            self._emit(
                LiveEventType.SENSOR_SOURCE_RECONNECT_EXHAUSTED,
                {"source_id": self.source.source_id, "gateway_id": self.gateway_id},
            )
            return False

        self.buffer.reset(self.source.epoch)
        self.clock.reset(self.source.source_start_timestamp)
        self._state = "running"
        self._samples.clear()
        self._assessments.clear()
        self._frames.clear()
        self._frame_counter = 0
        self._warnings.clear()
        self.health = self.health.transition(LiveHealthStatus.RUNNING)
        self._emit(
            LiveEventType.SENSOR_SOURCE_CONNECTED,
            {
                "source_id": self.source.source_id,
                "epoch": self.source.epoch,
                "gateway_id": self.gateway_id,
            },
        )
        self._emit(
            LiveEventType.GATEWAY_STARTED,
            {"gateway_id": self.gateway_id, "session_id": self.session_id},
        )
        return True

    def pause(self) -> None:
        """Pause ingestion without closing the source connection."""
        if self._state == "running":
            self._state = "paused"
            self.health = self.health.transition(LiveHealthStatus.PAUSED)
            self._emit(
                LiveEventType.GATEWAY_PAUSED,
                {"gateway_id": self.gateway_id, "session_id": self.session_id},
            )

    def resume(self) -> None:
        """Resume a paused gateway."""
        if self._state == "paused":
            self._state = "running"
            self.health = self.health.transition(LiveHealthStatus.RUNNING)
            self._emit(
                LiveEventType.GATEWAY_RESUMED,
                {"gateway_id": self.gateway_id, "session_id": self.session_id},
            )

    def stop(self) -> None:
        """Stop the gateway and close the source."""
        self._state = "stopped"
        self.source.disconnect()
        self.health = self.health.transition(LiveHealthStatus.STOPPED)
        self._emit(
            LiveEventType.SENSOR_SOURCE_DISCONNECTED,
            {"source_id": self.source.source_id, "gateway_id": self.gateway_id},
        )
        self._emit(
            LiveEventType.GATEWAY_STOPPED,
            {"gateway_id": self.gateway_id, "session_id": self.session_id},
        )

    # ------------------------------------------------------------------ #
    # Packet ingestion
    # ------------------------------------------------------------------ #

    def tick(self) -> bool:
        """Receive and buffer one packet.  Returns ``False`` when the source ends."""
        if self._state != "running":
            return False
        pkt = self.source.receive()
        if pkt is None:
            return False
        receipt = self.buffer.push(pkt)
        return self._handle_receipt(receipt, pkt)

    def ingest(self, packet: LivePacket) -> bool:
        """Inject a packet directly (used for tests and deterministic replay)."""
        if self._state == "stopped":
            return False
        receipt = self.buffer.push(packet)
        return self._handle_receipt(receipt, packet)

    def _handle_receipt(self, receipt: PacketReceipt, pkt: LivePacket) -> bool:
        if receipt.accepted:
            self.health = self.health.with_counters(packets_received=1)
            self._emit(
                LiveEventType.PACKET_RECEIVED,
                {
                    "packet_index": pkt.packet_index,
                    "source_timestamp": pkt.source_timestamp,
                    "epoch": pkt.connection_epoch,
                    "gateway_id": self.gateway_id,
                },
            )
            return True

        if receipt.reason == "late_packet":
            self.health = self.health.with_counters(packets_late=1)
            self._emit(
                LiveEventType.PACKET_LATE,
                {
                    "packet_index": pkt.packet_index,
                    "source_timestamp": pkt.source_timestamp,
                    "epoch": pkt.connection_epoch,
                    "gateway_id": self.gateway_id,
                },
            )
            self._warnings.append(f"late_packet:{pkt.packet_index}")
        elif receipt.reason == "duplicate_packet":
            self.health = self.health.with_counters(packets_duplicate=1)
            self._emit(
                LiveEventType.PACKET_DUPLICATE,
                {
                    "packet_index": pkt.packet_index,
                    "source_timestamp": pkt.source_timestamp,
                    "epoch": pkt.connection_epoch,
                    "gateway_id": self.gateway_id,
                },
            )
            self._warnings.append(f"duplicate_packet:{pkt.packet_index}")
        elif receipt.reason == "buffer_overflow":
            self.health = self.health.with_counters(buffer_overflows=1)
            self._emit(
                LiveEventType.BUFFER_OVERFLOW,
                {
                    "packet_index": pkt.packet_index,
                    "source_timestamp": pkt.source_timestamp,
                    "epoch": pkt.connection_epoch,
                    "gateway_id": self.gateway_id,
                },
            )
            self._warnings.append(f"buffer_overflow:{pkt.packet_index}")

        return False

    # ------------------------------------------------------------------ #
    # Window / frame materialization
    # ------------------------------------------------------------------ #

    def run(self) -> LiveGatewayResult:
        """Ingest all available packets, flush windows and frames, then stop."""
        if not self.start():
            return self._result([])
        while self.tick():
            pass
        result = self.flush()
        self.stop()
        return result

    def flush(self) -> LiveGatewayResult:
        """Normalize, assess, window, and produce observation frames."""
        packets = self.buffer.pop_all()
        if packets:
            self._process_packets(packets)

        if not self._samples:
            return self._result([])

        windows = self.windowing.make_windows(
            self.session_id,
            self._samples,
            self._assessments,
            self.quality,
        )
        sample_by_id = {s.normalized_sample_id: s for s in self._samples}

        for window in windows:
            self._emit_window_event(window)

        new_frames = self._frames_from_windows(windows, sample_by_id)
        self._frames.extend(new_frames)

        self._emit(
            LiveEventType.GATEWAY_COMPLETED,
            {
                "gateway_id": self.gateway_id,
                "session_id": self.session_id,
                "frame_count": len(self._frames),
            },
        )

        return self._result(self._frames)

    def _process_packets(self, packets: list[LivePacket]) -> None:
        if self.source.recorded_source is None:
            raise RuntimeError("Source has no recorded source identity")
        normalized = self.normalizer.normalize_live(packets, self.source.recorded_source)
        assessments = self.quality.assess_samples(normalized)
        self._samples.extend(normalized)
        self._assessments.extend(assessments)

        for n in normalized:
            for op in n.normalization_operations:
                if any(
                    token in op
                    for token in ["rejected", "failed", "malformed", "regression", "missing_required"]
                ):
                    self._warnings.append(f"{n.normalized_sample_id}:{op}")

        self._emit(
            LiveEventType.PACKET_NORMALIZED,
            {
                "gateway_id": self.gateway_id,
                "session_id": self.session_id,
                "normalized_sample_count": len(normalized),
            },
        )
        self._emit(
            LiveEventType.QUALITY_ASSESSED,
            {
                "gateway_id": self.gateway_id,
                "session_id": self.session_id,
                "assessment_count": len(assessments),
                "accepted_count": sum(1 for a in assessments if a.accepted),
            },
        )

    def _emit_window_event(self, window: ReplayWindow) -> None:
        payload = {
            "gateway_id": self.gateway_id,
            "session_id": self.session_id,
            "window_id": window.window_id,
            "start_replay_timestamp": window.start_replay_timestamp,
            "end_replay_timestamp": window.end_replay_timestamp,
            "accepted_sample_count": window.accepted_sample_count,
            "rejected_sample_count": window.rejected_sample_count,
            "accepted": window.accepted,
            "reason_codes": window.reason_codes,
        }
        if window.accepted:
            self._emit(LiveEventType.WINDOW_CREATED, payload)
        else:
            self._emit(LiveEventType.WINDOW_REJECTED, payload)

    def _frames_from_windows(
        self,
        windows: list[ReplayWindow],
        samples: dict[str, NormalizedSensorSample],
    ) -> list[ObservationFrame]:
        frames: list[ObservationFrame] = []
        for window in windows:
            if not window.accepted:
                continue
            self._frame_counter += 1
            frame = to_observation_frame(
                window,
                samples,
                replay_id=self.session_id,
                sequence_number=self._frame_counter,
                eeg_channel="eeg_scaled",
                eeg_stability_feature="signal_stability",
            )
            frames.append(frame)
            self._emit(
                LiveEventType.OBSERVATION_FRAME_GENERATED,
                {
                    "gateway_id": self.gateway_id,
                    "session_id": self.session_id,
                    "observation_frame_id": frame.observation_frame_id,
                    "control_cycle_id": frame.control_cycle_id,
                    "window_id": window.window_id,
                    "eeg_stability": frame.eeg_stability,
                    "eeg_quality": frame.eeg_quality,
                    "available_modalities": frame.available_modalities,
                },
            )
        return frames

    def _result(self, frames: list[ObservationFrame]) -> LiveGatewayResult:
        return LiveGatewayResult(
            session_id=self.session_id,
            source_id=self.source.source_id,
            observation_frames=frames,
            normalized_samples=list(self._samples),
            quality_assessments=list(self._assessments),
            windows=self._collect_windows(),
            event_ids=[str(e.event_id) for e in self.store.read(SessionID(self.session_id))],
            health=self.health,
            warnings=list(self._warnings),
        )

    def _collect_windows(self) -> list[ReplayWindow]:
        if not self._samples:
            return []
        return self.windowing.make_windows(
            self.session_id,
            self._samples,
            self._assessments,
            self.quality,
        )

    # ------------------------------------------------------------------ #
    # Event emission
    # ------------------------------------------------------------------ #

    def _emit(self, event_type: LiveEventType, payload: dict) -> Event:
        self._seq += 1
        timestamp = self.clock.semantic_time + (self._seq * 0.001)
        provenance: list[EventID] = []
        if self._last_event_id is not None:
            provenance = [self._last_event_id]

        event = Event(
            event_id=make_id(EventID),
            event_type=event_type.value,
            schema_version="1.1",
            session_id=SessionID(self.session_id),
            session_sequence_number=self._seq,
            protocol_version_id=ProtocolVersionID("clm-04-v1.0.0"),
            timestamp=timestamp,
            component="clm04_live",
            component_version="1.0.0",
            provenance=provenance,
            payload=payload,
            data_classification=DataClassification.INTERNAL,
        )
        self.store.append(event)
        self._last_event_id = event.event_id
        return event
