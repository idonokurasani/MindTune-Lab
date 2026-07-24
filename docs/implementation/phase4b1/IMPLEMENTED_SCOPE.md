# Phase 4B.1 — Implemented Scope

**Date:** 2026-07-23

## What was implemented

- Canonical `Identifier` types (`SessionID`, `TrialID`, `EventID`, etc.).
- Canonical string enums (`SessionStatus`, `ResponseMode`, `AnswerStatus`, `DecisionStatus`, etc.) with `.validate()` and `.values()` helpers.
- Immutable `Event` envelope with deterministic payload schemas and `as_dict()` serialization.
- `InMemoryEventStore` with:
  - Per-session streams
  - Strictly monotonic `session_sequence_number`
  - Optimistic concurrency (`expected_version`)
  - Non-decreasing timestamp checks
  - Provenance existence checks
  - Immutable stored events
- `RuntimeState` aggregate with handlers for all 22 canonical event types in the mock flow.
- `Runtime` orchestrator that emits the 22-event mock session:
  1. `session_created`
  2. `session_started`
  3. `schedule_decision`
  4. `block_started`
  5. `trial_created`
  6. `instruction_started`
  7. `instruction_completed`
  8. `stimulus_requested`
  9. `stimulus_ready`
  10. `instruction_started`
  11. `instruction_completed`
  12. `response_window_opened`
  13. `observation_received`
  14. `captured_response_created`
  15. `response_interpreted`
  16. `domain_response_normalized`
  17. `evaluation_completed`
  18. `feedback_started`
  19. `feedback_completed`
  20. `schedule_decision`
  21. `block_completed`
  22. `session_completed`
- Deterministic mock providers: `MockRenderer`, `MockKeyboardObservationProvider`, `MockResponseInterpreter`, `MockDomainNormalizer`, `MockEvaluator`, `MockScheduler`.
- `Replay` class that reconstructs `RuntimeState` from the stored event stream.
- `mpe.demo` live/replay verification script.
- `pytest`/`unittest` test suite under `packages/mpe/tests/` covering identifiers, enums, event store, state machines, providers, replay, reference flow, and invariants.
- Docker development/test environment: `Dockerfile`, `.dockerignore`, `requirements.txt`, `pyproject.toml`, `docker-compose.yml`, `compose/testing.yaml`, and `packages/mpe/README.md`.

## Explicitly out of scope

- Persistence, databases, files, or durable event storage. (An unauthorized `packages/mpe/src/mpe/persistence/` SQLite backend was introduced outside this scope during implementation and was removed during closure verification; see `PHASE_4B_1_COMPLETION_REPORT.md` §7 for the audit trail.)
- Network APIs, servers, CLI beyond the demo script, UI, or mobile code.
- CI/CD, production orchestration, or multi-service Compose.
- Real Hebrew Engine integration (mock evaluator only).
- Adaptation policies, scheduler policies beyond a fixed single-item sequence.
- EEG/sensor ingestion or `StateEstimate` production.
- Multi-session, multi-block, multi-trial protocols beyond the single-trial mock flow.
