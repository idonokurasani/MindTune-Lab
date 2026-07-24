# MindTune Lab — Next Task (Single Source of Truth)

> **Read this document first every time you start work on this repository.**

## 1. Current objective

**Phase 4C.1 is complete and approved.**

The next task is **Phase 4C.2 — Protocol Execution Generalization**. This is a **planning and design-reconciliation phase** before any additional protocol is implemented.

The purpose is to determine which parts of `ImmediateRecallRunner` are:

- protocol-specific;
- reusable protocol execution infrastructure;
- existing Runtime responsibilities;
- candidates for a minimal shared protocol runner.

This phase must avoid premature abstraction.

## 2. Allowed scope

In Phase 4C.2, you may:

- Analyze the `packages/mpe/src/mpe/protocol/` implementation produced in Phase 4C.1.
- Compare Immediate Recall execution flow against the existing `Runtime` contracts.
- Identify which trial lifecycle steps are generic and which are Immediate-Recall-specific.
- Propose a minimal shared protocol runner design, if justified.
- Define the interface between a shared runner and protocol-specific callbacks.
- Document the analysis and design in `docs/implementation/phase4c2/MPE_PHASE_4C2_PROTOCOL_EXECUTION_GENERALIZATION_PLAN.md`.

## 3. Forbidden scope

In Phase 4C.2, you must **not**:

- Implement Phase 4C.2 code.
- Create a second protocol implementation.
- Choose Delayed Recall as the second protocol.
- Introduce a scheduler component or spaced-repetition logic.
- Add a Hebrew or Piano adapter.
- Integrate an audio provider, live TTS, or `mpe_audio`.
- Add EEG, ASR, or physiological-signal dependencies.
- Build a broad protocol framework, taxonomy, or composition system.
- Introduce a textual DSL for protocol definition.
- Modify `docs/MPE_*.md`, `docs/specification/v1.1/*.md`, or canonical registries without an approved ADR.
- Modify `PROJECT_STATE.md` or `NEXT_TASK.md` except to record phase completion and next task.

## 4. Required analysis

The Phase 4C.2 plan must explicitly examine:

1. Whether a shared protocol runner is actually justified by the Phase 4C.1 implementation.
2. Which components may safely be generalized:
   - fixture/item iteration;
   - trial creation;
   - stimulus request/render flow;
   - observation collection;
   - bounded adaptation;
   - item completion;
   - event-derived summaries.
3. Which components must remain protocol-specific:
   - cognitive semantics;
   - step ordering;
   - adaptation policy;
   - completion criteria;
   - summary interpretation.
4. Whether a second protocol should be implemented as evidence before extracting a shared abstraction.
5. Candidate second protocol:
   - **Recognition** is preferred over Delayed Recall because it does not require spaced repetition, future scheduling, or new temporal infrastructure.
6. How the shared runner would interact with the existing `Runtime` without duplicating its responsibilities.

## 5. Required deliverable

`docs/implementation/phase4c2/MPE_PHASE_4C2_PROTOCOL_EXECUTION_GENERALIZATION_PLAN.md`

The plan must end with exactly one of the following recommendation tokens:

- `APPROVE_PHASE_4C2_IMPLEMENTATION`
- `APPROVE_PHASE_4C2_IMPLEMENTATION_WITH_CONDITIONS`
- `REVISE_PHASE_4C2_PLAN`
- `BLOCK_PHASE_4C2_IMPLEMENTATION`

## 6. How to proceed after this phase

1. Present the Phase 4C.2 plan to the user.
2. Obtain the selected recommendation token before writing implementation code.
3. If approved, begin implementation only with explicit user direction.

## 7. Quick reference

- Phase 4C.1 implementation report: `docs/implementation/phase4c1/MPE_PHASE_4C1_IMPLEMENTATION_REPORT.md`
- Phase 4C.1 closure record: `docs/implementation/phase4c1/MPE_PHASE_4C1_CLOSURE_RECORD.md`
- MPE source: `packages/mpe/src/mpe/`
- Immediate Recall tests: `packages/mpe/tests/test_protocol_immediate_recall.py`
- Architecture: `docs/MPE_ARCHITECTURE_V1_1.md`
- Directory map: `docs/project/REPOSITORY_STRUCTURE.md`
- Agent rules: `docs/project/AGENTS.md`
- Workflow: `docs/project/DEVELOPER_WORKFLOW.md`
- Testing: `docs/project/TESTING_STRATEGY.md`
- Project state: `docs/project/PROJECT_STATE.md`
