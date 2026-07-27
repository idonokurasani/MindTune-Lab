"""Persistent SQLite event store.

Database layout v2 (`PRAGMA user_version = 2`) carries the integrity and
provenance columns. Layout v1 databases stay readable and are closed to append
until they are structurally migrated (ADR-0001 sec. 2.11); the layout version
describes storage only, while integrity status is decided per stream.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

from mpe.errors import ConcurrencyError, IntegrityError, MPEError, ValidationError
from mpe.event_store import SessionSummary
from mpe.events import SUPPORTED_EVENT_TYPES, Event
from mpe.integrity import (
    chain_event,
    is_chained_schema,
    verify_link,
    verify_stream,
)
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
    content_digest TEXT,
    previous_digest TEXT,
    writer_revision TEXT,
    inserted_at REAL NOT NULL,
    UNIQUE (session_id, session_sequence_number)
);
"""

CURRENT_DATABASE_VERSION = 2
_V2_COLUMNS = ("content_digest", "previous_digest", "writer_revision")


def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Structurally migrate a layout-v1 database in place.

    Adds the nullable columns and bumps `PRAGMA user_version`. Historical events
    are never rewritten and are never retro-chained: existing schema-1.1 streams
    stay byte-identical and keep reporting `integrity: unavailable`.
    """
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == CURRENT_DATABASE_VERSION:
        return
    if version != 1:
        raise ValidationError(f"Cannot migrate database schema version {version}")

    existing = {row["name"] for row in conn.execute("PRAGMA table_info(events)")}
    for column in _V2_COLUMNS:
        if column not in existing:
            conn.execute(f"ALTER TABLE events ADD COLUMN {column} TEXT")
    conn.execute(f"PRAGMA user_version = {CURRENT_DATABASE_VERSION}")


class SQLiteEventStore:
    """Append-only SQLite-backed event store."""

    def __init__(self, path: str | Path, *, migrate: bool = False) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._migrate = migrate
        self._conn: sqlite3.Connection = self._connect()
        self.database_version: int = int(
            self._conn.execute("PRAGMA user_version").fetchone()[0]
        )

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(self.path),
            isolation_level=None,
            timeout=5.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        self._init_schema(conn)
        return conn

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            conn.execute(_CREATE_EVENTS_TABLE)
            conn.execute(f"PRAGMA user_version = {CURRENT_DATABASE_VERSION}")
        elif version == 1:
            if self._migrate:
                migrate_v1_to_v2(conn)
        elif version != CURRENT_DATABASE_VERSION:
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
        if self.database_version != CURRENT_DATABASE_VERSION:
            raise IntegrityError(
                f"Database at {self.path} is on layout v{self.database_version} and is "
                "closed to append; migrate it to v2 first"
            )
        if not is_chained_schema(event.schema_version):
            raise IntegrityError(
                f"Refusing to append schema-{event.schema_version} event "
                f"{event.event_id}: layout-v2 databases accept chained events only"
            )

    def _stream_tail(self, session_id: str) -> tuple[str, str | None] | None:
        """Return (schema_version, content_digest) of the last stored event."""
        row = self._conn.execute(
            "SELECT schema_version, content_digest FROM events WHERE session_id = ? "
            "ORDER BY session_sequence_number DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return row["schema_version"], row["content_digest"]

    def _link_to_stream(self, event: Event, tail: tuple[str, str | None] | None) -> Event:
        """Chain `event` onto the stream tail, or verify a digest it already carries."""
        if tail is not None and tail[0] != event.schema_version:
            raise IntegrityError(
                f"Refusing to append a schema-{event.schema_version} event to a "
                f"schema-{tail[0]} stream ({event.session_id})"
            )
        previous_digest = tail[1] if tail is not None else None
        if event.content_digest is not None:
            verify_link(event, previous_digest)
            return event
        return chain_event(event, previous_digest)

    def append(self, event: Event, expected_version: int | None = None) -> Event:
        self._validate_event_for_append(event)

        with self._lock:
            try:
                self._begin_immediate()
                stored = self._append_in_transaction(event, expected_version)
                self._conn.execute("COMMIT")
                return stored
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
    ) -> Event:
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

        stored = self._link_to_stream(event, self._stream_tail(session_id))
        row = to_row(stored)
        columns = ",".join(row.keys())
        placeholders = ",".join("?" * len(row))
        self._conn.execute(
            f"INSERT INTO events ({columns}) VALUES ({placeholders})",
            tuple(row.values()),
        )
        return stored

    def append_batch(  # noqa: C901
        self, events: list[Event], expected_version: int | None = None
    ) -> list[Event]:
        if not events:
            return []

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

                tail = self._stream_tail(session_id)
                stored: list[Event] = []
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
                    linked = self._link_to_stream(event, tail)
                    tail = (linked.schema_version, linked.content_digest)
                    stored.append(linked)
                    row = to_row(linked)
                    columns = ",".join(row.keys())
                    placeholders = ",".join("?" * len(row))
                    self._conn.execute(
                        f"INSERT INTO events ({columns}) VALUES ({placeholders})",
                        tuple(row.values()),
                    )

                self._conn.execute("COMMIT")
                return stored
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

        events = self._read_unverified_rows(query, params)
        if from_seq is None and to_seq is None:
            verify_stream(events)
        else:
            self._verify_slice(session_id, events)
        return events

    def read_unverified(
        self,
        session_id: SessionID,
        *,
        reason: str,
    ) -> list[Event]:
        """Read a stream without verifying its chain. Recovery path only.

        Never call this from the application path: it exists so a damaged store
        can be inspected. `reason` is required so the call site has to say why.
        """
        if not reason.strip():
            raise ValidationError("read_unverified requires a non-empty reason")
        return self._read_unverified_rows(
            "SELECT * FROM events WHERE session_id = ? ORDER BY session_sequence_number",
            [str(session_id)],
        )

    def integrity_status(self, session_id: SessionID) -> str:
        """Return `verified` or `unavailable`, or raise `IntegrityError`.

        `unavailable` covers historical schema-1.1 streams and unknown sessions.
        A `verified` result says nothing about whether the tail of the stream is
        complete (ADR-0001 sec. 2.10).
        """
        return verify_stream(self.read(session_id))

    def _read_unverified_rows(self, query: str, params: list[Any]) -> list[Event]:
        events: list[Event] = []
        for row in self._conn.execute(query, params).fetchall():
            event = from_row(row)
            validate_event(event, previous_events=events)
            events.append(event)
        return events

    def _verify_slice(self, session_id: SessionID, events: list[Event]) -> None:
        """Verify a partial range against the digest preceding it."""
        if not events or not is_chained_schema(events[0].schema_version):
            return
        row = self._conn.execute(
            "SELECT content_digest FROM events WHERE session_id = ? "
            "AND session_sequence_number < ? ORDER BY session_sequence_number DESC "
            "LIMIT 1",
            (str(session_id), events[0].session_sequence_number),
        ).fetchone()
        previous_digest = row["content_digest"] if row is not None else None
        for event in events:
            verify_link(event, previous_digest)
            previous_digest = event.content_digest

    def get_last_sequence(self, session_id: SessionID) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(session_sequence_number), 0) "
            "FROM events WHERE session_id = ?",
            (str(session_id),),
        ).fetchone()
        return int(row[0])

    def all_events(self) -> list[Event]:
        events: list[Event] = []
        for summary in self.list_sessions():
            events.extend(self.read(summary.session_id))
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
