"""Canonical event type constants for the CLM-04 live FC11 sensor gateway."""

from __future__ import annotations

from enum import Enum


class LiveEventType(str, Enum):
    """Event type names emitted by the live sensor gateway.

    Each variant is also a CLM-04 MPE event type registered in
    ``mpe.events.SUPPORTED_EVENT_TYPES``.
    """

    GATEWAY_STARTED = "live_gateway_started"
    GATEWAY_PAUSED = "live_gateway_paused"
    GATEWAY_RESUMED = "live_gateway_resumed"
    GATEWAY_STOPPED = "live_gateway_stopped"
    GATEWAY_COMPLETED = "live_gateway_completed"
    GATEWAY_HEALTH_CHANGED = "live_gateway_health_changed"

    SENSOR_SOURCE_CONNECTED = "live_sensor_source_connected"
    SENSOR_SOURCE_DISCONNECTED = "live_sensor_source_disconnected"
    SENSOR_SOURCE_RECONNECT_ATTEMPT = "live_sensor_source_reconnect_attempt"
    SENSOR_SOURCE_RECONNECT_EXHAUSTED = "live_sensor_source_reconnect_exhausted"
    SENSOR_SOURCE_EPOCH_CHANGED = "live_sensor_source_epoch_changed"

    PACKET_RECEIVED = "live_packet_received"
    PACKET_LATE = "live_packet_late"
    PACKET_DUPLICATE = "live_packet_duplicate"
    BUFFER_OVERFLOW = "live_buffer_overflow"

    PACKET_NORMALIZED = "live_packet_normalized"
    QUALITY_ASSESSED = "live_quality_assessed"
    WINDOW_CREATED = "live_window_created"
    WINDOW_REJECTED = "live_window_rejected"
    OBSERVATION_FRAME_GENERATED = "live_observation_frame_generated"

    @classmethod
    def all(cls) -> frozenset[str]:
        """Return all supported CLM-04 event type strings."""
        return frozenset(member.value for member in cls)
