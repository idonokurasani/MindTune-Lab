# MPE Risk Register v1.1

## Audit basis

This register operationalizes `EXECUTIVE_SYNTHESIS.md` §Key risks and `METHODOLOGY_AND_LIMITATIONS.md` §Limitations (no external review, no empirical validation, technology/domain assumptions). Risks are derived from the rejection of `SOURCE_CLAIM_AUDIT.md` claims 5–13 and the adoption of `DOMAIN_INDEPENDENCE_MAP.md`.

## Scientific risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Over-adaptation based on weak behavioral signals | Medium | High | Conservative policies, abstention, rollback, one-dimension-at-a-time, simulation. |
| False confidence in EEG / sensor features | High | High | EEG `exploratory_only` default; no real-time control in Phase 5B; behavioral fallback. |
| Covert mental activity treated as observable | Medium | High | Explicit `Instruction` semantics; observable probe required for `Evaluation`. |
| Generic difficulty operations mask real causes | Medium | High | Typed difficulty dimensions; dimension-specific policies. |
| Provisional bounds treated as safe ranges | Medium | High | Label bounds as `simulation_default`; require evidence grade and validation. |
| Retention metrics confounded by item difficulty | Medium | Medium | Stratify outcomes by task, response mode, item class; use delayed recall. |
| Far-transfer or clinical claims made without evidence | Medium | High | Default transfer claim to `trained_task_performance`; require separate justification. |

## Technical risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Provider god object | Medium | High | Decomposed provider interfaces; runtime validates boundaries. |
| Hebrew correctness logic leaks into MPE core | Medium | High | `MPE_HEBREW_PROVIDER_CONTRACT.md`; code review; contract tests. |
| Runtime timestamps inaccurate or provider-owned | Medium | High | Runtime owns `timestamp`; providers report device times in payload. |
| Event stream not reproducible | Medium | High | Deterministic replay harness; seeded randomness; captured observations. |
| TTS latency breaks pacing | Medium | Medium | Pre-render in Phase 4B; latency logging; fallback to button cues. |
| Provider version mismatch | Medium | Medium | `ProtocolVersion` records dependency versions; refuse execution on mismatch. |
| Response normalization loses domain nuance | Medium | High | Separate `ResponseInterpreter` from `DomainNormalizer`; Hebrew-specific normalizer. |

## Data and privacy risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Raw EEG/voice stored without consent | Medium | High | Consent flags; encryption at rest; retention policies; pseudonymization. |
| Free-text self-report leakage | Low | High | Encrypt sensitive events; minimize free-text collection. |
| Cross-session profiling without consent | Medium | High | Learner profile scoped by consent; export/delete capability. |

## Safety risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Closed-eyes session in unsafe environment | Medium | High | Environment check; always-on stop command; audio pause cue. |
| Session silently extended beyond user limit | Low | High | Maximum duration safety rule; no silent extension. |
| Volume too high | Low | Medium | Volume constraints; device-level limits; warning. |
| Repeated errors cause frustration | Medium | Medium | Frustration threshold safety rule; insert recovery/offer end. |
| Microphone/EEG failure leaves learner stuck | Medium | Medium | Fallback to button; provider timeout; degraded mode. |

## Product and architectural risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Premature DSL commitment | Medium | High | Schema-first; textual DSL deferred. |
| Domain-independent core becomes Hebrew-specific | Medium | High | Strict provider boundaries; no Hebrew in core. |
| "First platform" claims marketed as fact | Low | High | Quarantine product-positioning hypotheses. |
| Phase 4 scope creep into adaptation/EEG | Medium | High | Phase 4 plan excludes adaptation and EEG; stop conditions.

## Traceability

This register maps risks from `EXECUTIVE_SYNTHESIS.md` §Key risks to likelihood, impact, and mitigation. It reflects `SOURCE_CLAIM_AUDIT.md` claims 1, 4–13 (rejected v1.0 claims) and the design constraints in `DOMAIN_INDEPENDENCE_MAP.md`. The limitations in `METHODOLOGY_AND_LIMITATIONS.md` (no external expert review, no empirical validation, limited clinical scope) are treated as residual risk sources. |
