"""Persistent SQLite event store for MPE v1.1."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

from mpe.errors import ConcurrencyError, MPEError, ValidationError
from mpe.event_store import SessionSummary
from mpe.events import SUPPORTED_EVENT_TYPES, Event
from mpe.persistence.serializer import from_row, to_row
from mpe.types import SessionID
from mpe.validation import validate_event

_CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    session_sequence_number INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    protocol_version_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    wallclock_at REAL,
    component TEXT NOT NULL,
    component_version TEXT NOT NULL,
    correlation_id TEXT,
    provenance TEXT NOT NULL,
    payload TEXT NOT NULL,
    sensitive INTEGER NOT NULL,
    data_classification TEXT,
    trial_id TEXT,
    block_id TEXT,
    quality_flags TEXT NOT NULL,
    inserted_at REAL NOT NULL,
    UNIQUE (session_id, session_sequence_number)
);
"""


class SQLiteEventStore:
    """Append-only SQLite-backed event store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection = self._connect()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self.path),
            isolation_level=None,
            timeout=5.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        self._init_schema(conn)
        return conn

    @staticmethod
    def _init_schema(conn: sqlite3.Connection) -> None:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            conn.execute(_CREATE_EVENTS_TABLE)
            conn.execute("PRAGMA user_version = 1")
        elif version != 1:
            raise ValidationError(
                f"Unsupported database schema version: {version}"
            )

    def _begin_immediate(self) -> sqlite3.Connection:
        self._conn.execute("BEGIN IMMEDIATE")
        return self._conn

    @staticmethod
    def _map_sqlite_error(exc: Exception) -> Exception:
        if isinstance(exc, sqlite3.OperationalError):
            message = str(exc).lower()
            if "locked" in message or "busy" in message:
                return ConcurrencyError(f"Store lock conflict: {exc}")
            return MPEError(f"SQLite operational error: {exc}")
        if isinstance(exc, sqlite3.IntegrityError):
            return ConcurrencyError(f"Integrity constraint violated: {exc}")
        return exc

    def _validate_event_for_append(self, event: Event) -> None:
        if not isinstance(event, Event):
            raise ValidationError("Can only append Event instances")
        if event.event_type not in SUPPORTED_EVENT_TYPES:
            raise ValidationError(f"Unsupported event type: {event.event_type}")
        validate_event(event)

    def append(self, event: Event, expected_version: int | None = None) -> None:
        self._validate_event_for_append(event)

        with self._lock:
            try:
                self._begin_immediate()
                self._append_in_transaction(event, expected_version)
                self._conn.execute("COMMIT")
            except Exception as exc:
                try:
                    self._conn.execute("ROLLBACK")
                except Exception:
                    pass
                mapped = self._map_sqlite_error(exc)
                if mapped is exc:
                    raise
                raise mapped from exc

    def _append_in_transaction(
        self, event: Event, expected_version: int | None = None
    ) -> None:
        session_id = str(event.session_id)

        last_seq = self._conn.execute(
            "SELECT COALESCE(MAX(session_sequence_number), 0) "
            "FROM events WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]

        if expected_version is not None and expected_version != last_seq:
            raise ConcurrencyError(
                f"Expected version {expected_version}, current {last_seq}"
            )

        if event.session_sequence_number <= last_seq:
            raise ConcurrencyError(
                "Event session_sequence_number must be strictly increasing"
            )

        last_ts = self._conn.execute(
            "SELECT timestamp FROM events WHERE session_id = ? "
            "ORDER BY session_sequence_number DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if last_ts is not None and event.timestamp < last_ts[0]:
            raise ValidationError("Event timestamps must be non-decreasing")

        if event.provenance:
            provenance_ids = [str(e) for e in event.provenance]
            placeholders = ",".join("?" * len(provenance_ids))
            found = self._conn.execute(
                f"SELECT COUNT(*) FROM events WHERE event_id IN ({placeholders}) "
                "AND session_id = ?",
                (*provenance_ids, session_id),
            ).fetchone()[0]
            if found != len(provenance_ids):
                raise ValidationError(
                    f"Provenance event(s) not found for {event.event_id}"
                )

        row = to_row(event)
        columns = ",".join(row.keys())
        placeholders = ",".join("?" * len(row))
        self._conn.execute(
            f"INSERT INTO events ({columns}) VALUES ({placeholders})",
            tuple(row.values()),
        )

    def append_batch(  # noqa: C901
        self, events: list[Event], expected_version: int | None = None
    ) -> None:
        if not events:
            return

        for event in events:
            self._validate_event_for_append(event)

        with self._lock:
            try:
                self._begin_immediate()

                session_id = str(events[0].session_id)
                last_seq = self._conn.execute(
                    "SELECT COALESCE(MAX(session_sequence_number), 0) "
                    "FROM events WHERE session_id = ?",
                    (session_id,),
                ).fetchone()[0]

                if expected_version is not None and expected_version != last_seq:
                    raise ConcurrencyError(
                        f"Expected version {expected_version}, current {last_seq}"
                    )

                last_ts_row = self._conn.execute(
                    "SELECT timestamp FROM events WHERE session_id = ? "
                    "ORDER BY session_sequence_number DESC LIMIT 1",
                    (session_id,),
                ).fetchone()
                last_ts = last_ts_row[0] if last_ts_row else None

                known_ids: set[str] = set()
                for row in self._conn.execute(
                    "SELECT event_id FROM events WHERE session_id = ?", (session_id,)
                ):
                    known_ids.add(row[0])

                for i, event in enumerate(events):
                    expected_seq = last_seq + i + 1
                    if event.session_sequence_number != expected_seq:
                        raise ConcurrencyError(
                            "Batch event session_sequence_number must be contiguous"
                        )

                    if i == 0:
                        if last_ts is not None and event.timestamp < last_ts:
                            raise ValidationError(
                                "Event timestamps must be non-decreasing"
                            )
                    else:
                        if event.timestamp < events[i - 1].timestamp:
                            raise ValidationError(
                                "Event timestamps must be non-decreasing"
                            )

                    if event.provenance:
                        for prov in event.provenance:
                            if str(prov) not in known_ids:
                                raise ValidationError(
                                    f"Provenance event(s) not found for {event.event_id}"
                                )

                    known_ids.add(str(event.event_id))
                    row = to_row(event)
                    columns = ",".join(row.keys())
                    placeholders = ",".join("?" * len(row))
                    self._conn.execute(
                        f"INSERT INTO events ({columns}) VALUES ({placeholders})",
                        tuple(row.values()),
                    )

                self._conn.execute("COMMIT")
            except Exception as exc:
                try:
                    self._conn.execute("ROLLBACK")
                except Exception:
                    pass
                mapped = self._map_sqlite_error(exc)
                if mapped is exc:
                    raise
                raise mapped from exc

    def read(
        self,
        session_id: SessionID,
        from_seq: int | None = None,
        to_seq: int | None = None,
    ) -> list[Event]:
        if from_seq is not None and from_seq < 1:
            raise ValidationError("from_seq must be >= 1")
        if to_seq is not None and to_seq < 1:
            raise ValidationError("to_seq must be >= 1")

        params: list[Any] = [str(session_id)]
        query = "SELECT * FROM events WHERE session_id = ?"

        if from_seq is not None:
            query += " AND session_sequence_number >= ?"
            params.append(from_seq)
        if to_seq is not None:
            query += " AND session_sequence_number <= ?"
            params.append(to_seq)

        query += " ORDER BY session_sequence_number"

        rows = self._conn.execute(query, params).fetchall()
        events: list[Event] = []
        for row in rows:
            event = from_row(row)
            validate_event(event, previous_events=events)
            events.append(event)
        return events

    def get_last_sequence(self, session_id: SessionID) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(session_sequence_number), 0) "
            "FROM events WHERE session_id = ?",
            (str(session_id),),
        ).fetchone()
        return int(row[0])

    def all_events(self) -> list[Event]:
        rows = self._conn.execute(
            "SELECT * FROM events ORDER BY session_id, session_sequence_number"
        ).fetchall()
        events: list[Event] = []
        for row in rows:
            event = from_row(row)
            validate_event(event, previous_events=events)
            events.append(event)
        return events

    def list_sessions(self) -> list[SessionSummary]:
        rows = self._conn.execute(
            "SELECT session_id, COUNT(*) AS event_count, "
            "MAX(session_sequence_number) AS last_sequence "
            "FROM events GROUP BY session_id ORDER BY session_id"
        ).fetchall()
        return [
            SessionSummary(
                session_id=SessionID(row["session_id"]),
                event_count=int(row["event_count"]),
                last_sequence=int(row["last_sequence"]),
            )
            for row in rows
        ]

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> SQLiteEventStore:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
