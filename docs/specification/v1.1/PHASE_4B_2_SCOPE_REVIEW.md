# Phase 4B.2 — Persistence Foundation Scope Review

**Date:** 2026-07-23  
**Review target:** `docs/specification/v1.1/PHASE_4B_2_SCOPE_PROPOSAL.md`  
**Author of review:** Devin (self-critique of the proposed scope)  

## 1. Executive Summary

The proposed scope is directionally correct: it keeps Phase 4B.2 limited to durable persistence, chooses SQLite, and preserves the event-sourced runtime semantics from Phase 4B.1. However, it contains several concrete issues that must be corrected before implementation begins:

- The optimistic-concurrency check is specified as `COUNT(*)` rather than `MAX(session_sequence_number)`, which can diverge from the in-memory contract if a gap ever occurs.
- The migration mechanism (`schema_migrations` table + directory of SQL files) is disproportionate for a single-event-store schema.
- The Docker strategy does not modify the `Dockerfile` to create a writable persistence directory.
- The process-restart demo is split into two scripts and the Compose test may run both writes and reads inside the same container.
- Several important SQLite pragmas (`busy_timeout`, `isolation_level`/`BEGIN IMMEDIATE`) are not specified.
- The contract test plan duplicates existing assertions instead of reusing them.

These are all fixable. The scope should be revised, not blocked. After the corrections below, Phase 4B.2 is ready for implementation.

## 2. Review Method

The review checked the 24 topics requested by the user, plus the requested sections against the current Phase 4B.1 implementation (`packages/mpe/src/mpe/event_store.py`, `events.py`, `replay.py`, `runtime.py`, `types.py`, `errors.py`, and the existing Docker files). No implementation code was written and no Phase 4B.1 files were modified.

## 3. Findings

### 3.1 BLOCKER

None. The proposal is not fundamentally unsound; all issues can be corrected by scope revision.

### 3.2 REQUIRED

| # | Finding | Section(s) to correct |
|---|---|---|
| 3.2.1 | **Optimistic-concurrency check must use `MAX(session_sequence_number)`, not `COUNT(*)`.** The Phase 4B.1 runtime passes `expected_version=last_seq` and `next_seq=last_seq+1`. The in-memory store's `get_last_sequence()` returns the last sequence number, and `current_version = len(stream)`. Those are equal only if the stream is contiguous. Using `COUNT(*)` in SQLite silently assumes contiguity and would accept a non-contiguous stream as long as the count matches the last seq. The persistent store must compare `expected_version` against `MAX(session_sequence_number)` for the session, returning `0` when the stream is empty. | Section 10.2, Section 8.1 (`get_last_sequence` index), Milestone 4 |
| 3.2.2 | **`read(session_id, from_seq, to_seq)` SQL must match the in-memory slice semantics exactly.** The in-memory store computes `start = from_seq - 1` and `end = to_seq` (or `len(stream)`). Because sequence numbers start at 1 and the store enforces contiguous sequences, `WHERE session_sequence_number BETWEEN ? AND ?` is equivalent **only** under the contiguous-sequence invariant. The scope must state that the persistent store relies on the runtime for contiguous sequences and uses `BETWEEN from_seq AND to_seq` with `from_seq` defaulting to `1`. If the implementation ever supports gaps, the SQL must be revisited. | Section 11.2 |
| 3.2.3 | **`busy_timeout` and explicit `BEGIN IMMEDIATE` must be specified.** The proposal mentions `BEGIN IMMEDIATE` in the database-decision narrative but does not define the connection configuration. `sqlite3` defaults to deferred transactions and no busy timeout, which yields `OperationalError` (database locked) under concurrent writers. Phase 4B.2 must set `PRAGMA busy_timeout = 5000` (or fail-fast `0`) and begin every write with `BEGIN IMMEDIATE`. | Section 6.1, Section 10.6, Section 14 |
| 3.2.4 | **The `Dockerfile` must create a writable persistence directory.** Reusing the Phase 4B.1 image is fine, but the image currently has no `/data/mpe` directory and the `mpe` user cannot write to `/data`. The scope must list `Dockerfile` as a file to modify: add `RUN mkdir -p /data/mpe && chown -R mpe:mpe /data`. | Section 14.1, Section 14.2, Section 17 |
| 3.2.5 | **The process-restart Docker verification must use two separate container runs, not one container with two demo scripts.** The Compose command in Section 14.5 runs the persistence tests and then `restart_demo` inside one container. That proves connection close/reopen, not process restart. The corrected minimum is two independent `docker run ... mpe.persistence.restart_demo` invocations against the same named volume: the first persists the session, the second replays it and asserts equality. The Compose file should run only the persistence unit tests; the restart demo should be documented as separate commands. | Section 14.4, Section 14.5, Milestone 6 |
| 3.2.6 | **The `restart_demo`/`replay_demo` split should be consolidated.** Two demo scripts add files without adding clarity. The corrected design is one `mpe.persistence.restart_demo` module that is idempotent: if the target session is not present, it writes it; if it is present, it replays and verifies equality. This allows the two-container demonstration with a single module and no CLI arguments. | Section 14.4, Section 17 |
| 3.2.7 | **`from_json` / row deserialization must explicitly reconstruct typed identifiers and `DataClassification`.** `Event` constructor fields are typed (`event_id: EventID`, `data_classification: DataClassification | None`, etc.). The proposal states this but does not show the conversion path. The corrected serialization boundary must call `Identifier` constructors and `CanonicalEnum.validate(..., required=False)` for `data_classification`. Failure to do so will raise `AttributeError` on `data_classification.value` or `TypeError` for identifier fields. | Section 9.2, Milestone 2 |
| 3.2.8 | **Provenance existence must be checked on append in the persistent store.** The in-memory store checks that every `event_id` in `event.provenance` already exists in the same session. The persistent store must do the same before insert, either by querying `SELECT event_id FROM events WHERE event_id IN (...) AND session_id = ?` or by reading the stream prefix and calling `validate_event(event, previous_events=...)`. This check must occur inside the write transaction. | Section 10.1, Milestone 4 |
| 3.2.9 | **The migration mechanism should be simplified.** A `schema_migrations` table and a directory of `.sql` files is over-engineering for a single event-store table. The corrected approach is to use `PRAGMA user_version` and a single `init_schema()` function in `mpe/persistence/store.py` that applies idempotent `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` statements. Future schema changes can bump `PRAGMA user_version` and add conditional `ALTER TABLE` statements in the same function. | Section 8.3, Section 12.2, Milestone 3, Section 17 |
| 3.2.10 | **The contract-test plan duplicates existing assertions.** Adding `packages/mpe/tests/test_event_store_contract.py` that "reimplements" the assertions from `test_event_store.py` is unnecessary duplication. The corrected approach is to convert `test_event_store.py` into an `EventStoreContractTests` base class and create two concrete test classes (`InMemoryEventStoreTests` and `SQLiteEventStoreTests`) that inherit it. This keeps the original assertions authoritative and avoids drift. If Phase 4B.1 test files must not be touched, the alternative is a shared helper module imported by both files; plain reimplementation is not acceptable. | Section 15.1, Section 15.2, Section 17 |
| 3.2.11 | **Backup and restore must be explicitly excluded from Phase 4B.2.** The requested design topics include "backup and restore assumptions," but the proposal body never addresses them. The corrected scope must state that no automated backup/restore is implemented; durability is the SQLite file itself, and recovery tests rely on filesystem-level persistence. Backup/restore is deferred to a later phase. | Section 4 (Non-Goals) or new section |
| 3.2.12 | **The abrupt-termination test must be renamed and its guarantee narrowed.** "Simulate SIGKILL by closing the connection without commit" is not a SIGKILL simulation; it is a test that uncommitted transactions are rolled back. The corrected wording is: `test_uncommitted_transaction_rollback` validates that events not yet committed are not visible after `close()`. A true process-restart test must run a separate Python interpreter or a separate Docker container (see 3.2.5). | Section 11.4, Section 15.3 |
| 3.2.13 | **The `EventStore` protocol should not require `append_batch` as a core method unless both implementations truly need it.** The runtime currently appends one event at a time. `append_batch` is justified by the "atomic multi-event append" design topic, but it should be an **optional** extension method, not a protocol requirement, to keep `InMemoryEventStore` changes minimal. The corrected protocol includes `append`, `read`, `get_last_sequence`, `all_events`, and `close`. `SQLiteEventStore` may additionally expose `append_batch`, tested independently. | Section 7.1, Section 7.2, Section 10.1 |
| 3.2.14 | **The file-change list is not minimal.** Remove `packages/mpe/src/mpe/persistence/schema.py`, `packages/mpe/src/mpe/persistence/migrations.py`, `packages/mpe/src/mpe/persistence/migrations/`, `packages/mpe/src/mpe/persistence/errors.py`, and `packages/mpe/src/mpe/persistence/replay_demo.py` from the plan. Move DDL into `store.py`; use existing `mpe.errors`; consolidate demos as described in 3.2.6. Add `Dockerfile` to the list of files to modify. | Section 17 |

### 3.3 RECOMMENDED

| # | Finding | Section(s) to correct |
|---|---|---|
| 3.3.1 | **Contiguous sequence numbers are not enforced by the database.** The `UNIQUE (session_id, session_sequence_number)` constraint prevents duplicates but not gaps (e.g., seq 1 then 3). The runtime and `expected_version` checks prevent gaps in practice. The scope should explicitly state that contiguous sequences are an invariant owned by the runtime; the database only enforces uniqueness, monotonicity, and optimistic concurrency. A future phase could add a trigger or `CHECK` constraint if gaps become a real risk. | Section 8.2, Section 10.3 |
| 3.3.2 | **The `idx_events_session_seq` index is redundant.** The `UNIQUE (session_id, session_sequence_number)` constraint already creates a covering index for `WHERE session_id = ? ORDER BY session_sequence_number`. The separate index can be omitted. | Section 8.2 |
| 3.3.3 | **`all_events()` ordering should be deterministic.** The in-memory implementation iterates `_streams` in insertion order. The persistent store should order by `session_id, session_sequence_number` to give a deterministic result. Because `all_events()` is not used in the 42 Phase 4B.1 tests, this is a recommendation rather than a blocker. | Section 7.1, Section 10.5 |
| 3.3.4 | **The acceptance criterion "No unresolved corruption or consistency issue remains" is untestable.** Replace it with concrete, testable statements such as "all contract tests, restart-recovery tests, and Docker persistence verification pass." | Section 19 |
| 3.3.5 | **Clarify that `restart_demo` and `replay_demo` are not CLI tools.** They are one-off diagnostic scripts, like `mpe.demo`. Add a sentence in Section 14 to avoid confusion with the excluded "CLI for end users" non-goal. | Section 14.1, Section 4 |
| 3.3.6 | **Use `PRAGMA foreign_keys = OFF` or omit it.** No foreign keys are defined in Phase 4B.2, so enabling foreign keys has no effect and may mislead future maintainers. | Section 8.4 |

### 3.4 OPTIONAL

| # | Finding | Section(s) to correct |
|---|---|---|
| 3.4.1 | **Consider adding a `__enter__`/`__exit__` context manager to `SQLiteEventStore`.** This would make test cleanup cleaner but is not required. | Section 7.1 |
| 3.4.2 | **Consider storing the full canonical JSON of each event in an additional `event_json` column.** This would simplify round-trip verification and corruption detection at the cost of slight storage duplication. Not required for Phase 4B.2. | Section 8.1 |
| 3.4.3 | **Consider a `PRAGMA integrity_check` diagnostic helper.** A test helper that runs `PRAGMA integrity_check` on a closed database could strengthen corruption detection, but it is not part of the minimum required scope. | Section 15.3 |

## 4. Exact Sections of the Scope Proposal Requiring Correction

| Section | Why it requires correction |
|---|---|
| **6.1 Database Decision** | Must add `PRAGMA busy_timeout` and explicit `BEGIN IMMEDIATE` to the `sqlite3` rationale. |
| **7.1 `EventStore` Protocol** | Should remove `append_batch` from the core protocol and make it optional; `close` must remain. |
| **8.2 Indexes** | Remove redundant `idx_events_session_seq`; note that `UNIQUE (session_id, session_sequence_number)` already covers the query. |
| **8.3 Schema-migrations table** | Replace with `PRAGMA user_version` or remove; a separate table is disproportionate. |
| **8.4 SQLite settings** | Remove `PRAGMA foreign_keys = ON` or justify; add `PRAGMA busy_timeout`. |
| **9.2 Deserialization** | Add explicit steps for reconstructing `Identifier` subclasses and `DataClassification`. |
| **10.1 Append transaction boundaries** | Add provenance check inside the transaction; define connection lifecycle (per-operation vs. persistent). |
| **10.2 Optimistic concurrency** | Change `SELECT COUNT(*)` to `SELECT MAX(session_sequence_number)`. |
| **10.3 Sequence-number guarantees** | Clarify that DB enforces uniqueness/monotonicity, not contiguity; contiguity is a runtime invariant. |
| **10.6 Multiple store instances** | Add `busy_timeout` / lock-wait behavior and map `OperationalError` to `ConcurrencyError`. |
| **11.2 Partial replay** | Clarify `BETWEEN` semantics and the contiguous-sequence assumption. |
| **11.4 Recovery after abrupt termination** | Rename to "uncommitted transaction rollback"; true restart goes to Docker/subprocess. |
| **12.2 Migration mechanism** | Replace with `PRAGMA user_version` and in-module idempotent DDL. |
| **14.1–14.5 Docker Strategy** | Add `Dockerfile` modification; fix Compose to run only tests; document two-container restart demo. |
| **15.1–15.2 Test Strategy** | Replace duplicated contract tests with a parameterized base class or shared helper. |
| **17 Files Expected to Change** | Remove over-engineered files; add `Dockerfile`; consolidate demo scripts. |
| **19 Acceptance Criteria** | Replace untestable criterion with concrete test-pass statements. |

## 5. Minimal Corrected Implementation Boundary

### 5.1 New modules (minimal)

- `packages/mpe/src/mpe/persistence/__init__.py`
- `packages/mpe/src/mpe/persistence/store.py` — `SQLiteEventStore` plus idempotent `init_schema()` using `PRAGMA user_version`.
- `packages/mpe/src/mpe/persistence/serializer.py` — `to_row(event)` and `from_row(row)` with identifier/enum reconstruction.
- `packages/mpe/src/mpe/persistence/restart_demo.py` — one idempotent demo script (write if missing, replay/verify if present).

### 5.2 Modifications to Phase 4B.1 files (minimal)

- `packages/mpe/src/mpe/event_store.py`:
  - Add `EventStore` `typing.Protocol`.
  - Add `close()` no-op method to `InMemoryEventStore`.
  - Optionally add `append_batch()` no-op/loop method if it remains in the protocol.
- `packages/mpe/src/mpe/runtime.py`:
  - Change `store: InMemoryEventStore` parameter annotation to `store: EventStore`.
- `packages/mpe/src/mpe/replay.py`:
  - Change `store: InMemoryEventStore` parameter annotation to `store: EventStore`.

### 5.3 Modifications to tests (minimal)

- Refactor `packages/mpe/tests/test_event_store.py` into a contract base class plus concrete `InMemoryEventStoreTests` and `SQLiteEventStoreTests` (or use a shared helper if the file must not change).
- Add `packages/mpe/tests/persistence/test_sqlite_event_store.py` for SQLite-specific behavior.
- Add `packages/mpe/tests/persistence/test_restart_recovery.py` using `subprocess` for true process restart.
- Add `packages/mpe/tests/persistence/test_replay_from_disk.py` for live/replay equality through a file-backed store.

### 5.4 Docker/workflow files (minimal)

- `Dockerfile`: create `/data/mpe` and chown to `mpe`.
- `compose/persistence.yaml`: run persistence unit tests only.
- Documentation: two-container `restart_demo` commands in `PERSISTENCE_DESIGN.md`.

### 5.5 Excluded from this boundary

- `packages/mpe/src/mpe/persistence/schema.py`
- `packages/mpe/src/mpe/persistence/migrations.py`
- `packages/mpe/src/mpe/persistence/migrations/`
- `packages/mpe/src/mpe/persistence/errors.py`
- A second demo script (`replay_demo.py`).
- Backup/restore logic.
- Snapshots, compaction, read models, performance tuning.

## 6. Recommended Database Access Choice

**Python standard-library `sqlite3`** is the correct choice for Phase 4B.2. It is the smallest justified option, provides explicit SQL, requires no new dependencies, and supports all required transactional and concurrency behavior when combined with `BEGIN IMMEDIATE`, `PRAGMA busy_timeout`, and WAL mode.

**SQLAlchemy Core** would add a dependency and abstraction layer that is not justified by a single table. **SQLAlchemy ORM** is inappropriate because it introduces object-relational mapping, dynamic schema inference, and a learning/dependency cost that are disproportionate to the goal.

## 7. Recommended Migration Mechanism

Use **SQLite `PRAGMA user_version`** plus an idempotent `init_schema()` function inside `mpe/persistence/store.py`:

```text
1. On connection, read PRAGMA user_version.
2. If version is 1, run CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS and set user_version to 1.
3. Future schema changes bump user_version and add conditional ALTER TABLE blocks.
```

This avoids the `schema_migrations` table, the migration-runner module, and the `migrations/` directory while still supporting forward-only schema evolution.

## 8. Recommended SQLite Transaction and Concurrency Strategy

### 8.1 Connection and pragma setup

```text
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;  -- or 0 for immediate fail
```

### 8.2 Write path

1. Open a connection for the operation (or reuse a persistent connection).
2. Execute `BEGIN IMMEDIATE` to acquire the write lock.
3. Compute `last_seq = SELECT COALESCE(MAX(session_sequence_number), 0) FROM events WHERE session_id = ?`.
4. Validate `expected_version`, sequence monotonicity, timestamp ordering, and provenance existence.
5. Insert the event(s).
6. `COMMIT`.
7. Close the connection (or keep it open for subsequent operations and close on `store.close()`).

### 8.3 Read path

1. Open a connection.
2. Run the `SELECT` without an explicit transaction (WAL mode permits readers during writes).
3. Deserialize rows and validate event schema version.
4. Close the connection.

### 8.4 Batch append

1. `BEGIN IMMEDIATE`.
2. Compute `last_seq` once.
3. Validate the whole batch is contiguous and that all events pass payload/provenance/timestamp checks.
4. Insert all events.
5. `COMMIT`.
6. On any error, `ROLLBACK`.

### 8.5 Concurrent writers

- Multiple `SQLiteEventStore` instances in the same process or in different processes share the file lock.
- `BEGIN IMMEDIATE` serializes writers; `busy_timeout` determines wait-or-fail behavior.
- After acquiring the lock, the writer re-reads `last_seq` and raises `ConcurrencyError` if `expected_version` is stale.
- `OperationalError` from lock timeout is mapped to `ConcurrencyError`.

## 9. Minimum Required Docker Verification

The corrected Docker verification must prove three things:

1. **Persistence contract tests pass in Docker.**
   ```bash
   docker run --rm mpe:phase4b1 \
     python -m unittest discover -s packages/mpe/tests/persistence -p 'test_*.py' -v
   ```

2. **Process restart works across containers.**
   ```bash
   docker volume create mpe-event-store-data
   docker run --rm -v mpe-event-store-data:/data mpe:phase4b1 python -m mpe.persistence.restart_demo
   docker run --rm -v mpe-event-store-data:/data mpe:phase4b1 python -m mpe.persistence.restart_demo
   docker volume rm mpe-event-store-data
   ```
   The first run writes the session; the second run replays it and asserts terminal-state equality.

3. **Compose-based persistence tests pass without a database container.**
   ```bash
   docker compose -f compose/persistence.yaml up --build
   ```
   The Compose file should run only the persistence test suite; the cross-container restart demo is documented as manual commands.

## 10. Final Implementation Gate

Phase 4B.2 implementation may begin only after the scope proposal is revised to:

1. Replace `COUNT(*)` with `MAX(session_sequence_number)` for optimistic concurrency.
2. Simplify migrations to `PRAGMA user_version` and in-module DDL.
3. Add `Dockerfile` modifications for `/data/mpe`.
4. Consolidate the process-restart demo and document two-container restart verification.
5. Remove over-engineered files (`schema.py`, `migrations.py`, `migrations/`, `errors.py`, `replay_demo.py`).
6. Replace duplicated contract tests with a parameterized base class or shared helper.
7. Add explicit SQLite `busy_timeout` and `BEGIN IMMEDIATE` transaction strategy.
8. Add identifier/enum round-trip details and provenance validation inside the write transaction.
9. Explicitly exclude backup/restore from Phase 4B.2.
10. Make acceptance criteria testable.

## 11. Final Recommendation

**`REVISE_PHASE_4B_2_SCOPE`**

The proposal is fundamentally sound and aligned with the approved MPE v1.1 architecture, but it must be tightened before implementation. The required corrections are minor and mechanical; they do not indicate a need to change the database choice, the persistence contract, or the event-sourced design. After revision, the implementation boundary described above is minimal and ready for approval.
