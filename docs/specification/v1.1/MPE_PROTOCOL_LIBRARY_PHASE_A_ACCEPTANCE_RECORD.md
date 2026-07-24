# MPE Protocol Library v1.0 — Phase A Acceptance Record

## 1. Documents reviewed

- `docs/specification/v1.1/MPE_PROTOCOL_LIBRARY_v1.0.md` — the document being reconciled.
- `docs/specification/v1.1/MPE_AUDIO_ASSET_PIPELINE_SPEECHGEN_HEBREW_v0.1.md` — referenced for audio asset boundary compatibility.
- `docs/specification/v1.1/MPE_AUDIO_PIPELINE_PHASE_A_DECISION_RECORD.md` — authoritative audio pipeline decisions.
- `docs/MPE_OBJECT_MODEL_V1_1.md` — canonical object model (`Program`, `ProgramVersion`, `Protocol`, `ProtocolVersion`, `Block`, `Trial`, `TaskDefinition`, `Instruction`, `StimulusRequest`, `RenderedStimulus`, `ResponseWindow`, `Observation`, `CapturedResponse`, `ResponseInterpretation`, `DomainNormalizedResponse`, `Evaluation`, `FeedbackEvent`, `SafetyInstruction`, `AdaptationDecision`, `ScheduleDecision`, `EvidenceRecord`, `Outcome`).
- `docs/MPE_EVENT_MODEL_V1_1.md` — canonical event taxonomy, payload shapes, replay semantics, sensitive-data handling.
- `docs/MPE_PROVIDER_BOUNDARIES.md` — provider interface responsibilities and prohibitions.
- `docs/MPE_ADAPTATION_CONTRACT.md` — permitted/prohibited adaptation dimensions, `AdaptationDecision` schema, EEG policy.
- `docs/MPE_DSL_DECISION_RECORD.md` — decision to use typed model (JSON/YAML fixtures) in Phase 4, textual DSL deferred.
- `docs/research/mpe_ontology_audit_v1/PROTOCOL_PRIMITIVES_CATALOG.md` — allowed/prohibited primitives and trial role sequences.
- `docs/research/mpe_ontology_audit_v1/COGNITIVE_PROTOCOL_ONTOLOGY.md` — conceptual ontology for `Program`, `Protocol`, `ProtocolVersion`, `TaskDefinition`, `Trial`, `Instruction`, `Stimulus`, `Evaluation`, `Feedback`, `Safety`, `ScheduleDecision`, `AdaptationDecision`, `Outcome`.
- `docs/research/mpe_ontology_audit_v1/DOMAIN_INDEPENDENCE_MAP.md` — what belongs in MPE core vs domain providers.
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md` — Hebrew `DomainProvider`, `Renderer`, and `Evaluator` outputs.
- `docs/MPE_OPEN_DECISIONS.md` — existing open decisions relevant to protocol semantics (microphone fallback, voice response path, delayed recall architecture, correctness credit, canonical TTS, streaming vs pre-rendered, StateEstimate inputs).
- `docs/MPE_CANONICAL_ENUM_REGISTRY.md` and `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md` — canonical enum/identifier contracts.
- `docs/MPE_RISK_REGISTER_V1_1.md` — risks to be carried forward.
- `packages/mpe/src/mpe/` runtime implementation (events, types, provider protocol, replay, aggregates) — baseline compatibility check.

## 2. Conceptual-entity-to-repository-contract mapping

| Protocol Library concept | MPE v1.1 repository contract | Mapping status | Notes |
|---|---|---|---|
| `Program` (logical identity) | `Program` | Aligned | Stable logical identity; not executable. |
| `ProgramVersion` | `ProgramVersion` | Aligned | Immutable executable definition; dependency versions and checksum. |
| `Protocol` | `Protocol` | Aligned | Stable logical identity; not executable. |
| `ProtocolVersion` | `ProtocolVersion` | Aligned | Immutable; contains `block_sequence` or `trial_sequence`, `required_providers`, `safety_profile_id`, `dependency_versions`. |
| `ProtocolObjective` | `ProtocolVersion.objective` / `purpose` / `primary_transfer_claim` | Partial | Objectives map to `protocol_purpose` and `transfer_claim_level`; the cognitive-goal vocabulary (§3.3) is a library-level taxonomy on top of MPE enums. |
| `ProtocolStep` | `Instruction` + `StimulusRequest` + `ResponseWindow` + `FeedbackEvent` + `ScheduleDecision` | Reconcile | A `ProtocolStep` is a *semantic* primitive; its concrete expression is one or more MPE typed-model entities. `branch_spec` may require `ScheduleDecision` or an extension to `Block`/`ProtocolVersion` graph (unresolved). |
| `ProtocolStep.duration_policy` | `Instruction.allotted_duration` / `ResponseWindow.deadline_at` / `WAIT_DURATION` | Partial | `Pause`/`Wait` durations are runtime parameters subject to `AdaptationDecision` bounds. The typed model already supports `allotted_duration` and `deadline_at`; a dedicated `duration_policy` field is a library-level convenience. |
| `ProtocolStep.stimulus_ref` | `StimulusRequest` (`content_item_id`, `renderer_id`, `voice_id`, `rate`, `prosody_hints`) | Aligned | (`item_id`, `asset_role`, `voice_profile_family`) are encoded in `content_item_id` + `prosody_hints` (or `voice_id`). Asset resolution is `Renderer`/`mpe_audio` responsibility. |
| `ProtocolStep.expected_response` | `Instruction.observable_response_expected` + `ResponseWindow` + `response_requirement` | Aligned | Internal vs overt maps to `INSTRUCT_COVERT_RETRIEVAL` vs `REQUEST_OVERT_RESPONSE`. |
| `ProtocolStep.branch_spec` | `ScheduleDecision` + `Block.exit_condition` | Gap | MPE `ProtocolVersion` does not yet define an explicit per-step branching graph. Branching can be expressed through `ScheduleDecision`s and `Block`/`exit_condition`s; a richer protocol graph is a future schema extension, not a Phase 4 blocker. |
| `Observation` (Protocol Library) | `Observation` / `CapturedResponse` / `ResponseInterpretation` / `DomainNormalizedResponse` / `Evaluation` | Partial | The library uses "Observation" loosely for any evidence. In MPE, raw observations (`Observation`) are distinct from interpreted/normalized responses and `Evaluation`. The library should reference the layered response pipeline explicitly. |
| `AdaptationDecision` | `AdaptationDecision` | Reconcile | Library model is simplified; must include all MPE required fields (`deployment_status`, `allowed_bounds`, `source_event_ids`, `evidence_record_ids`, `aggregation_window`, `minimum_evidence`, `uncertainty_threshold`, `confidence`, `cooldown`, `hysteresis`, `maximum_step_size`, `rollback_rule`, `abstention_rule`, `decision`). |
| `ExecutionPlan` | `Session` start parameters + `ScheduleDecision` | Reconcile | Not a formal MPE object. Equivalent data lives in `session_started.start_parameters`, `ProtocolVersion`, and `ScheduleDecision`. The library may treat it as a runtime-derived artifact. |
| `ExecutionResult` | `Outcome` + event stream | Partial | Maps to `Outcome` (computed from events) and `session_completed`. The library's richer `steps_executed` list is a derived view. |
| `ProtocolSummary` | `Outcome` / derived analytics | Partial | Not a formal MPE object; produced in Analysis from `Outcome` and events. |
| `DomainAdapter` | `DomainProvider` + `ResponseInterpreter` + `DomainNormalizer` + `Evaluator` + `Scheduler`/`ItemPolicy` | Aligned | The library's abstract `DomainAdapter` is realized by the MPE provider boundary set. |
| `AssetRole` | `mpe_audio` asset roles + `FeedbackEvent.content_item_id` / `Instruction.instruction_payload` | Aligned | Roles are shared vocabulary with `mpe_audio`: `natural`, `pedagogical_slow`, `prompt`, `confirmation`, `instruction`, `minimal_pair`, `sentence_context`. The `instruction` asset role supplies media for `Instruction` payloads. |
| `EvidenceKind` | `observation_type`, `interpretation_type`, `answer_status`, `evaluation_status` | Aligned | Behavioral evidence kinds map to MPE event payload fields. |
| `ProtocolSummary.metrics` | `Outcome` + `ProtocolSummary` (derived) | Aligned | Metrics are descriptive, computed offline. |

## 3. Primitive-to-contract mapping table

| Protocol Library primitive | MPE typed-model / event contract | Produces observation / event | Adaptation contract mapping |
|---|---|---|---|
| **Play stimulus** | `Instruction(instruction_type=PRESENT_STIMULUS)` → `StimulusRequest` → `RenderedStimulus` → `stimulus_started`/`stimulus_completed` | `stimulus_*` events; onset/offset; `RenderedStimulus.duration` | `rate` via `AdaptationDecision.target_dimension=speech_rate` (bounded); variant/role via `ScheduleDecision` or `StimulusRequest.voice_id`/`prosody_hints` |
| **Pause** | `WAIT_DURATION` runtime instruction or inter-`Instruction` silence; duration policy is an `AdaptationDecision` | `instruction_started`/`instruction_completed` or silent timing derived from event timestamps | `AdaptationDecision.target_dimension=pause_duration` (primary lever) |
| **Expect internal response** | `Instruction(instruction_type=INSTRUCT_COVERT_RETRIEVAL)` + optional `ResponseWindow` if overt marker enabled | `instruction_started`/`instruction_completed`; `response_window_opened`/`response_completed` if overt; latency from event timestamps | `AdaptationDecision.target_dimension=response_deadline` or `pause_duration`; `ScheduleDecision` for repetition |
| **Expect overt response** | `Instruction(instruction_type=REQUEST_OVERT_RESPONSE)` + `ResponseWindow` | `response_window_opened`, `response_detected`, `response_completed`, `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed` | As above; correctness flows to `ScheduleDecision` and `AdaptationDecision` |
| **Confirm** | `PRESENT_STIMULUS` of a `confirmation` asset, optionally followed by `FeedbackEvent(feedback_category=KNOWLEDGE, feedback_type=correct_answer/elaboration)` | `stimulus_started`/`stimulus_completed` or `feedback_started`/`feedback_completed`; self-confirm captured as `Observation`/`CapturedResponse` | `AdaptationDecision` for whether/when to confirm and repetition after |
| **Repeat** | `ScheduleDecision` to re-select current/previous `Trial`/`Block`, or `Block.exit_condition` loop | `schedule_decision`, `trial_created`, `block_started` | Bounded repeat count enforced by `ScheduleDecision` policy; `AdaptationDecision` may adjust count |
| **Branch** | `ScheduleDecision` (`decision_type`, `selected_item_ids`, `excluded_candidates`) + `AdaptationDecision` for parameter branches | `schedule_decision`, `adaptation_proposed`/`applied`/`abstained` | Branch reason recorded in `schedule_decision`/`adaptation_*` `reason` and `source_event_ids` |
| **Transition** | `ScheduleDecision` (`next_block`, `insert_review`, `offer_break`, `session_end`) + `safety_rule_triggered`/`recovery_inserted` for recovery entry | `schedule_decision`, `block_started`/`block_completed`, `recovery_inserted` | Progression/recovery/consolidation entry via `ScheduleDecision` |
| **Wait** | `WAIT_DURATION` | `instruction_started`/`instruction_completed` or derived timing | Rarely adapted; `pause_duration` if adaptive |
| **Observe** | `OPEN_RESPONSE_WINDOW` + `observation_received` | `observation_received`, `signal_quality_changed` | Feeds `AdaptationDecision` and `ScheduleDecision` evidence |
| **Score** | The evaluation pipeline: `captured_response_created` → `response_interpreted` → `domain_response_normalized` → `evaluation_completed`/`abstained`/`failed` | `evaluation_*` events | `Evaluation` drives `ScheduleDecision` and history-based `AdaptationDecision` |
| **Record** | Implicit in MPE event model; every semantically meaningful moment emits an `Event` | All events | None (audit/replay) |
| **Explain** | `Program`/`Protocol`/`ProtocolVersion` metadata or onboarding content; not an in-session `Instruction` | Not an execution event (unless used in config/review) | None |

## 4. Lifecycle-to-runtime mapping table

| Protocol Library lifecycle phase | MPE runtime contract | Events / objects | Notes |
|---|---|---|---|
| **Planning** | Pre-session build of `ProgramVersion`/`ProtocolVersion` + `ScheduleDecision` + `Session` start parameters | `session_created` (`program_version_id`, `protocol_version_id`, `learner_id`) | Prefetch and validate audio assets via `Renderer`; no provider calls during execution. `ExecutionPlan` is a runtime planning artifact, not a core object. |
| **Execution** | `Session` active phase | `session_started`, `block_started`, `trial_created`, `instruction_started`/`completed`, `stimulus_*`, `feedback_*`, `safety_instruction_*` | Runs `Instruction`s, `ResponseWindow`s, `FeedbackEvent`s over approved local assets. |
| **Observation** | `ObservationProvider` + `ResponseInterpreter` + `DomainNormalizer` | `observation_received`, `response_detected`, `response_completed`, `response_timeout`, `captured_response_created` | Interleaved with Execution. |
| **Adaptation** | `AdaptationDecision` + `ScheduleDecision` | `adaptation_proposed`, `adaptation_abstained`, `adaptation_applied`, `adaptation_reversed`, `schedule_decision` | Bounded, reasoned, recorded. `Transition` to Recovery/Consolidation is a `ScheduleDecision`. |
| **Completion** | `Session` terminal state | `session_completed` / `session_cancelled` / `protocol_terminated` | `Outcome` computed from events; durable learning-state updates only from behavior/history. |
| **Replay** | `Replay` class over `EventStore` | `Replay` reconstructs `RuntimeState` from events; `protocol replay` re-runs decision logic against recorded inputs | Event replay is fidelity; protocol replay is soundness/EEG ablation. Protocol replay is a Phase 5+ capability. |
| **Analysis** | Derived metrics from `Outcome` + event stream | `Outcome` computation; `state_estimate_produced` (diagnostic) | Descriptive only; EEG never becomes authoritative retroactively. |

## 5. Adaptation compatibility assessment

The Protocol Library's four adaptation sources and bounded-parameter set are compatible with `MPE_ADAPTATION_CONTRACT.md` and the MPE `AdaptationDecision` schema, with the following reconciliations:

| Library source | MPE contract mapping | Compatibility |
|---|---|---|
| **Behavior-based** | `AdaptationDecision` + `ScheduleDecision` driven by `evaluation_completed`, `feedback_started`, learner-initiated `Observation`s | Compatible. Only behavior may establish correctness/mastery. |
| **Latency-based** | `AdaptationDecision.target_dimension` = `pause_duration`, `response_deadline`, `speech_rate` | Compatible. Latency is a pacing proxy, not correctness. |
| **History-based** | `ScheduleDecision` (`candidate_item_ids`, `selection_rule`) + `item_history_snapshot_id` | Compatible. History governs selection/scheduling. |
| **EEG-context** | `SensorObservation` → optional `state_estimate_produced` (diagnostic) → `AdaptationDecision` with `eeg_context_ref` and `deployment_status` | Compatible, provided every EEG-influenced decision carries the mandatory reasoned fields (§9.4). |

**Library bounded-parameter → MPE `target_dimension` mapping:**

| Library parameter | MPE `target_dimension` | Notes |
|---|---|---|
| Pause / window duration | `pause_duration`, `response_deadline` | Primary lever. |
| Runtime playback rate | `speech_rate` | Within validated phonetic bounds; otherwise select a pedagogical variant. |
| Repetition count | Not a single `AdaptationDecision` dimension; expressed via `ScheduleDecision` re-selection or loop counter | Can be treated as an internal `ScheduleDecision` policy. |
| Item selection | `ScheduleDecision.selected_item_ids` | History-based selection. |
| Difficulty band / progression step | `new_item_rate`, `cue_specificity` | Library's abstract difficulty band maps to typed dimensions. |
| Category/mode transitions | `ScheduleDecision.decision_type` (`next_block`, `insert_review`, `offer_break`, `session_end`) + `recovery_inserted` | Not an `AdaptationDecision` parameter change. |
| Presentation density (Listening) | `pause_duration` / `response_deadline` applied to segmentation windows | A compound policy over pause spacing. |

**Conflict resolved:** The Protocol Library treats `Branch`/`Transition` as adaptation touchpoints. In MPE, branching/transitioning is a `ScheduleDecision` (selection/progression), while parameter changes are `AdaptationDecision`s. The reconciled view separates these: protocol flow decisions are `ScheduleDecision`s; bounded parameter nudges are `AdaptationDecision`s. Both must be recorded with reasons and source events.

## 6. Replay compatibility assessment

The Protocol Library's dual replay model (event replay + protocol replay) aligns with MPE v1.1:

- **Event replay** is the primary MPE replay mechanism (`packages/mpe/src/mpe/replay.py` reconstructs `RuntimeState` from the event store). The library's requirement that stimuli (exact asset id + version), pauses, confirmations, observations, and adaptation decisions are reconstructible is satisfied if:
  - every `StimulusRequest`/`RenderedStimulus` records the concrete `audio_asset_version_id` (per `MPE_AUDIO_PIPELINE_PHASE_A_DECISION_RECORD.md`);
  - every `AdaptationDecision` and `ScheduleDecision` is emitted as an event;
  - every `Observation`/`CapturedResponse`/`ResponseInterpretation`/`DomainNormalizedResponse`/`Evaluation` is captured.

- **Protocol replay** (re-running protocol decision logic against recorded inputs) is not yet implemented in `packages/mpe`. It is architecturally compatible because:
  - `ProtocolVersion` and `ProgramVersion` are immutable;
  - `Session` start parameters include `random_seed`;
  - `ScheduleDecision` and `AdaptationDecision` events contain `source_event_ids`, `policy_id`, `policy_version`, and random seeds, enabling deterministic re-computation.
  - EEG ablation is supported in design because all EEG-influenced decisions carry `eeg_context_ref`; dropping those events during replay leaves a coherent behavioral-only session.

**Gap:** Protocol replay requires a future `ProtocolReplay` harness that re-runs `Scheduler`/`ItemPolicy` and adaptation policies against the captured observation stream. This is a Phase 5+ implementation item, not a Phase A blocker.

## 7. Audio-boundary assessment

The Protocol Library's audio assumptions are compatible with the reconciled `MPE_AUDIO_ASSET_PIPELINE_SPEECHGEN_HEBREW_v0.1.md` and `MPE_AUDIO_PIPELINE_PHASE_A_DECISION_RECORD.md`:

- Protocols address audio only as (`item_id`, `asset_role`, `voice_profile_family`). This maps directly to `StimulusRequest.content_item_id` + `voice_id`/`prosody_hints` (where `voice_id` is the logical `voice_profile_id` and `prosody_hints` carries `asset_role`/`logical_audio_asset_id`).
- No protocol definition contains provider URLs, voice names, or synthesis parameters.
- `Play` uses approved local assets; prefetch happens at Planning; no synchronous provider calls during Execution.
- `runtime_playback_rate` is bounded; outside bounds the protocol requests a pre-synthesized pedagogical variant (`pedagogical_slow`) rather than time-stretching.
- Asset roles (`natural`, `pedagogical_slow`, `prompt`, `confirmation`, `instruction`, `minimal_pair`, `sentence_context`) are a shared vocabulary with `mpe_audio`.
- The `instruction` asset role is compatible with MPE `Instruction.instruction_payload`: an `Instruction` whose payload is media uses a `StimulusRequest` with `asset_role=instruction`.

**Minor reconciliation:** The Protocol Library's appendix examples use DSL-style `play(...)`, `pause(...)`, etc. These are illustrative pseudocode only; the actual runtime contract is the typed MPE model (`Instruction`, `StimulusRequest`, `ResponseWindow`, `FeedbackEvent`). This has been clarified in the reconciled Protocol Library document.

## 8. EEG-policy assessment

The Protocol Library's EEG policy (§9) is a direct restatement of `MPE_ADAPTATION_CONTRACT.md` and `MPE_PROVIDER_BOUNDARIES.md`:

- EEG is contextual, never authoritative, never determines correctness, never rewrites learning state directly.
- EEG MAY influence bounded pause/window duration, repetition probability, temporary difficulty hold, transition to Consolidation/Recovery, presentation density, and exit readiness (with behavioral corroboration).
- EEG MUST NOT mark responses correct/incorrect, invent performance, override behavioral evidence, rewrite curriculum/mastery/scheduling, or make irreversible learning-state changes.
- Every EEG-influenced adaptation emits a reasoned `AdaptationDecision` with `eeg_context_ref`, `policy_rule_id`, bounded adjustment, previous/new values.
- EEG ablation (replay without EEG-sourced decisions) must leave a coherent session.

**Status:** Fully compatible. The only requirement is that any protocol implementing EEG-influenced adaptation in Phase 5C uses the full `AdaptationDecision` schema from `MPE_ADAPTATION_CONTRACT.md`, including `deployment_status` (`exploratory_only` default until validated).

## 9. Normative-status classification

| Protocol Library concept or section | Normative status | Rationale |
|---|---|---|
| Eight-category taxonomy (Encoding, Recall, Transformation, Recognition, Internal Speech, Listening, Consolidation, Recovery) | **Normative** | Defines the protocol space; closed vocabulary. |
| Closed cognitive-goal vocabulary (Encode, Retrieve, Discriminate, Transform, Produce, Comprehend, Consolidate, Restore) | **Normative** | Used to classify protocols and objectives. |
| Closed primitive catalog (Play, Pause, Expect, Confirm, Repeat, Branch, Transition, Wait, Observe, Score, Record, Explain) | **Normative** | Semantic primitives; extension is architecture-level. |
| Neutral relation vocabulary (`associate`, `derive`, `inflect`, `contrast`, `family`, `sequence`, `contains`) | **Normative** | Domain-agnostic relation language. |
| Asset role vocabulary | **Normative** | Shared with `mpe_audio`; extension requires ADR. |
| Four-source adaptation model and bounded-parameter set | **Normative** | Architectural boundary; compatible with `MPE_ADAPTATION_CONTRACT.md`. |
| EEG policy (§9) | **Normative / permanent rule** | May not be weakened. |
| Per-protocol specifications (§7) | **Recommended / reference** | They describe canonical protocols; new protocols may be added using the same template. |
| Concrete primitive names as DSL keywords | **Rejected / illustrative** | No textual DSL is approved. Pseudocode in appendices is not runtime syntax. |
| `ProtocolStep.branch_spec` graph semantics | **Experimental / pending ADR** | MPE typed model currently uses `block_sequence`/`trial_sequence` + `ScheduleDecision`. A richer protocol graph is a future extension. |
| `ExecutionPlan`, `ExecutionResult`, `ProtocolSummary` object model | **Recommended / derived** | Not formal MPE objects. Equivalent data exists in `Session` start parameters, `Outcome`, and derived analytics. |
| Self-confirmation capture mechanism | **Unresolved / blocker for internal-speech protocols** | Needs ADR to choose button/self-report/breath/minimal voice marker. |
| Overt-response capture scope (ASR vs timing-only) | **Unresolved / non-blocker for v1.0** | `MPE_OPEN_DECISIONS.md` #3 covers this. |
| Difficulty model ownership | **Unresolved / non-blocker** | `MPE_OPEN_DECISIONS.md` does not explicitly resolve; needs ADR. |
| Spacing/history engine boundary | **Unresolved / non-blocker for Phase 4** | Affects Consolidation protocols; scheduler design can resolve. |
| EEG context representation | **Unresolved / non-blocker** | Co-design with Phase 5B sensor layer. |
| Stochastic policy determinism | **Recommended / implement in schema** | Record random seeds/draws in `ScheduleDecision`/`AdaptationDecision` payloads. |
| Protocol composition (single vs multiple protocols per session) | **Unresolved / non-blocker** | `ProgramVersion.protocol_version_sequence` already supports multiple `ProtocolVersion`s. |
| Minimal-pair / error asset generation authority | **Unresolved / non-blocker** | Affects Recognition protocols; pipeline/adapter responsibility. |

## 10. Unresolved decisions and their blocker status

| # | Unresolved decision | Blocker for Phase 4? | Notes / path to resolution |
|---|---|---|---|
| 1 | Self-confirmation capture mechanism for eyes-closed internal-speech protocols. | **Blocker for Internal Speech/Recall execution** | Must be resolved before implementing `INSTRUCT_COVERT_RETRIEVAL` end-to-end. Options: button tap, self-report prompt, breath/marker, minimal voice onset timing. ADR required. |
| 2 | Overt-response capture scope: timing/energy only vs ASR vs button/typed. | No | `MPE_OPEN_DECISIONS.md` #3 already defers ASR validation; protocol library can support all modes through `ResponseWindow`/`response_mode`. |
| 3 | Difficulty model ownership (neutral bands vs domain-owned mapping). | No for Phase 4 schema | Can start with neutral bands and `difficulty_dimensions` JSON; formalize in Phase 5A. |
| 4 | Spacing/history engine boundary. | No for Phase 4 | Consolidation protocols are Phase 5+; scheduler design can resolve. |
| 5 | EEG context representation. | No for Phase 4 | Phase 5B co-design; protocol library only requires `eeg_context_ref` pointer. |
| 6 | Stochastic policy determinism. | No | Add `random_seed`/`draw` fields to `ScheduleDecision`/`AdaptationDecision` payloads. |
| 7 | Self-confirmation vs machine score reconciliation. | No for Phase 4 | Metrics hygiene already requires labeling; can refine in Analysis. |
| 8 | Protocol composition (single vs multiple protocols per `Session`). | No | `ProgramVersion.protocol_version_sequence` already supports sequencing. |
| 9 | Minimal-pair / error asset generation authority. | No for schema | Domain adapter / `mpe_audio` pipeline responsibility; clarify in provider contracts. |
| 10 | Rich protocol graph (`branch_spec` on `ProtocolStep`) vs sequence-only `ProtocolVersion`. | **Potential blocker for protocols requiring loops/branches in fixture** | Can be resolved by mapping `Branch`/`Transition`/`Repeat` to `ScheduleDecision` + `Block.exit_condition` for Phase 4, or by a future schema extension. ADR if extending `ProtocolVersion`. |

## 11. Implementation dependencies

- `Phase 4A` (completed): canonical enums, identifiers, `Protocol`/`ProtocolVersion`/`Program`/`ProgramVersion` fixtures, `TaskDefinition`, `Instruction`, `StimulusRequest`, `ResponseWindow`, `FeedbackEvent`, `ScheduleDecision`, `AdaptationDecision` schemas.
- `Phase 4B` (completed through 4B.3): runtime, event store, replay, CLI, provider orchestration.
- `Phase 4B.4` (pending authorization): Hebrew `DomainProvider`, `Renderer`, `Evaluator` integration; needed to run the Hebrew examples.
- `MPE_AUDIO_PIPELINE` Phase B–G (pending authorization): `mpe_audio` SpeechGen adapter, asset pipeline, registry, `Renderer` integration; needed for prefetched local audio assets.
- `Phase 5A`: adaptation policy framework and typed difficulty dimensions.
- `Phase 5B`: sensor/EEG `ObservationProvider` and `StateInferenceModel` for EEG-context decisions.
- `Phase 6`: protocol library authoring tools, longitudinal learning, A/B testing.

No implementation is authorized by this Phase A record.

## 12. Risks

| Risk | Source | Status in MPE v1.1 |
|---|---|---|
| Premature DSL commitment if Protocol Library primitives are treated as a textual language. | `MPE_PROTOCOL_LIBRARY_v1.0.md` §6, Appendix C | Mitigated by `MPE_DSL_DECISION_RECORD.md` and explicit reconciliation: primitives are semantic, typed model is concrete. |
| Protocol graph expressiveness (`branch_spec`) beyond current `ProtocolVersion`/`Block` schema. | §3.2, §6, §12 | Low: Phase 4 can implement canonical protocols via `ScheduleDecision` + `Block.exit_condition`; future ADR can extend the fixture schema. |
| Self-confirmation mechanism undefined, blocking internal-speech protocols. | §10, §19.1 | High: requires ADR before implementation. |
| `AdaptationDecision` conceptual model in Protocol Library omits required MPE fields. | §12 | Low: reconciled document now references the full `MPE_ADAPTATION_CONTRACT.md` schema; implementation must use it. |
| `ExecutionPlan`/`ExecutionResult`/`ProtocolSummary` confused with core objects. | §12, §16 | Low: reconciled as runtime-derived artifacts / `Outcome` + derived analytics. |
| EEG-context adaptation not yet grounded in `StateInferenceModel` outputs. | §9, §8 | Mitigated by `MPE_ADAPTATION_CONTRACT.md` Phase 5C rules; default `exploratory_only`. |
| Asset role `instruction` collides with `Instruction` object name. | §14, Glossary | Low: clarified as a media role distinct from `InstructionType`. |
| Domain-independence drift if per-protocol Hebrew examples leak into definitions. | §4, §7, Appendix C | Mitigated by portability test and explicit "examples only" markers. |

## 13. Acceptance criteria

- [x] Documents reviewed list complete.
- [x] Conceptual-entity-to-repository-contract mapping produced.
- [x] Primitive-to-contract mapping table produced.
- [x] Lifecycle-to-runtime mapping table produced.
- [x] Adaptation compatibility assessment produced with source/parameter mapping.
- [x] Replay compatibility assessment produced.
- [x] Audio-boundary assessment produced and aligned with `mpe_audio` decisions.
- [x] EEG-policy assessment produced and aligned with `MPE_ADAPTATION_CONTRACT.md`.
- [x] Normative-status classification produced.
- [x] Unresolved decisions identified with blocker status.
- [x] Implementation dependencies listed.
- [x] Risks identified.
- [x] `MPE_PROTOCOL_LIBRARY_v1.0.md` reconciled (no textual DSL references, object model aligned with MPE, mapping appendix added).
- [x] `PROJECT_STATE.md` and `NEXT_TASK.md` not modified.
- [x] Audio pipeline documents not modified except as compatibility references.
- [x] No implementation code written.

## 14. Final recommendation

**APPROVE_PROTOCOL_LIBRARY_ARCHITECTURE_WITH_CONDITIONS**

The Protocol Library v1.0 architecture is accepted as the semantic definition layer for MindTune protocols, subject to the following conditions:

1. The Protocol Library document is reconciled to remove any implication that the primitive names are an approved textual DSL; their concrete expression is the MPE typed model (`Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, `FeedbackEvent`).
2. The `AdaptationDecision` conceptual model in the Protocol Library explicitly defers to the full `MPE_ADAPTATION_CONTRACT.md` schema (including `deployment_status`, `allowed_bounds`, `source_event_ids`, `evidence_record_ids`, `aggregation_window`, `minimum_evidence`, `uncertainty_threshold`, `confidence`, `cooldown`, `hysteresis`, `maximum_step_size`, `rollback_rule`, `abstention_rule`, `decision`).
3. `ExecutionPlan`, `ExecutionResult`, and `ProtocolSummary` are treated as runtime-derived artifacts or `Outcome`/derived views, not as new core objects, until an ADR justifies elevating them.
4. The self-confirmation capture mechanism (unresolved decision #1) is resolved through an ADR before implementing Internal Speech or Recall protocols end-to-end.
5. The protocol graph question (unresolved decision #10) is resolved before Phase 4 fixtures require loops/branching beyond `ScheduleDecision` + `Block.exit_condition`.
6. Implementation of any protocol runtime logic requires explicit user authorization and proceeds through the existing phase plan (`PROJECT_STATE.md` / `NEXT_TASK.md`).
