"""Graceful shutdown helpers."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class ShutdownController:
    """Bounded graceful shutdown orchestrator."""

    phases: list[str]
    timeout_s: float
    _handlers: dict[str, Callable[[], None]] = field(default_factory=dict)
    _results: list[dict[str, Any]] = field(default_factory=list)

    def register(self, phase: str, handler: Callable[[], None]) -> None:
        self._handlers[phase] = handler

    def shutdown(self, receipt_path: Path | None = None) -> dict[str, Any]:
        """Run shutdown phases in order with a global timeout."""
        deadline = time.monotonic() + self.timeout_s
        for phase in self.phases:
            if time.monotonic() > deadline:
                self._results.append({"phase": phase, "ok": False, "message": "timeout"})
                break
            try:
                handler = self._handlers.get(phase)
                if handler:
                    handler()
                self._results.append({"phase": phase, "ok": True})
            except Exception as exc:
                self._results.append({"phase": phase, "ok": False, "message": str(exc)})

        receipt = {
            "timestamp": time.time(),
            "timeout_s": self.timeout_s,
            "phases": self._results,
            "completed": all(r["ok"] for r in self._results),
        }
        if receipt_path:
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps(receipt, sort_keys=True, default=str), encoding="utf-8")
        return receipt
