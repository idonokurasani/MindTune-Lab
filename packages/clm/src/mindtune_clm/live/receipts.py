"""Per-packet provenance receipts for the CLM-04 live gateway buffer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PacketReceipt:
    """Deterministic receipt emitted when a live packet reaches the buffer."""

    receipt_id: str
    packet_index: int
    received_at: float
    connection_epoch: int
    accepted: bool
    reason: str | None = None
