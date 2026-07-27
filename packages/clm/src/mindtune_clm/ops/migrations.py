"""SQLite schema migration helpers."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Migration:
    """A single migration."""

    version: str
    name: str
    sql: str

    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()[:16]


class MigrationManager:
    """Ordered SQLite migrations with checksum and transaction safety."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.migrations: list[Migration] = []

    def register(self, migration: Migration) -> None:
        self.migrations.append(migration)

    def _ensure_meta(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clm09_migrations (
                version TEXT PRIMARY KEY,
                name TEXT,
                checksum TEXT,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def _applied_versions(self, conn: sqlite3.Connection) -> dict[str, str]:
        try:
            rows = conn.execute(
                "SELECT version, checksum FROM clm09_migrations"
            ).fetchall()
            return {row[0]: row[1] for row in rows}
        except sqlite3.OperationalError:
            return {}

    def current(self) -> dict[str, Any]:
        """Return current migration status without changing anything."""
        if not self.db_path.exists():
            return {"status": "no_database", "applied": [], "pending": [m.version for m in self.migrations]}
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._ensure_meta(conn)
            applied = self._applied_versions(conn)
            pending = [m.version for m in self.migrations if m.version not in applied]
            return {
                "status": "current" if not pending else "pending",
                "applied": list(applied.keys()),
                "pending": pending,
            }
        finally:
            conn.close()

    def migrate(self, dry_run: bool = False) -> dict[str, Any]:
        """Apply pending migrations in a transaction."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._ensure_meta(conn)
            applied = self._applied_versions(conn)
            pending = [m for m in self.migrations if m.version not in applied]

            if not pending:
                return {"status": "current", "applied": list(applied.keys()), "pending": []}

            if dry_run:
                return {
                    "status": "dry_run",
                    "would_apply": [m.version for m in pending],
                    "current_applied": list(applied.keys()),
                }

            conn.execute("BEGIN")
            try:
                for migration in pending:
                    conn.executescript(migration.sql)
                    conn.execute(
                        "INSERT INTO clm09_migrations (version, name, checksum) VALUES (?, ?, ?)",
                        (migration.version, migration.name, migration.checksum()),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            return {
                "status": "migrated",
                "applied": [m.version for m in self.migrations],
                "pending": [],
            }
        finally:
            conn.close()

    def validate_checksums(self) -> bool:
        """Validate that applied migration checksums match expected."""
        if not self.db_path.exists():
            return True
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._ensure_meta(conn)
            applied = self._applied_versions(conn)
            for migration in self.migrations:
                if migration.version in applied:
                    if applied[migration.version] != migration.checksum():
                        return False
            return True
        finally:
            conn.close()
