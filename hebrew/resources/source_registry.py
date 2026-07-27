"""Machine-readable source registry and eligibility filtering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..exceptions import ResourceNotFoundError


@dataclass
class SourceRecord:
    source_id: str
    title: str
    local_path: str
    upstream_url: str
    license: str
    license_confidence: str
    attribution_requirements: str
    redistribution_allowed: bool
    derivative_data_implications: str
    commercial_use_status: str
    production_eligibility: str
    unresolved_questions: list[str]

    def is_eligible(self, mode: str = "strict") -> bool:
        if self.production_eligibility == "production_approved":
            return True
        if mode in ("permissive", "internal"):
            return self.production_eligibility in (
                "production_approved",
                "private_research_only",
                "reference_only",
            )
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "local_path": self.local_path,
            "upstream_url": self.upstream_url,
            "license": self.license,
            "license_confidence": self.license_confidence,
            "attribution_requirements": self.attribution_requirements,
            "redistribution_allowed": self.redistribution_allowed,
            "derivative_data_implications": self.derivative_data_implications,
            "commercial_use_status": self.commercial_use_status,
            "production_eligibility": self.production_eligibility,
            "unresolved_questions": self.unresolved_questions,
        }


class SourceRegistry:
    """Load source_registry.json and answer eligibility questions."""

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or self._default_path()
        self._by_id: dict[str, SourceRecord] = {}
        self.load()

    @staticmethod
    def _default_path() -> Path:
        return Path(__file__).resolve().parents[2] / "data" / "hebrew" / "source_registry.json"

    def load(self) -> None:
        if not self.registry_path.exists():
            raise ResourceNotFoundError(f"Source registry not found: {self.registry_path}")
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        for src in data.get("sources", []):
            rec = SourceRecord(**src)
            self._by_id[rec.source_id] = rec

    def get(self, source_id: str) -> SourceRecord:
        if source_id not in self._by_id:
            raise ResourceNotFoundError(f"Unknown source_id: {source_id}")
        return self._by_id[source_id]

    def is_eligible(self, source_id: str, mode: str = "strict") -> bool:
        try:
            return self.get(source_id).is_eligible(mode)
        except ResourceNotFoundError:
            return False

    def eligible_sources(self, mode: str = "strict") -> list[str]:
        return [sid for sid, rec in self._by_id.items() if rec.is_eligible(mode)]

    def production_approved(self) -> list[str]:
        return self.eligible_sources("strict")

    def research_only(self) -> list[str]:
        return [
            sid
            for sid, rec in self._by_id.items()
            if rec.production_eligibility == "private_research_only"
        ]

    def reference_only(self) -> list[str]:
        return [
            sid
            for sid, rec in self._by_id.items()
            if rec.production_eligibility == "reference_only"
        ]

    def blocked_or_unknown(self) -> list[str]:
        return [
            sid
            for sid, rec in self._by_id.items()
            if rec.production_eligibility in ("blocked", "unknown")
        ]

    def filter_records(
        self,
        records: list[dict[str, Any]],
        source_key: str = "source",
        mode: str = "strict",
    ) -> list[dict[str, Any]]:
        return [r for r in records if self.is_eligible(r.get(source_key, ""), mode)]
