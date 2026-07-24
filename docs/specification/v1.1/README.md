# MPE v1.1 Implementation Specification Package

This directory contains the Phase 4A implementation-ready specification for the MindTune Protocol Engine v1.1. All documents are derived from the approved architecture and object/event models.

## Documents

| Document | Purpose |
|---|---|
| `DATABASE_SCHEMA_SPEC.md` | Persistent entities, fields, types, constraints, indexes, foreign keys, immutable/derived fields. |
| `EVENT_STORE_SPEC.md` | Event envelope, append rules, ordering, replay, snapshots, versioning, serialization, archival, retention. |
| `RUNTIME_STATE_MACHINE.md` | Session, block, trial, response, adaptation, and safety state machines. |
| `PROVIDER_API_SPEC.md` | Abstract API for every provider: Renderer, ObservationProvider, ResponseInterpreter, DomainNormalizer, Evaluator, Scheduler, StateInferenceModel. |
| `ERROR_MODEL.md` | Recoverable and unrecoverable errors by category: severity, retry, fallback, generated events. |
| `PERSISTENCE_BOUNDARIES.md` | Classification of every object as persistent, derived, cached, ephemeral, or stream-only. |
| `SCHEMA_VALIDATION_RULES.md` | Validation rules for identifiers, enums, foreign keys, timestamps, protocol/provider compatibility, checksums, versions. |
| `IMPLEMENTATION_SEQUENCE.md` | Milestone roadmap for Phase 4A with dependencies and acceptance criteria. |

## Authority

- `MPE_ARCHITECTURE_V1_1.md`
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_HEBREW_PROVIDER_CONTRACT.md`
- `MPE_ADAPTATION_CONTRACT.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`
- `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`
- `MPE_RISK_REGISTER_V1_1.md`
- `MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`

## Scope

This package contains no runtime code, database code, SQL, APIs, UI, EEG implementation, adaptation implementation, DSL parser, or Hebrew engine changes. It is implementation-language agnostic.
