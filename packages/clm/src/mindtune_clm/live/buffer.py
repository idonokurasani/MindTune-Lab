"""Live packet buffer with overflow, duplicate, and late-packet detection."""

from __future__ import annotations

from dataclasses import dataclass, field

from mindtune_clm.live.models import LivePacket
from mindtune_clm.live.receipts import PacketReceipt


@dataclass
class PacketBuffer:
    """Provider-neutral live packet buffer.

    Detects duplicate timestamps, non-monotonic (late) packets, and bounded
    overflow.  Per-epoch reset clears the ordering state when the sensor
    reconnects.
    """

    max_size: int = 1000
    _buffer: list[LivePacket] = field(default_factory=list, repr=False)
    _seen_timestamps: set[float] = field(default_factory=set, repr=False)
    _last_timestamp: float | None = field(default=None, init=False, repr=False)
    _epoch: int = field(default=0, init=False, repr=False)
    _receipt_counter: int = field(default=0, init=False, repr=False)

    def reset(self, epoch: int) -> None:
        """Clear buffered packets and per-epoch ordering state."""
        self._buffer.clear()
        self._seen_timestamps.clear()
        self._last_timestamp = None
        self._epoch = epoch

    def push(self, packet: LivePacket) -> PacketReceipt:
        """Insert a packet into the buffer and return a deterministic receipt.

        Out-of-order packets are rejected without entering the buffer so that
        downstream normalization and quality policies see only monotonic
        sequences.  Duplicate timestamps and buffer-full conditions are
        reported explicitly through the receipt reason code.
        """
        self._receipt_counter += 1
        receipt_id = f"recv-{self._epoch}-{self._receipt_counter}"
        received_at = packet.source_timestamp if packet.source_timestamp is not None else 0.0

        if len(self._buffer) >= self.max_size:
            return PacketReceipt(
                receipt_id=receipt_id,
                packet_index=packet.packet_index,
                received_at=received_at,
                connection_epoch=self._epoch,
                accepted=False,
                reason="buffer_overflow",
            )

        ts = packet.source_timestamp
        if ts is not None:
            if self._last_timestamp is not None and ts < self._last_timestamp:
                return PacketReceipt(
                    receipt_id=receipt_id,
                    packet_index=packet.packet_index,
                    received_at=received_at,
                    connection_epoch=self._epoch,
                    accepted=False,
                    reason="late_packet",
                )
            if ts in self._seen_timestamps:
                return PacketReceipt(
                    receipt_id=receipt_id,
                    packet_index=packet.packet_index,
                    received_at=received_at,
                    connection_epoch=self._epoch,
                    accepted=False,
                    reason="duplicate_packet",
                )

        stamped = LivePacket(
            packet_index=packet.packet_index,
            source_timestamp=packet.source_timestamp,
            channel_values=dict(packet.channel_values),
            raw_quality=packet.raw_quality,
            parsed=packet.parsed,
            parse_reason=packet.parse_reason,
            connection_epoch=self._epoch,
        )
        self._buffer.append(stamped)

        if ts is not None:
            self._seen_timestamps.add(ts)
            self._last_timestamp = ts

        return PacketReceipt(
            receipt_id=receipt_id,
            packet_index=packet.packet_index,
            received_at=received_at,
            connection_epoch=self._epoch,
            accepted=True,
            reason="accepted",
        )

    def pop_all(self) -> list[LivePacket]:
        """Return and clear all buffered packets in arrival order."""
        packets = list(self._buffer)
        self._buffer.clear()
        return packets

    def __len__(self) -> int:
        return len(self._buffer)
