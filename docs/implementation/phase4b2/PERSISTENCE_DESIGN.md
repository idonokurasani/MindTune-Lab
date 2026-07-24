# Phase 4B.2 — Persistence Design

## 1. Purpose

This document describes the SQLite-backed persistent event store added in Phase 4B.2.
It preserves the MPE v1.1 event-sourced semantics approved in Phase 4B.1 and satisfies
the acceptance criteria in `docs/specification/v1.1/PHASE_4B_2_SCOPE_PROPOSAL.md`.

## 2. Scope

- A shared `EventStore` `typing.Protocol` that both `InMemoryEventStore` and
  `SQLiteEventStore` implement.
- Canonical serialization from `Event` to SQLite rows and back, including typed
  `Identifier` reconstruction and `DataClassification` enum validation.
- Append-only, transactional event persistence with optimistic concurrency,
  sequence monotonicity, timestamp ordering, and provenance existence checks.
- Process-restart and cross-container replay verification.
- Docker `/data/mpe` directory and Compose-based persistence tests.

Out of scope: backup/restore, migration directory frameworks, network services,
CLI tooling, REST APIs, and Hebrew/provider integration.

## 3. Architecture

### 3.1 `EventStore` protocol

`mpe/event_store.py` defines:

```python
class EventStore(Protocol):
    def append(self, event: Event, expected_version: int | None = None) -> None: ...
    def read(self, session_id, from_seq=None, to_seq=None) -> list[Event]: ...
    def get_last_sequence(self, session_id) -> int: ...
    def all_events(self) -> list[Event]: ...
    def close(self) -> None: ...
```

`InMemoryEventStore` adds a no-op `close()`. `Runtime` and `Replay` now accept
`EventStore` instead of the concrete in-memory type. `Runtime.create_session` and
`Runtime.run_mock_session` optionally accept a fixed `session_id` to support
deterministic cross-process restart/replay demos; this does not change any MPE
v1.1 state-machine rule.

### 3.2 Serialization layer

`packages/mpe/src/mpe/persistence/serializer.py` provides:

- `to_row(event)` — converts an `Event` into a flat `dict` of column values.
- `from_row(row)` — reconstructs an `Event` from a `sqlite3.Row` or any mapping.

JSON columns (`provenance`, `payload`, `quality_flags`) use deterministic
serialization with a default handler for `Identifier` and `CanonicalEnum` values.
`Identifier` subclasses are reconstructed from their string values, and
`DataClassification` is validated with `required=False`.

### 3.3 SQLite store

`packages/mpe/src/mpe/persistence/store.py` implements `SQLiteEventStore`:

- Opens the database with `isolation_level=None` (autocommit) and `timeout=5.0`.
- Enables WAL, `synchronous=NORMAL`, and `busy_timeout=5000`.
- Initializes the `events` table and sets `PRAGMA user_version = 1`.
- Rejects unsupported `user_version` values on open.
- Uses `BEGIN IMMEDIATE` for writes to enforce a single writer per session.
- Maps `sqlite3.OperationalError` (busy/locked) and `IntegrityError` to
  `ConcurrencyError`; corrupt JSON is mapped to `ReplayError`.
- Validates events on append and again on read using `mpe.validation.validate_event`.

### 3.4 Schema

```sql
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
```

`PRAGMA user_version` is used for schema versioning; no `schema_migrations`
table is required for this phase.

## 4. Concurrency and transactions

- `append` and `append_batch` begin with `BEGIN IMMEDIATE` to acquire the write
  lock immediately and wait up to 5 seconds (`busy_timeout`).
- All in-transaction validation (expected version, sequence, timestamp ordering,
  provenance existence) happens before the `INSERT`.
- A single `ROLLBACK` is issued on any exception; `COMMIT` only succeeds when
  all validation and inserts complete.
- `append_batch` validates contiguous sequence numbers and monotonic timestamps
  for the whole batch before persisting any event.

## 5. Restart and replay

`packages/mpe/src/mpe/persistence/restart_demo.py` is an idempotent module:

- If the fixed demo session is not in the store, it runs the mock session and
  persists it.
- If the session is present, it replays it and asserts that the replayed
  terminal `RuntimeState` equals the expected deterministic live state.
- A deterministic `uuid.uuid4` patch ensures that provider-generated identifiers
  are stable across processes.

This module is used by the two-container Docker verification and by
`test_restart_recovery.py`.

## 6. Docker integration

- `Dockerfile` now creates `/data/mpe` and `chown`s `/data` to the `mpe` user.
- `compose/persistence.yaml` runs the persistence unit tests inside a container
  using a temporary in-container database path.
- The manual two-container restart demo uses a named Docker volume mounted at
  `/data`.

## 7. Verification

- All 42 Phase 4B.1 unit tests continue to pass.
- Shared `EventStore` contract tests run against both `InMemoryEventStore` and
  `SQLiteEventStore`.
- Persistence-specific tests cover WAL recovery, uncommitted rollback, batch
  atomicity, duplicate event/sequence, optimistic concurrency, partial replay,
  unknown schema version, corrupt payload, concurrent writers, and schema-version
  rejection on open.
- `docker build -t mpe:phase4b2 .`, `docker compose -f compose/persistence.yaml
  up --build`, and the two-container `restart_demo` verification all pass.
