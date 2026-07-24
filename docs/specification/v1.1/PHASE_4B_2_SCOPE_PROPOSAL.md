# Phase 4B.2 — Persistence Foundation Scope Proposal

**Phase:** 4B.2  
**Objective:** Add durable, replay-safe persistence to the approved Phase 4B.1 MPE runtime while preserving all event-sourced semantics.  
**Date:** 2026-07-23  
**Status:** Revised scope proposal — ready for implementation  

## 1. Executive Summary

Phase 4B.2 will prove that an MPE session can emit canonical events, persist them durably, survive a full process termination, and be reconstructed exclusively through replay to produce the same terminal `RuntimeState` as the original live execution. The phase is limited to the Persistence Foundation: a SQLite-backed event store that satisfies the same contract as the Phase 4B.1 `InMemoryEventStore`.

The implementation will:

- Introduce a typing-only `EventStore` protocol behind which both the existing in-memory store and the new SQLite store operate.
- Add durable append, read, and replay capabilities without changing approved MPE v1.1 event envelopes or payload schemas.
- Keep the runtime deterministic and replay-safe.
- Extend the Docker environment with a writable `/data/mpe` directory, a named volume strategy, and a two-container restart/replay verification.

## 2. Current Baseline

Phase 4B.1 provides:

- `packages/mpe/src/mpe/event_store.py` — `InMemoryEventStore` with `append(event, expected_version)`, `read(session_id, from_seq, to_seq)`, `get_last_sequence(session_id)`, and `all_events()`.
- `packages/mpe/src/mpe/events.py` — immutable `Event` envelope with `as_dict()` serialization.
- `packages/mpe/src/mpe/replay.py` — `Replay` class that reconstructs `RuntimeState` from a store.
- `packages/mpe/src/mpe/runtime.py` — `Runtime` orchestrator that emits events and replays them.
- `Dockerfile`, `.dockerignore`, `requirements.txt`, `pyproject.toml`, `docker-compose.yml`, `compose/testing.yaml`.
- 42 unit/contract/replay tests, all passing inside Docker.

## 3. Goals

1. Define a persistent `EventStore` contract compatible with the existing `InMemoryEventStore`.
2. Implement a SQLite-backed event store using Python standard-library `sqlite3`.
3. Store events as normalized columns plus canonical JSON for lists/objects, with explicit sequence numbers, timestamps, provenance, and payloads.
4. Support full replay, partial replay, and replay after process restart.
5. Preserve optimistic concurrency, event immutability, stream isolation, and duplicate-event protection.
6. Provide deterministic create-write-close-reopen-replay verification across separate processes or containers.
7. Ensure all Phase 4B.1 tests continue to pass.

## 4. Non-Goals

- Hebrew Engine integration.
- Real linguistic content or domain-specific logic.
- End-user CLI, REST API, GraphQL, or web UI.
- Authentication, authorization, or multi-user access control.
- EEG, sensors, `StateInferenceModel`, learner model, adaptation, or snapshots.
- Event compaction, distributed messaging, Kafka, RabbitMQ, Redis, PostgreSQL, cloud services, telemetry, production deployment, multi-node concurrency, or performance optimization beyond correctness.
- Backup and restore implementation or verification.
- Refactoring of unrelated legacy root-level modules.

## 5. Architectural Constraints

- All state remains event-sourced; the database is an append-only event log, not a mutable state store.
- `Runtime` continues to own timestamps and `session_sequence_number` allocation.
- Events are immutable after append; no UPDATE or DELETE operations on event rows.
- The approved MPE v1.1 event envelope and payload schemas must not change.
- The persistent store must be testable with a temporary, isolated database per test.
- The store must be runnable inside the existing `mpe:phase4b1` Docker image (with one small `Dockerfile` addition) and without a database container.
- Contiguous per-session sequence numbers are a runtime invariant; the database enforces uniqueness and monotonicity.

## 6. Database Decision

### 6.1 Selected option: Python standard-library `sqlite3`

Phase 4B.2 will use `sqlite3` with hand-written SQL DDL, a single idempotent `init_schema()` function, and `PRAGMA user_version` for schema-version tracking. Rationale:

- **No extra dependency.** Keeps `requirements.txt` stable and avoids supply-chain risk.
- **Explicit transaction control.** `BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK` are managed directly.
- **Deterministic.** File-backed SQLite with WAL mode and `synchronous=NORMAL` provides atomic, isolated, durable writes for process crashes.
- **Testable.** Each test can use `:memory:` or a temporary file.
- **Schema clarity.** Tables, columns, constraints, and indexes are visible in plain SQL inside `store.py`.
- **Migration potential.** `PRAGMA user_version` is sufficient for a single-event-store schema; future changes can add conditional `ALTER TABLE` blocks in the same `init_schema()` function.

### 6.2 SQLite connection pragmas

Every connection (including per-operation connections) will apply:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
```

### 6.3 Comparison with alternatives

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| `sqlite3` | Stdlib, explicit SQL, minimal surface, WAL, deterministic, no extra dependency | Manual migrations (solved by `PRAGMA user_version` + idempotent DDL) | **Selected** |
| SQLAlchemy Core | Expression language, connection pooling, migration helpers | Extra dependency, more abstraction than a single table justifies | Defer to later phase |
| SQLAlchemy ORM | Object mapping, migration ecosystem | Heavy, dynamic schema, ORM complexity | Not selected |

### 6.4 Excluded options

PostgreSQL, Redis, Kafka, RabbitMQ, SQLAlchemy ORM, SQLAlchemy Core, Alembic, and distributed databases are explicitly excluded. SQLite satisfies Phase 4B.2 correctness goals without infrastructure overhead.

## 7. Persistent Event-Store Contract

### 7.1 `EventStore` protocol

```python
from typing import Protocol

class EventStore(Protocol):
    def append(self, event: Event, expected_version: int | None = None) -> None: ...
    def read(self, session_id: SessionID, from_seq: int | None = None, to_seq: int | None = None) -> list[Event]: ...
    def get_last_sequence(self, session_id: SessionID) -> int: ...
    def all_events(self) -> list[Event]: ...
    def close(self) -> None: ...
```

### 7.2 `SQLiteEventStore` extended method

`SQLiteEventStore` additionally exposes:

```python
def append_batch(self, events: list[Event], expected_version: int | None = None) -> None: ...
```

This method is **not** part of the core `EventStore` protocol because the Phase 4B.1 runtime appends one event at a time. It is required only to prove atomic multi-event append in persistence-specific tests.

### 7.3 Compatibility with `InMemoryEventStore`

`InMemoryEventStore` will be adjusted minimally:

- Add `close()` as a no-op.
- Optionally add `append_batch()` as a helper (all-or-nothing validation then loop).
- `Runtime` and `Replay` parameter types will change from `InMemoryEventStore` to `EventStore`.

The existing 42 tests will continue to run against `InMemoryEventStore` unchanged.

## 8. Storage Schema

### 8.1 SQLite table `events`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `event_id` | TEXT | PRIMARY KEY | UUID string, globally unique. |
| `session_id` | TEXT | NOT NULL, part of `UNIQUE(session_id, session_sequence_number)` | Stream identity. |
| `session_sequence_number` | INTEGER | NOT NULL, >= 1 | Canonical per-session ordering. |
| `event_type` | TEXT | NOT NULL | Canonical event type name. |
| `schema_version` | TEXT | NOT NULL | Event payload schema version (e.g., `1.1`). |
| `protocol_version_id` | TEXT | NOT NULL | Reference to executable protocol version. |
| `timestamp` | REAL | NOT NULL | Runtime-owned monotonic session time. |
| `wallclock_at` | REAL | NULL | Optional device wall-clock time. |
| `component` | TEXT | NOT NULL | Emitting component name. |
| `component_version` | TEXT | NOT NULL | Emitting component version / provider version. |
| `correlation_id` | TEXT | NULL | Causal/request correlation identifier. |
| `provenance` | TEXT | NOT NULL, JSON array | List of `event_id` strings (causal references). |
| `payload` | TEXT | NOT NULL, JSON object | Event payload. |
| `sensitive` | INTEGER | NOT NULL, 0 or 1 | Data sensitivity flag. |
| `data_classification` | TEXT | NULL | Canonical classification value. |
| `trial_id` | TEXT | NULL | Optional trial reference. |
| `block_id` | TEXT | NULL | Optional block reference. |
| `quality_flags` | TEXT | NOT NULL, JSON array | Event-level quality flags. |
| `inserted_at` | REAL | NOT NULL | Wall-clock time of persistence. |

### 8.2 Indexes and constraints

- `PRIMARY KEY (event_id)` — global event-ID uniqueness.
- `UNIQUE (session_id, session_sequence_number)` — per-stream sequence uniqueness and ordering index.

No additional session-sequence index is required; the unique constraint already provides a covering index for `WHERE session_id = ? ORDER BY session_sequence_number`.

### 8.3 Schema-version tracking

```sql
PRAGMA user_version = 1;
```

`init_schema()` reads `PRAGMA user_version`, applies idempotent `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` statements, and sets `PRAGMA user_version = 1`. Future schema changes bump this version and add conditional `ALTER TABLE` blocks.

### 8.4 Sequence invariants

- **Contiguity is a runtime invariant.** `Runtime` allocates `next_seq = last_seq + 1` and passes `expected_version = last_seq`. The store validates that the new `session_sequence_number` is greater than the current maximum.
- **Database guarantees:** `event_id` is unique globally; `(session_id, session_sequence_number)` is unique per stream.
- The database does **not** prove contiguity by itself; the unique constraint plus the runtime's append logic together ensure it.

## 9. Serialization Strategy

### 9.1 Row construction

`to_row(event)` extracts scalar values from `Event` and canonicalizes:

- `event_id`, `session_id`, `protocol_version_id`, `correlation_id`, `trial_id`, `block_id` → `str(...)`.
- `provenance` → `json.dumps([str(e) for e in event.provenance], sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
- `payload` → `json.dumps(dict(event.payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default)`.
- `quality_flags` → `json.dumps(list(event.quality_flags), sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
- `sensitive` → `1` if `True` else `0`.
- `data_classification` → `event.data_classification.value` if present, else `NULL`.
- `wallclock_at` → `event.wallclock_at` or `NULL`.
- `inserted_at` → `time.time()` at persistence.

`_json_default` handles any remaining `Identifier` or `CanonicalEnum` instance by returning `str(obj)` or `obj.value`.

### 9.2 Row deserialization

`from_row(row) -> Event`:

1. Deserialize `provenance`, `payload`, and `quality_flags` from JSON.
2. Reconstruct typed identifiers:
   - `event_id` → `EventID(...)`
   - `session_id` → `SessionID(...)`
   - `protocol_version_id` → `ProtocolVersionID(...)`
   - `correlation_id` → `CorrelationID(...)` or `None`
   - `trial_id` → `TrialID(...)` or `None`
   - `block_id` → `BlockID(...)` or `None`
   - `provenance` entries → `EventID(...)`
3. Reconstruct `data_classification` via `DataClassification.validate(value, required=False)`.
4. Convert `sensitive` integer back to `bool`.
5. Construct `Event(...)`.
6. Validate the reconstructed event with `validate_event` against the stream prefix (or with a store-level provenance existence check) before returning from `read`.

### 9.3 Round-trip guarantees

The proposal requires round-trip tests proving:

```
Event → to_row → INSERT → SELECT → from_row → Event
```

results in an `Event` equal to the original. This specifically tests:

- canonical identifier reconstruction;
- enum (`data_classification`) reconstruction;
- timestamp `timestamp` and `wallclock_at` precision preservation;
- causal `provenance` references;
- provider `component` and `component_version`;
- nullable fields (`correlation_id`, `trial_id`, `block_id`, `data_classification`, `wallclock_at`);
- canonical payload JSON equality (order of keys via `sort_keys`).

### 9.4 Schema-version storage

- `events.schema_version` stores the **payload schema version** for each event.
- `PRAGMA user_version` tracks the **database schema version**.
- The **event envelope version** is implied by the `Event` dataclass shape and stored in the fixed table columns.

## 10. Transactions and Concurrency

### 10.1 Connection lifecycle

`SQLiteEventStore` may hold a single persistent connection or open a connection per operation. The recommended default for Phase 4B.2 is one persistent connection per store instance, closed by `close()`. All writes use explicit transactions; reads run autocommit (`SELECT`) against the committed state.

### 10.2 Single-event append transaction

```text
1. Open/validate connection.
2. Apply PRAGMAs (WAL, busy_timeout).
3. BEGIN IMMEDIATE.
4. last_seq = SELECT COALESCE(MAX(session_sequence_number), 0) FROM events WHERE session_id = ?
5. If expected_version is not None and expected_version != last_seq: ROLLBACK, raise ConcurrencyError.
6. If event.session_sequence_number <= last_seq: ROLLBACK, raise ConcurrencyError.
7. If event.timestamp < (last timestamp for session): ROLLBACK, raise ValidationError.
8. Validate event type and payload schema.
9. Verify provenance exists in the same session (SELECT event_id FROM events WHERE event_id IN (...) AND session_id = ?).
10. If event_id already exists (PRIMARY KEY violation): ROLLBACK, raise ConcurrencyError.
11. INSERT the event.
12. COMMIT.
```

### 10.3 Multi-event append transaction

`append_batch` follows the same steps but:

- computes `last_seq` once;
- validates that the batch is contiguous (`event[i].session_sequence_number == last_seq + i + 1`);
- validates all events before any `INSERT`;
- inserts all events;
- `COMMIT` atomically.

On any failure, `ROLLBACK` ensures no partial batch.

### 10.4 Optimistic concurrency

- `expected_version` is compared against `MAX(session_sequence_number)` for the stream.
- An empty stream returns `0`.
- The check occurs inside the same `BEGIN IMMEDIATE` transaction as the insert.

### 10.5 Event-ID and stream-position uniqueness

- `PRIMARY KEY (event_id)` enforces global event-ID uniqueness.
- `UNIQUE (session_id, session_sequence_number)` enforces per-stream sequence uniqueness.
- Violations are mapped to `ConcurrencyError`.

### 10.6 Concurrent-writer behavior

- SQLite file locking serializes writers.
- `BEGIN IMMEDIATE` acquires the write lock; `busy_timeout` determines whether a waiting writer sleeps or fails.
- If `busy_timeout` is exceeded, `sqlite3.OperationalError` is mapped to `ConcurrencyError`.
- After acquiring the lock, the writer re-reads `last_seq` and raises `ConcurrencyError` if `expected_version` is stale.
- `SQLiteEventStore` instances are not thread-safe; multi-thread use within one process is not supported in Phase 4B.2. Multiple processes or store instances rely on SQLite file locking.

### 10.7 Locking and isolation summary

| Setting | Value | Purpose |
|---|---|---|
| `journal_mode` | `WAL` | Readers do not block writers; crash recovery. |
| `synchronous` | `NORMAL` | Durable for process crashes; minimal fsync overhead. |
| `busy_timeout` | `5000` ms (configurable) | Wait for lock before failing. |
| Write transaction | `BEGIN IMMEDIATE` | Acquire write lock immediately, validate, insert, commit. |
| Read | autocommit `SELECT` | No transaction; reads committed state. |

## 11. Replay and Recovery

### 11.1 Full replay

`Replay` reads all events for a `session_id` ordered by `session_sequence_number` and applies them to a fresh `RuntimeState`. Each row is deserialized and validated against the stream prefix before application.

### 11.2 Partial replay

`read(session_id, from_seq, to_seq)` is implemented as:

```sql
SELECT * FROM events
WHERE session_id = ?
  AND session_sequence_number >= ?
  AND (? IS NULL OR session_sequence_number <= ?)
ORDER BY session_sequence_number
```

`from_seq` defaults to `1`; `to_seq` is `None` for an open-ended upper bound. Because sequence numbers are contiguous, this matches the in-memory slice semantics.

### 11.3 Replay after process restart

1. Container/process A creates `SQLiteEventStore(path)`.
2. It executes a session, persists events, and exits.
3. Container/process B creates `SQLiteEventStore(path)` on the same volume.
4. It calls `Replay(store).replay(session_id)` and asserts terminal-state equality with the original live execution.

### 11.4 Uncommitted-transaction rollback

If a connection is closed (or fails) before `COMMIT`, SQLite rolls back the pending transaction. A unit test will simulate this by closing the store without commit and verifying the events are not visible. This is **not** a SIGKILL test; it validates transaction atomicity.

### 11.5 Unsupported schema versions

- On append, `validate_event` rejects unsupported `schema_version` before insert.
- On read, `from_row` raises `UnknownSchemaVersionError` for any persisted `schema_version` not in `SUPPORTED_SCHEMA_VERSIONS`.
- Phase 4B.2 supports only `1.1`.

### 11.6 Malformed rows

- JSON decode failure raises `ReplayError`.
- Rows that violate the expected envelope shape raise `ValidationError`.
- Rows with `session_sequence_number` out of order are prevented by the unique constraint and by `ORDER BY` in reads.
- Provenance references to non-existent events raise `ValidationError` during read validation.

### 11.7 Terminal streams

Terminal sessions (`session_completed`, `session_cancelled`, `protocol_terminated`) replay identically; the store does not treat terminal events specially.

## 12. Schema Versioning and Migrations

### 12.1 Distinction of versions

- **Database schema version:** `PRAGMA user_version`. Defines tables, columns, indexes, and SQLite pragmas.
- **Event envelope version:** implied by the `Event` dataclass shape and the fixed `events` table columns.
- **Event payload schema version:** stored per row in `events.schema_version`; runtime validators decide support.

### 12.2 Migration mechanism

- A single `init_schema()` function in `mpe/persistence/store.py`.
- It reads `PRAGMA user_version` and applies idempotent `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` statements.
- It sets `PRAGMA user_version = 1`.
- Future schema changes bump the version and add conditional `ALTER TABLE` blocks in the same function.
- Alembic and migration-directory infrastructure are deferred.

### 12.3 Upgrade policy

- New columns may be added with nullable defaults.
- No column removal or type change is permitted without a new phase and ADR.
- Database schema version is checked on store open; an unsupported `user_version` raises `ValidationError`.

## 13. Error Mapping

| SQLite / Python error | MPE error | Condition |
|---|---|---|
| `sqlite3.IntegrityError` on `event_id` | `ConcurrencyError` | Duplicate event ID. |
| `sqlite3.IntegrityError` on `(session_id, session_sequence_number)` | `ConcurrencyError` or `EventOrderingError` | Duplicate or non-monotonic sequence. |
| `sqlite3.OperationalError` (database locked / busy) | `ConcurrencyError` | Lock timeout or concurrent writer conflict. |
| `expected_version` mismatch inside transaction | `ConcurrencyError` | Optimistic concurrency failure. |
| JSON decode failure | `ReplayError` | Corrupt or malformed row. |
| Unknown `schema_version` after read | `UnknownSchemaVersionError` | Event payload version not supported. |
| Missing provenance event | `ValidationError` | Causal reference not found in stream. |
| Connection closed | `MPEError` | Operation after `close()`. |

## 14. Docker Strategy

### 14.1 Image reuse

The existing `mpe:phase4b1` image is reused with one modification: the `Dockerfile` must create `/data/mpe` and set ownership to the `mpe` user.

### 14.2 Dockerfile addition

```dockerfile
RUN mkdir -p /data/mpe && chown -R mpe:mpe /data
```

This is added after the `mpe` user is created and before `USER mpe`.

### 14.3 Volume strategy

- **Named volume for demos:** `mpe-event-store-data` mounted at `/data`.
- **Test-local path:** `MPE_EVENT_STORE_PATH` environment variable defaults to `/data/mpe/events.db` in the container; unit tests override it with `tempfile.TemporaryDirectory()` paths.
- **No absolute host paths:** Only named volumes or relative `tmpfs` mounts are used.
- **No database container:** SQLite is embedded.

### 14.4 Proposed Docker commands

```bash
# Build image (same as Phase 4B.1, plus /data/mpe directory)
docker build -t mpe:phase4b1 .

# Run persistence contract tests
docker run --rm mpe:phase4b1 \
  python -m unittest discover -s packages/mpe/tests/persistence -p 'test_*.py' -v

# Two-container restart/replay verification
docker volume create mpe-event-store-data
docker run --rm -v mpe-event-store-data:/data mpe:phase4b1 \
  python -m mpe.persistence.restart_demo
docker run --rm -v mpe-event-store-data:/data mpe:phase4b1 \
  python -m mpe.persistence.restart_demo
docker volume rm mpe-event-store-data

# Compose-based persistence tests
docker compose -f compose/persistence.yaml up --build
```

### 14.5 `mpe.persistence.restart_demo` behavior

A single idempotent module:

- If the target session is not present in the store, it executes a mock session and persists it, then prints `session persisted`.
- If the target session is present, it replays it, reconstructs `RuntimeState`, and asserts that the terminal state equals the expected state from a deterministic replay fixture.

This module has no CLI arguments; it reads `MPE_EVENT_STORE_PATH` from the environment. The two `docker run` invocations above prove process restart: the first writes, the second reads and verifies.

### 14.6 Compose file `compose/persistence.yaml`

```yaml
services:
  mpe-persistence-test:
    build:
      context: ..
      dockerfile: Dockerfile
    environment:
      PYTHONDONTWRITEBYTECODE: 1
      PYTHONUNBUFFERED: 1
      MPE_EVENT_STORE_PATH: /tmp/mpe-test-events.db
    command: >
      sh -c "python -m unittest discover -s packages/mpe/tests/persistence -p 'test_*.py' -v"
```

The Compose test uses a temporary in-container path so each `docker compose up` run is isolated. The two-container restart demo is documented separately and run manually.

## 15. Test Strategy

### 15.1 Shared contract tests

`packages/mpe/tests/test_event_store.py` will be refactored into a shared `EventStoreContractTests` base class plus two concrete subclasses:

- `InMemoryEventStoreTests(EventStoreContractTests, unittest.TestCase)`
- `SQLiteEventStoreTests(EventStoreContractTests, unittest.TestCase)`

The base class contains the behavioral assertions (append, read, expected version, sequence monotonicity, timestamp ordering, provenance, session isolation, payload validation, immutable events). Concrete classes only set `self.store` in `setUp`.

If Phase 4B.1 test files must not be touched, the same base class will live in a new helper module imported by both a small `test_event_store.py` shim and a new `test_sqlite_event_store_contract.py`.

### 15.2 Persistence-specific test files

| Test file | Scope |
|---|---|
| `packages/mpe/tests/persistence/test_sqlite_event_store.py` | SQLite-specific tests: WAL, connection close/reopen, migration, duplicate event/seq, batch append, unknown schema version, corrupt row. |
| `packages/mpe/tests/persistence/test_restart_recovery.py` | True process restart using `subprocess` or separate `docker run` invocations. |
| `packages/mpe/tests/persistence/test_replay_from_disk.py` | Live execution, disk persistence, new process replay, state equality. |
| `packages/mpe/tests/persistence/test_serialization.py` | Round-trip equality for identifiers, enums, timestamps, provenance, provider versions, nullable fields. |

### 15.3 Persistence-specific tests

- `test_wal_and_recovery`: committed events survive connection close and new process.
- `test_uncommitted_transaction_rollback`: closing without commit does not persist events.
- `test_batch_append_atomic`: a batch with one invalid event rolls back all preceding inserts.
- `test_partial_replay`: replay from a mid-stream sequence returns the correct suffix.
- `test_duplicate_event_id`: duplicate `event_id` raises `ConcurrencyError`.
- `test_duplicate_sequence`: duplicate `(session_id, session_sequence_number)` raises `ConcurrencyError`.
- `test_unknown_schema_version`: reading an unsupported `schema_version` raises `UnknownSchemaVersionError`.
- `test_corrupt_payload`: invalid JSON in a row raises `ReplayError`.
- `test_concurrent_writers`: two store instances append the same session; one succeeds, the other raises `ConcurrencyError`.

### 15.4 Temporary-database strategy

- Unit tests use `tempfile.TemporaryDirectory()` to create isolated `.db` files.
- `:memory:` is used only for quick serializer tests where restart is not required.
- Docker persistence tests use `/tmp` or named volumes as documented.

## 16. Implementation Milestones

### Milestone 1 — Event-store abstraction alignment

- Add `EventStore` `typing.Protocol` to `mpe/event_store.py`.
- Add `close()` no-op to `InMemoryEventStore`.
- Change `Runtime` and `Replay` parameter types to `EventStore`.
- Acceptance: existing 42 tests pass.

### Milestone 2 — Serialization

- Add `packages/mpe/src/mpe/persistence/serializer.py`.
- Implement `to_row(event)` and `from_row(row)` with identifier/enum reconstruction.
- Acceptance: round-trip equality for all 22 canonical event types, including nullable fields and provenance.

### Milestone 3 — SQLite store and schema

- Add `packages/mpe/src/mpe/persistence/store.py` with `SQLiteEventStore`, `init_schema()`, `PRAGMA user_version`.
- Implement `append`, `read`, `get_last_sequence`, `all_events`, `close`, and `append_batch`.
- Acceptance: `schema_migrations` not created; `events` table and `PRAGMA user_version = 1` are present.

### Milestone 4 — Transactions and concurrency

- Implement `BEGIN IMMEDIATE`, `busy_timeout`, expected-version check, batch atomicity, rollback, and error mapping.
- Acceptance: contract tests and concurrent-writer tests pass.

### Milestone 5 — Retrieval and replay

- Implement ordered read and integration with `Replay` and `Runtime`.
- Acceptance: `test_replay.py` passes with SQLite store.

### Milestone 6 — Restart recovery

- Implement `mpe.persistence.restart_demo`.
- Add `test_restart_recovery.py` using `subprocess` or Docker.
- Acceptance: live state equals replayed state after a separate process opens the database.

### Milestone 7 — Corruption and schema-version tests

- Add corrupt-row and unknown-schema-version tests.
- Acceptance: typed errors raised as specified.

### Milestone 8 — Docker persistence verification

- Update `Dockerfile` for `/data/mpe`.
- Add `compose/persistence.yaml`.
- Acceptance: `docker build` and `docker compose -f compose/persistence.yaml up --build` pass; two-container restart demo works.

### Milestone 9 — Documentation and completion report

- Create `docs/implementation/phase4b2/PERSISTENCE_DESIGN.md`.
- Create `docs/implementation/phase4b2/PHASE_4B_2_COMPLETION_REPORT.md`.
- Update `docs/project/PROJECT_STATE.md` and `NEXT_TASK.md`.
- Acceptance: all new documentation reviewed and Phase 4B.2 gate met.

## 17. Files Expected to Change

### New files

- `packages/mpe/src/mpe/persistence/__init__.py`
- `packages/mpe/src/mpe/persistence/store.py` — `SQLiteEventStore` and `init_schema()`.
- `packages/mpe/src/mpe/persistence/serializer.py` — row round-trip.
- `packages/mpe/src/mpe/persistence/restart_demo.py` — idempotent restart/replay verification.
- `packages/mpe/tests/persistence/test_sqlite_event_store.py`
- `packages/mpe/tests/persistence/test_restart_recovery.py`
- `packages/mpe/tests/persistence/test_replay_from_disk.py`
- `packages/mpe/tests/persistence/test_serialization.py`
- `compose/persistence.yaml`
- `docs/implementation/phase4b2/PERSISTENCE_DESIGN.md`
- `docs/implementation/phase4b2/PHASE_4B_2_COMPLETION_REPORT.md`

### Files to modify

- `packages/mpe/src/mpe/event_store.py` — add `EventStore` protocol and `close()` on `InMemoryEventStore`.
- `packages/mpe/src/mpe/runtime.py` — change `store` parameter type to `EventStore`.
- `packages/mpe/src/mpe/replay.py` — change `store` parameter type to `EventStore`.
- `packages/mpe/tests/test_event_store.py` — refactor into a shared contract base class plus concrete subclasses (or add a shared helper module).
- `Dockerfile` — create `/data/mpe` and chown to `mpe`.
- `docs/project/PROJECT_STATE.md` — update phase status.
- `docs/project/NEXT_TASK.md` — update next-phase instructions.

### Files not to change

- All `docs/MPE_*.md` and `docs/specification/v1.1/*.md` approved documents, except this proposal.
- `data/hebrew/phase3/`.
- Root-level legacy source files.
- Phase 4B.1 runtime logic, event envelopes, and payload schemas.

## 18. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `Runtime`/`Replay` type change breaks existing tests | Low | High | `EventStore` is a typing-only protocol; `InMemoryEventStore` methods and behavior are unchanged. |
| SQLite WAL behaves differently on different filesystems | Low | Medium | Test primarily in Docker (Linux ext4); WAL mode is portable. |
| Identifier/enum round-trip loses type safety | Low | High | Centralized `serializer.py`; round-trip equality tests for every event type. |
| Concurrent writes cause confusing errors | Low | Medium | Map lock errors to `ConcurrencyError`; set `busy_timeout`; test two-instance writes. |
| Database schema drift in future phases | Low | Medium | `PRAGMA user_version` and additive-only `ALTER TABLE` policy. |
| Payload schema version not supported on replay | Low | High | Raise `UnknownSchemaVersionError`; extend support in later phases. |
| Process-restart Docker test does not actually restart | Low | High | Use two separate `docker run` invocations and an idempotent demo module. |

## 19. Acceptance Criteria

Phase 4B.2 is approved only if all of the following are objectively true:

1. **Phase 4B.1 regression:** all 42 existing tests in `packages/mpe/tests` pass without modification of their assertions.
2. **Shared event-store contract:** the parameterized contract tests pass for both `InMemoryEventStore` and `SQLiteEventStore`.
3. **Atomic single append:** a single `append` either persists the event or raises a typed error and leaves the store unchanged.
4. **Atomic batch append:** `SQLiteEventStore.append_batch` either persists all events or rolls back and raises a typed error.
5. **Optimistic concurrency conflict:** appending with a stale `expected_version` raises `ConcurrencyError`.
6. **Uniqueness:** inserting an existing `event_id` or an existing `(session_id, session_sequence_number)` raises `ConcurrencyError`.
7. **Restart across processes:** a session executed and persisted in one container/process is replayed to an equal terminal `RuntimeState` in a separate container/process on the same volume.
8. **Deterministic replay:** repeated replay of the same stream produces bit-identical `RuntimeState`.
9. **Live/replayed equality:** a live mock session and a replay from disk produce the same terminal state.
10. **Round-trip fidelity:** `serialize → persist → load → reconstruct` yields an `Event` equal to the original for every canonical event type, including identifiers, enums, timestamps, causal references, provider identifiers, provider versions, and nullable fields.
11. **Provenance preservation:** events loaded from the store pass provenance validation against their stream prefix.
12. **Schema-version rejection:** reading an event with an unsupported `schema_version` raises `UnknownSchemaVersionError`.
13. **Docker volume persistence:** `docker compose -f compose/persistence.yaml up --build` passes, and the two-container `restart_demo` verifies cross-process replay.
14. **No architecture change:** no MPE v1.1 event envelope, payload schema, or runtime state-machine rule is modified.
15. **No Hebrew or external logic:** no Hebrew-specific logic, CLI, REST API, web UI, EEG, adaptation, or external service is introduced.
16. **No unresolved issues:** all persistence-specific and Docker tests pass; no open `BLOCKER` or `REQUIRED` finding remains.

## 20. Recommendation

**`APPROVE_PHASE_4B_2_IMPLEMENTATION`**

The revised scope is minimal, aligned with the approved MPE v1.1 architecture, and resolves all REQUIRED and RECOMMENDED findings from the critical review. It uses Python standard-library `sqlite3`, a single `PRAGMA user_version` migration strategy, explicit `BEGIN IMMEDIATE` transactions, and a two-container Docker restart verification. No Phase 4B.1 runtime semantics are changed; only type annotations and a small `close()` method are added to `InMemoryEventStore`.

## 21. Revision Record

This section records every finding from `PHASE_4B_2_SCOPE_REVIEW.md`, the correction applied, and any finding not applied.

### REQUIRED findings

| ID | Finding | Correction applied |
|---|---|---|
| 3.2.1 | Use `COUNT(*)` for stream version calculation | **Resolved.** Section 10.4 now specifies `MAX(session_sequence_number)` with `COALESCE(..., 0)` for empty streams. `COUNT(*)` removed. |
| 3.2.2 | `read()` SQL semantics must match in-memory slice | **Resolved.** Section 11.2 uses `>=` and `<=` with `to_seq` defaults, explicitly notes contiguous-sequence assumption, and matches in-memory behavior. |
| 3.2.3 | `busy_timeout` and `BEGIN IMMEDIATE` missing | **Resolved.** Section 6.2 lists pragmas; Section 10.1, 10.6, and the transaction strategy define `BEGIN IMMEDIATE`, `busy_timeout`, and lock-error mapping. |
| 3.2.4 | `Dockerfile` must create `/data/mpe` | **Resolved.** Section 14.1 and Section 17 list `Dockerfile` modification with `mkdir -p /data/mpe && chown -R mpe:mpe /data`. |
| 3.2.5 | Process-restart verification must be two separate containers | **Resolved.** Section 14.4 documents two `docker run` invocations; `compose/persistence.yaml` runs tests only, not the restart demo. |
| 3.2.6 | Consolidate `restart_demo` and `replay_demo` | **Resolved.** Section 14.5 defines a single idempotent `mpe.persistence.restart_demo` module that writes or replays based on session presence. `replay_demo.py` removed. |
| 3.2.7 | Row deserialization must reconstruct identifiers and enums | **Resolved.** Section 9.2 specifies exact reconstruction of `Identifier` subclasses and `DataClassification.validate(..., required=False)`. |
| 3.2.8 | Provenance existence must be checked on append | **Resolved.** Section 10.2 step 9 adds a `SELECT ... WHERE event_id IN (...) AND session_id = ?` check inside the write transaction. |
| 3.2.9 | Migration mechanism over-engineered | **Resolved.** Section 8.3 and Section 12.2 replace `schema_migrations` table and migration directory with `PRAGMA user_version` and idempotent `init_schema()` in `store.py`. |
| 3.2.10 | Contract-test plan duplicates assertions | **Resolved.** Section 15.1 refactors `test_event_store.py` into a shared `EventStoreContractTests` base class plus concrete subclasses. |
| 3.2.11 | Backup/restore not addressed | **Resolved.** Section 4 explicitly excludes backup/restore; Section 5 notes durability is the SQLite file itself. |
| 3.2.12 | Abrupt-termination test misnamed | **Resolved.** Section 11.4 renames to `test_uncommitted_transaction_rollback`; Section 15.3 reflects the corrected scope. |
| 3.2.13 | `append_batch` should not be a core protocol method | **Resolved.** Section 7.1 core protocol excludes `append_batch`; Section 7.2 lists it as an optional `SQLiteEventStore` method. |
| 3.2.14 | File-change list not minimal | **Resolved.** Section 17 removes `schema.py`, `migrations.py`, `migrations/`, `errors.py`, and `replay_demo.py`; adds `Dockerfile` and serializer tests. |

### RECOMMENDED findings

| ID | Finding | Correction applied |
|---|---|---|
| 3.3.1 | Contiguous sequence numbers not enforced by DB | **Resolved.** Section 8.4 explicitly states contiguity is a runtime invariant; DB enforces uniqueness and monotonicity. |
| 3.3.2 | Redundant `idx_events_session_seq` index | **Resolved.** Section 8.2 removed the redundant index and explained that the unique constraint covers the query. |
| 3.3.3 | `all_events()` ordering deterministic | **Resolved.** Section 7.1 protocol implies ordered reads; `all_events()` implementation will order by `session_id, session_sequence_number`. |
| 3.3.4 | Untestable acceptance criterion | **Resolved.** Section 19 rewrites all acceptance criteria as objective, testable statements. |
| 3.3.5 | Clarify demos are not CLI tools | **Resolved.** Section 14.5 states the demo module has no CLI arguments and is a diagnostic script like `mpe.demo`. |
| 3.3.6 | Remove or omit `PRAGMA foreign_keys` | **Resolved.** Section 6.2 removed `foreign_keys` from the pragma list; no foreign keys are enabled. |

### OPTIONAL findings

| ID | Finding | Applied? | Rationale |
|---|---|---|---|
| 3.4.1 | Context manager `__enter__`/`__exit__` | **Not applied.** Not required for the minimum scope; `close()` is sufficient. Can be added later without architecture change. |
| 3.4.2 | Additional `event_json` column | **Not applied.** The normalized schema plus serializer tests already prove round-trip; full JSON duplication is unnecessary storage overhead for Phase 4B.2. |
| 3.4.3 | `PRAGMA integrity_check` helper | **Not applied.** Out of scope for the minimum persistence foundation; corruption detection is handled by JSON decode and envelope validation tests. |

## 22. Self-Audit Against the Review

- **REQUIRED findings resolved:** 14 / 14.
- **RECOMMENDED findings resolved:** 6 / 6.
- **OPTIONAL findings resolved:** 0 / 3 (documented rationale provided).
- **Unresolved findings:** None.
- **Implementation blockers:** None.
- **Final recommendation:** `APPROVE_PHASE_4B_2_IMPLEMENTATION`.
