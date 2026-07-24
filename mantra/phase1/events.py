"""Typed event stream for mantra generation and playback."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


class MantraEventType:
    """Phase 1 event type constants."""

    BUILD_STARTED = "mantra_build_started"
    SPEC_VALIDATED = "mantra_spec_validated"
    TIMELINE_COMPILED = "mantra_timeline_compiled"
    SEGMENT_REQUESTED = "mantra_segment_requested"
    SEGMENT_CACHE_HIT = "mantra_segment_cache_hit"
    SEGMENT_GENERATED = "mantra_segment_generated"
    SEGMENT_GENERATION_FAILED = "mantra_segment_generation_failed"
    AUDIO_ASSEMBLED = "mantra_audio_assembled"
    BUILD_COMPLETED = "mantra_build_completed"
    PLAYBACK_STARTED = "mantra_playback_started"
    SEGMENT_STARTED = "mantra_segment_started"
    SEGMENT_COMPLETED = "mantra_segment_completed"
    PLAYBACK_PAUSED = "mantra_playback_paused"
    PLAYBACK_RESUMED = "mantra_playback_resumed"
    PLAYBACK_COMPLETED = "mantra_playback_completed"
    PLAYBACK_STOPPED = "mantra_playback_stopped"


@dataclass
class MantraEvent:
    """A single timestamped event in the mantra lifecycle."""

    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.monotonic)
    event_id: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            import uuid

            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


class EventEmitter:
    """In-memory deterministic event emitter."""

    def __init__(self) -> None:
        self.events: list[MantraEvent] = []

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> MantraEvent:
        event = MantraEvent(event_type=event_type, payload=payload or {})
        self.events.append(event)
        return event

    def to_dicts(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.events]

    def save(self, path: Any) -> None:
        from pathlib import Path

        from .utils import save_json

        save_json(Path(path), self.to_dicts())
