"""Structured logging for CLM-09 operations."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def _redact(value: Any) -> Any:
    """Redact secret-like fields from values."""
    if isinstance(value, dict):
        return {k: _redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(v) for v in value]
    if isinstance(value, str):
        if any(k in value.lower() for k in ("token", "secret", "password", "api_key", "key")):
            if len(value) > 6:
                return value[:2] + "***" + value[-2:]
        return value
    return value


def _has_mac_address(text: str) -> bool:
    """Detect MAC address patterns."""
    return bool(
        re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", text)
    )


def _sanitize_message(message: str) -> str:
    """Remove MAC addresses and other sensitive patterns."""
    message = re.sub(
        r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})",
        "[MAC_REDACTED]",
        message,
    )
    return message


@dataclass(frozen=True)
class StructuredLogRecord:
    """A single structured log record."""

    timestamp: str
    level: str
    logger: str
    event: str
    request_id: str | None
    session_id: str | None
    experiment_id: str | None
    participant_pseudonym: str | None
    component: str
    error_code: str | None
    causal_event_id: str | None
    release_id: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base = {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger": self.logger,
            "event": self.event,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "experiment_id": self.experiment_id,
            "participant_pseudonym": self.participant_pseudonym,
            "component": self.component,
            "error_code": self.error_code,
            "causal_event_id": self.causal_event_id,
            "release_id": self.release_id,
        }
        base.update(self.payload)
        return cast(dict[str, Any], _redact(base))


class StructuredLogger:
    """CLM-09 structured logger."""

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        output: str | None = None,
        max_payload_bytes: int = 8192,
        include_tracebacks: bool = False,
    ):
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.output = Path(output) if output else None
        self.max_payload_bytes = max_payload_bytes
        self.include_tracebacks = include_tracebacks
        self.release_id = "clm09-local"
        if self.output:
            self.output.parent.mkdir(parents=True, exist_ok=True)

    def _emit(self, level: str, event: str, **kwargs: Any) -> None:
        if getattr(logging, level.upper(), logging.INFO) < self.level:
            return

        payload = dict(kwargs)
        message = payload.pop("message", "")
        message = _sanitize_message(str(message))
        payload["message"] = message

        exc = payload.pop("exception", None)
        if exc and self.include_tracebacks:
            payload["traceback"] = "".join(traceback.format_exception(exc))
        elif exc:
            payload["error_type"] = type(exc).__name__

        # bound payload size
        data = json.dumps(payload, sort_keys=True, default=str)
        if len(data) > self.max_payload_bytes:
            data = data[: self.max_payload_bytes] + "...[TRUNCATED]"
            payload = {
                "message": message,
                "payload_truncated": True,
                "original_hash": hashlib.sha256(data.encode()).hexdigest()[:16],
            }
        else:
            payload = json.loads(data)

        record = StructuredLogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.upper(),
            logger=self.name,
            event=event,
            request_id=kwargs.get("request_id"),
            session_id=kwargs.get("session_id"),
            experiment_id=kwargs.get("experiment_id"),
            participant_pseudonym=kwargs.get("participant_pseudonym"),
            component=kwargs.get("component", "ops"),
            error_code=kwargs.get("error_code"),
            causal_event_id=kwargs.get("causal_event_id"),
            release_id=self.release_id,
            payload=payload,
        )
        serialized = json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=True, default=str)
        print(serialized, file=sys.stderr)
        if self.output:
            with open(self.output, "a", encoding="utf-8") as f:
                f.write(serialized + "\n")

    def debug(self, event: str, **kwargs: Any) -> None:
        self._emit("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._emit("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._emit("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._emit("ERROR", event, **kwargs)

    def bind(self, **context: Any) -> "StructuredLogger":
        """Return a child logger with bound context."""
        child = StructuredLogger(
            self.name,
            level=logging.getLevelName(self.level),
            output=str(self.output) if self.output else None,
            max_payload_bytes=self.max_payload_bytes,
            include_tracebacks=self.include_tracebacks,
        )
        child.release_id = context.get("release_id", self.release_id)
        return child
