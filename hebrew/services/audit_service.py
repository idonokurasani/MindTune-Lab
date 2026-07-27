"""Audit logging for the Hebrew engine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditService:
    """Write structured audit entries."""

    def __init__(self, audit_dir: Path | None = None):
        self.audit_dir = audit_dir or (
            Path(__file__).resolve().parents[2] / "data" / "hebrew" / "audits"
        )
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        category: str,
        entry: dict[str, Any],
    ) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        path = self.audit_dir / f"{category}_{timestamp}.json"
        path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def log_disagreement(self, lemma: str, report: dict[str, Any]) -> Path:
        return self.log(
            "disagreement",
            {
                "lemma": lemma,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report": report,
            },
        )
