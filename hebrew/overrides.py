"""Central linguistic override registry.

Corrections made here propagate to all Hebrew Lab consumers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import LinguisticOverride


class OverrideRegistry:
    """Generic registry of manual linguistic corrections."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self.overrides: dict[str, dict[str, Any]] = {}
        if path and path.exists():
            self.load()

    def load(self) -> None:
        if self.path:
            self.overrides = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.overrides, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    def set(
        self,
        target: str,
        field: str,
        value: Any,
        reason: str = "",
        author: str = "",
    ) -> None:
        if target not in self.overrides:
            self.overrides[target] = {}
        self.overrides[target][field] = {
            "value": value,
            "reason": reason,
            "author": author,
        }
        self.save()

    def get(self, target: str, field: str, default: Any = None) -> Any:
        return self.overrides.get(target, {}).get(field, {}).get("value", default)

    def get_override(self, target: str, field: str) -> LinguisticOverride | None:
        entry = self.overrides.get(target, {}).get(field)
        if not entry:
            return None
        return LinguisticOverride(
            scope="global" if "*" in target else "form",
            target=target,
            field=field,
            value=entry["value"],
            reason=entry.get("reason", ""),
            author=entry.get("author", ""),
        )

    def apply_to_record(self, record: Any, target: str) -> Any:
        """Apply all matching overrides to a model record."""
        if target not in self.overrides:
            return record
        for field, override in self.overrides[target].items():
            if hasattr(record, field):
                setattr(record, field, override["value"])
        return record
