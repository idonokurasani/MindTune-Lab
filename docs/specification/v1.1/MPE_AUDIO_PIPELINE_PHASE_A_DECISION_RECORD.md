# MPE Audio Pipeline — Phase A Decision Record

## 1. Repository baseline inspected

- `docs/specification/v1.1/MPE_AUDIO_ASSET_PIPELINE_SPEECHGEN_HEBREW_v0.1.md` — Cloud-authored audio pipeline design (provided as an HTML document on the Desktop, converted to text and reviewed).
- `packages/mpe/src/mpe/` — current runtime implementation, event store, provider protocols, CLI, and types.
- `docs/MPE_ARCHITECTURE_V1_1.md`, `docs/MPE_OBJECT_MODEL_V1_1.md`, `docs/MPE_EVENT_MODEL_V1_1.md`, `docs/MPE_PROVIDER_BOUNDARIES.md`, `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`, `docs/MPE_CANONICAL_ENUM_REGISTRY.md`.
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`, `docs/MPE_ADAPTATION_CONTRACT.md`, `docs/MPE_DSL_DECISION_RECORD.md`, `docs/MPE_OPEN_DECISIONS.md`.
- `docs/MPE_PHASE_4_IMPLEMENTATION_PLAN.md`, `docs/specification/v1.1/IMPLEMENTATION_SEQUENCE.md`, `docs/specification/v1.1/DATABASE_SCHEMA_SPEC.md`.
- `docs/MPE_RISK_REGISTER_V1_1.md`, `docs/research/mpe_ontology_audit_v1/DOMAIN_INDEPENDENCE_MAP.md`.
- `docs/project/PROJECT_STATE.md`, `docs/project/NEXT_TASK.md`.
- `mantra/` and `hebrew/` top-level prototype packages.
- `Dockerfile`, `compose/testing.yaml`, `requirements.txt`, `packages/mpe/pyproject.toml`.

## 2. Documents and source modules examined

| Area | Key files |
|---|---|
| MPE core event model | `packages/mpe/src/mpe/events.py`, `MPE_EVENT_MODEL_V1_1.md` |
| MPE core object model | `MPE_OBJECT_MODEL_V1_1.md` (Program/ProgramVersion, Protocol/ProtocolVersion, Session, Trial, Instruction, StimulusRequest, RenderedStimulus, FeedbackEvent, AdaptationDecision, ScheduleDecision, ContentItem) |
| Provider boundaries | `MPE_PROVIDER_BOUNDARIES.md`, `packages/mpe/src/mpe/providers.py`, `MPE_HEBREW_PROVIDER_CONTRACT.md` |
| Identifiers and enums | `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`, `MPE_CANONICAL_ENUM_REGISTRY.md`, `packages/mpe/src/mpe/types.py`, `packages/mpe/src/mpe/enums.py` |
| Runtime and replay | `packages/mpe/src/mpe/runtime.py`, `packages/mpe/src/mpe/replay.py`, `packages/mpe/src/mpe/aggregates.py`, `packages/mpe/src/mpe/cli.py` |
| Persistence | `packages/mpe/src/mpe/event_store.py`, `packages/mpe/src/mpe/persistence/store.py` |
| Existing audio prototypes | `mantra/models.py`, `mantra/generator.py`, `mantra/piper_adapter.py`, `data/mantra/MANTRA_SCHEMA.md`, `data/mantra/UNCERTAINTIES.md` |
| Project state | `docs/project/PROJECT_STATE.md`, `docs/project/NEXT_TASK.md` |

## 3. Adopted decisions

The following decisions are adopted for the `mpe_audio` subsystem. They implement the ten authoritative decisions supplied for this task and reconcile them with MPE v1.1.

1. **Separate package.** `mpe_audio` lives under `packages/mpe_audio/`. It is never folded into `packages/mpe`. A `tools/mpe_audio/` lift-and-shift location is allowed only as a temporary staging area and must not be the production boundary.
2. **Two-part asset identity.** Every audio asset has a stable `logical_audio_asset_id` (semantic identity + role) and an immutable `audio_asset_version_id` (concrete version). Runtime playback and event records always identify the exact `audio_asset_version_id`. A session plan may resolve a logical id to a current approved version at planning time, but an already-created session plan or event stream must pin the concrete version.
3. **Physical deduplication at the object layer only.** Identical binary audio may be stored once and referenced by multiple logical assets. Logical asset records are never merged solely because their bytes are identical.
4. **Formats.** Archival master: FLAC. Delivery primary: Opus. Compatibility fallback/export: MP3. Mono. 48 kHz master. These are confirmed as the `mpe_audio` format policy; no codecs are installed and no implementation code is written in this task.
5. **Loudness and playback bounds.** -16 LUFS is a provisional engineering default, not a validated optimum. Playback-rate bounds and any pedagogical slow variants are pilot-validated before they become public contracts.
6. **Expected reading.** The authoritative phonological representation is Hebrew script with niqqud plus explicit stress. IPA and a versioned pedagogical transliteration are optional annotations, not the source of truth.
7. **Remote deletion.** SpeechGen remote storage is non-authoritative. Remote cleanup is configurable, best-effort, and runs only after successful download, validation, integrity verification, atomic local persistence, and manifest recording. It defaults to disabled and its failure never invalidates a local asset.
8. **EEG boundary.** MPE core receives only generic observations and event references. `mpe_audio` does not contain EEG-specific semantics, does not compute attention/load/engagement/correctness, and does not adapt audio. The runtime may vary playback instructions through independently authorized policies, but the approved source asset remains immutable.
9. **Contract reuse.** `mpe_audio` reuses MPE v1.1 `ContentItem`, `StimulusRequest`, `RenderedStimulus`, `Instruction`, `feedback_started`/`stimulus_started`/`stimulus_completed`, `AdaptationDecision`, `ScheduleDecision`, and `EvidenceRecord`. New audio-specific concepts are kept inside `mpe_audio`.
10. **Mantra preservation.** The subsystem explicitly supports the original adaptive audio protocol concept (eyes-closed listening, internal retrieval, anticipation, external confirmation, adaptive pauses, bounded playback-rate changes, repetition/progression changes). `mpe_audio` prepares and resolves approved speech assets; it does not execute the cognitive protocol.

## 4. Contract-mapping table

| Audio design concept | Existing MPE v1.1 concept | Action | Rationale |
|---|---|---|---|
| `LinguisticAudioSource` | `ContentItem` produced by `HebrewDomainProvider` | Extend / wrap | MPE already owns domain-neutral content identity. The audio pipeline adds an audio-specific view but must not replace `ContentItem`. |
| `SynthesisRequest` (canonical, provider-neutral) | `StimulusRequest` | Reuse / extend | `StimulusRequest` already carries `content_item_id`, `renderer_id`, `voice_id`, `rate`, `prosody_hints`. `mpe_audio` can place `voice_profile_id` and `asset_role` inside `prosody_hints` to avoid changing the MPE envelope. |
| `ProviderSynthesisRequest` | None (adapter-internal) | Reject as public contract | This is a Layer-2 adapter implementation detail; it never crosses into MPE core. |
| `SpeechSynthesisProvider` interface | `Renderer` Protocol (`packages/mpe/src/mpe/providers.py`) | Retain / implement | MPE already defines `Renderer(capabilities, render)`. The SpeechGen adapter is a `Renderer` implementation. |
| `GeneratedAudioAsset` | `RenderedStimulus` + new `AudioAssetVersion` registry record | Split / extend | `GeneratedAudioAsset` conflates the approved asset record with the runtime resolution result. MPE `RenderedStimulus` is the runtime result; `AudioAssetVersion` is the immutable registry record. |
| `AudioAssetManifest` | None | Extend | Batch-level preparation manifest is an `mpe_audio` internal concept; it is not a core MPE object. |
| `AudioPlaybackEvent` | `stimulus_started`, `stimulus_completed`, `feedback_started` | Reuse / extend | New event types are not needed. Audio-specific fields (`audio_asset_version_id`, `runtime_playback_rate`, `voice_profile_id`) are added to the existing event payloads. |
| `AdaptiveTimingDecision` | `AdaptationDecision` + `adaptation_proposed/applied/abstained/reversed` and `ScheduleDecision` | Reuse / reject | Runtime adaptation is outside `mpe_audio`. Timing decisions are MPE `AdaptationDecision`/`ScheduleDecision` events. |
| `AudioReview` | None (human asset approval record) | Retain as `mpe_audio` internal | This is approval of a generated audio file, not a learner response, so it is not an MPE `Evaluation`. |
| `VoiceProfile` | `renderer_id` + `voice_id` | Retain as `mpe_audio` registry concept | Runtime sees only `renderer_id` and `voice_id` strings; `VoiceProfile` is the `mpe_audio` mapping layer. |
| `AssetRole` (`natural`, `pedagogical_slow`, `prompt`, `confirmation`, etc.) | `InstructionType`, `FeedbackCategory`, `FeedbackType`, `content_type` | Map, do not duplicate | Asset role describes the intended use of an audio file. It is stored in `mpe_audio` and surfaced through `StimulusRequest.prosody_hints` or `Instruction.instruction_type` / `FeedbackEvent.feedback_type`. It is not a new core enum. |
| DSL primitives (`play`, `anticipate`, `pause`, `expect`, `confirm`, `repeat`, `branch`, `transition`) | `Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, `SafetyInstruction` | Reject as DSL | `MPE_DSL_DECISION_RECORD.md` forbids a textual DSL in Phase 4. Use the typed protocol model. |
| `expected_reading` | `ContentItem.pronunciation_metadata` (advisory) | Extend | Pronunciation metadata is already advisory in MPE. `expected_reading` becomes a structured field inside it, not a single authoritative string. |
| `audio_asset_id` (version-specific) | `rendered_stimulus_id` / `RenderedStimulus` | Rename | Use `audio_asset_version_id` for the concrete version and `logical_audio_asset_id` for the stable identity. |
| `request_fingerprint` | None (internal) | Retain as `mpe_audio` internal | Fingerprint is for idempotency and dedup inside the audio pipeline. |
| `content_hash` / `audio_hash` | None | Retain as `mpe_audio` internal | Integrity fields belong to the audio asset manifest, not MPE core event schemas. |

## 5. Identified conflicts

| # | Conflict | Resolution |
|---|---|---|
| 1 | Cloud design allows `mpe_audio` inside `packages/mpe/` or under `tools/` as a permanent home (§20 Options A and C). | Enforce Option B: `packages/mpe_audio/` is the production boundary. `tools/` is allowed only as a temporary lift-and-shift staging area. |
| 2 | Cloud design uses `audio_asset_id` for the concrete version and does not separate stable logical identity from concrete version (§9, appendix). | Introduce `logical_audio_asset_id` (stable semantic identity + role) and `audio_asset_version_id` (immutable concrete version). Runtime events record `audio_asset_version_id`. |
| 3 | Cloud design introduces new event types `AudioPlaybackEvent` and `AdaptiveTimingDecision` (§13). | Reuse existing MPE events (`stimulus_started`, `stimulus_completed`, `feedback_started`, `adaptation_proposed`, `adaptation_applied`, `schedule_decision`). Audio-specific fields are payload extensions. |
| 4 | Cloud design proposes a textual DSL (`play`, `anticipate`, `pause`, `expect`, `confirm`, `repeat`, `branch`, `transition`) (§11). | Reject. `MPE_DSL_DECISION_RECORD.md` closes the question: typed model only in Phase 4, textual DSL deferred. |
| 5 | Cloud design's `GeneratedAudioAsset` is used as both an approved immutable asset and a runtime playback instruction (appendix). | Split into `AudioAssetVersion` (approved registry record) and `RenderedStimulus` (runtime resolution result). `RenderedStimulus` is always the runtime boundary. |
| 6 | Cloud design encodes -16 LUFS as a fixed loudness target and `[0.9, 1.15]` as permanent safe playback-rate bounds (§B, §12). | Mark these as provisional engineering defaults with `evidence_grade: simulation_default`; final values are pilot-validated and never encoded as immutable public contracts. |
| 7 | Cloud design's `expected_reading` is a single string (§7). | Make it a structured object: Hebrew with niqqud (source truth), explicit stress, optional IPA, and a versioned pedagogical transliteration. Transliteration is not authoritative. |
| 8 | Cloud design's remote `/delete` behavior is optional and loosely defined (§6, §14). | Default to disabled; deletion is best-effort after local persistence; failure is non-fatal. |
| 9 | Cloud design's `AdaptiveTimingDecision` places adaptation logic inside the audio subsystem (§13). | Remove. Adaptation policies are MPE runtime concerns; `mpe_audio` only exposes `VoiceProfile.allowed_runtime_playback_rate_bounds` as configuration. |
| 10 | Existing `MPE_OPEN_DECISIONS.md` #7 canonical TTS voice lists Piper and Azure as candidates; the Cloud design is SpeechGen-only. | Treat SpeechGen as an additional candidate provider. `MPE_OPEN_DECISIONS.md` #7 and `MPE_HEBREW_PROVIDER_CONTRACT.md` should be updated through the ADR process to list `speechgen` as an allowed `renderer_id`. This is an external documentation action, not part of this Phase A deliverable. |
| 11 | Cloud design stores `provider_project_id`, `provider_voice_id`, and provider cost data on the asset (§6, appendix). | Keep these fields inside `mpe_audio` asset manifests for audit. Ensure they never leak into MPE core events, `ProtocolVersion` definitions, or the `RenderedStimulus` contract. |

## 6. Required edits to the Cloud design

The reconciled `MPE_AUDIO_ASSET_PIPELINE_SPEECHGEN_HEBREW_v0.1.md` in this directory implements the following edits:

1. Rename `audio_asset_id` to `audio_asset_version_id` for concrete versions and add `logical_audio_asset_id` for stable identity.
2. Add explicit session-pinning semantics: runtime resolves `logical_audio_asset_id` → `audio_asset_version_id` at `stimulus_ready` and records the concrete id in `stimulus_started`/`feedback_started` payloads.
3. Replace `AudioPlaybackEvent` and `AdaptiveTimingDecision` with payload extensions to existing MPE events.
4. Remove the textual DSL section; map each primitive to the typed MPE model (`Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, `SafetyInstruction`).
5. Mark `-16 LUFS` and playback-rate bounds as provisional and pilot-validated.
6. Restructure `expected_reading` as a source-truth-plus-annotations model.
7. Define remote deletion as `auto_delete_remote=False` by default, best-effort, and non-fatal.
8. Clarify the `mpe_audio` boundary: no EEG semantics, no adaptation computation, no correctness logic.
9. Update §20 packaging to require `packages/mpe_audio/` and reject folding into `mpe` or permanent `tools/` residence.
10. Map `GeneratedAudioAsset` to `AudioAssetVersion` (registry) and `RenderedStimulus` (runtime) explicitly.
11. Add a reconciliation change log to the Cloud design document.

## 7. Final package dependency graph

```text
packages/mpe/                    (runtime, event store, replay, provider protocols)
    ├── packages/mpe/src/mpe/providers.py  Renderer Protocol
    ├── packages/mpe/src/mpe/events.py     event taxonomy + payload schemas
    └── packages/mpe/src/mpe/types.py      Identifier types

packages/mpe_audio/              (SpeechGen adapter, asset pipeline, registry, CLI)
    ├── depends on mpe.providers.Renderer
    ├── depends on mpe.events.Event envelope + StimulusRequest/RenderedStimulus payload schemas
    ├── may depend on hebrew/ package only for source content lookup during preparation
    └── never imported by packages/mpe/ at import time

Runtime wiring (entry point / config, not a compile-time import):
    mpe runtime ──(renderer_id string, e.g. "mpe_audio.speechgen")──▶ mpe_audio renderer
```

`mpe_audio` may import `mpe` types and protocols. `mpe` never imports `mpe_audio`. The renderer is loaded at runtime through an entry point or a plugin registry configured in `ProtocolVersion.required_providers`. No circular import is possible because the dependency is one-way.

## 8. Asset identity and versioning model

```text
ContentItem (from HebrewDomainProvider)
    └── logical_audio_asset_id  (stable: content_item_id + role + voice_profile_family)
            ├── audio_asset_version_id  v1  (immutable, approved)
            ├── audio_asset_version_id  v2  (immutable, approved, supersedes v1)
            └── ...
```

- `logical_audio_asset_id` is a stable string derived from the linguistic item, the intended `AssetRole`, and a logical voice-profile family. It may resolve to different `audio_asset_version_id`s over time.
- `audio_asset_version_id` is a UUID or content-derived identifier that uniquely identifies one immutable generated file set (master + delivery + manifest).
- Every `audio_asset_version_id` records `parent_asset_version_id` (null for first), `asset_version` integer, `created_at`, and `review_status` (`generated`, `pending_review`, `approved`, `rejected`, `superseded`).
- Only `approved` versions are runtime-eligible.
- Superseded versions are retained so historical event streams can replay the exact audio that was originally played.

## 9. Runtime asset-pinning and replay semantics

A session plan references `logical_audio_asset_id` + `voice_profile_id` + `role`. Two pinning strategies are valid; the chosen one must be consistent per protocol and recorded in `ProtocolVersion.dependency_versions`:

1. **Pre-session pin.** At `session_created`/`session_started`, the runtime resolves every logical audio asset reference to a concrete `audio_asset_version_id` and stores the pin map in the session start metadata. This makes the entire session reproducible from the start.
2. **Just-in-time pin.** At each `stimulus_ready` event, the `Renderer` resolves the logical reference and returns a `RenderedStimulus` containing the concrete `audio_asset_version_id`. The runtime emits `stimulus_ready`/`stimulus_started`/`feedback_started` with the concrete id.

**Replay guarantee:** The event stream stores the concrete `audio_asset_version_id`. `Replay` reconstructs the same `RenderedStimulus` references. The asset registry keeps all versions, including superseded ones, so replay never silently resolves to a newer file. New sessions may resolve to the current approved version, but replay always uses the version recorded in the events.

## 10. Storage and deduplication decision

```text
MPE_AUDIO_STORE_ROOT/
  objects/
    <audio_hash[:2]>/<audio_hash>.flac       # content-addressed master bytes
    <audio_hash[:2]>/<audio_hash>.opus        # derived delivery object (may share master hash)
    <audio_hash[:2]>/<audio_hash>.mp3         # optional fallback object
  assets/
    <logical_audio_asset_id>/
      <audio_asset_version_id>/
        asset.json          # AudioAssetVersion metadata + pointers to object hashes
        source.txt          # normalized input text actually sent to provider
        provider_raw.json   # redacted provider response
        review.json         # AudioAssetReview record(s)
```

- Deduplication happens at the `objects/` layer: identical master audio bytes are stored once and referenced by any number of `asset.json` records.
- Logical records under `assets/` are never merged. Two different `logical_audio_asset_id`s may point to the same object hash.
- Writes are atomic: download to a temp file, validate/hash, then rename into the final path. No consumer sees a partial asset.

## 11. Codec and operational dependency assessment

| Choice | Rationale | Runtime impact |
|---|---|---|
| Master: FLAC | Lossless archival; internal MD5 supports integrity verification. | Requires `ffmpeg`/`flac` in `mpe_audio` environment; not in `mpe`. |
| Delivery: Opus | High quality at low bitrate; suitable for streaming/eyes-closed use. | Requires `ffmpeg`/`opusenc` or `libopus` bindings in `mpe_audio`; not in `mpe`. |
| Fallback: MP3 | Compatibility for players that cannot decode Opus. | Same toolchain as Opus; generated from master on demand. |
| Mono, 48 kHz | Single-speaker pedagogical speech; 48 kHz is a clean production rate. | No runtime impact; kept in `mpe_audio` normalization policy. |

The existing `Dockerfile` (`packages/mpe` only) does not need audio codecs. When `mpe_audio` is built, a separate image or multi-stage build will install `ffmpeg`, `opus-tools`, and any Python audio libraries (`pydub`, `soundfile`, `requests`, etc.) as `mpe_audio` dependencies. `packages/mpe` retains its current minimal dependency set (`pydantic`, `typing-extensions`).

## 12. Expected-reading representation

The authoritative source of phonological truth is Hebrew script with niqqud, as provided by the Hebrew `DomainProvider` in `ContentItem.surface_form`.

```text
expected_reading (structured):
  ├── hebrew_with_niqqud     # source truth
  ├── stress_syllable_index  # 1-based primary stress
  ├── ipa_phonemes           # optional, versioned
  ├── transliteration        # versioned pedagogical scheme, not authoritative
  └── transliteration_version
```

`mpe_audio` uses `hebrew_with_niqqud` as the canonical synthesis input for isolated or ambiguous items. If a provider pronunciation does not match the expected stress/IPA, the asset is rejected; the source is never rewritten to match the provider.

## 13. Remote deletion policy

Remote SpeechGen files are non-authoritative. After local persistence, the system may optionally call `/delete`.

- Default: `auto_delete_remote = false`.
- When enabled, deletion is attempted only after: successful download, MIME/header validation, audio hash verification, atomic local write, and manifest recording.
- Deletion is best-effort. Failure is logged; it does not mark the local asset invalid.
- Credentials for `/delete` are the same as for synthesis; they come from the environment and never appear in manifests.

## 14. Security boundary

- SpeechGen `token` and `email` are loaded only from environment variables or a secret store (`SPEECHGEN_TOKEN`, `SPEECHGEN_EMAIL`).
- No credentials in source control, manifests, logs, or MPE events.
- TLS verification is always enabled; the SpeechGen example that disables `CURLOPT_SSL_VERIFYHOST/PEER` is rejected.
- Provider-specific identifiers (`provider_project_id`, `provider_job_ref`) live only in `mpe_audio` manifests, never in `ProtocolVersion`, `StimulusRequest` payload, or event payload.
- `provider_raw.json` is redacted before persistence.
- Downloads enforce max content length, expected MIME type, and audio header sniffing.
- Atomic writes prevent partial assets.

## 15. EEG and adaptation boundary

- `mpe_audio` must not calculate attention, cognitive load, engagement, or correctness.
- `mpe_audio` must not emit adaptation decisions.
- Runtime policies (outside `mpe_audio`) may produce `AdaptationDecision` events with `target_dimension` values such as `pause_duration` or `playback_rate`. These policies may consult `StateEstimate` objects, which remain `exploratory_only` by default.
- `mpe_audio` supplies each `VoiceProfile` with pilot-validated `allowed_runtime_playback_rate_bounds` and a list of pre-synthesized pedagogical variants. The runtime chooses between a normal asset and a slow variant; it does not time-stretch outside validated bounds.
- Where behavioral evidence and EEG-derived context conflict, behavioral evidence wins.

## 16. CLI namespace recommendation

The existing `mpe` console script is unchanged:

```text
mpe run-mock-session
mpe replay <session-id>
mpe list-sessions
mpe validate-store
```

The audio pipeline uses a separate console script to avoid coupling `packages/mpe` to audio dependencies and to avoid namespace collision:

```text
mpe-audio voices list [--lang he]
mpe-audio pilot prepare
mpe-audio generate --manifest <path> [--dry-run] [--budget N] [--max-items N] [--confirm]
mpe-audio review export [--batch <id>]
mpe-audio approve <logical_audio_asset_id>@<version>
mpe-audio validate [--all | --asset <id>]
mpe-audio cost-report [--batch <id>]
```

No `mpe audio` subcommand is introduced in `packages/mpe/cli.py`.

## 17. Proposed implementation phases

The Cloud design's phases are adjusted to respect MPE v1.1 contracts and the Phase 4 boundaries.

1. **Phase A (this task):** Contracts and decision record. No code.
2. **Phase B:** SpeechGen adapter implementing the MPE `Renderer` Protocol, with mocked-HTTP unit tests. No paid calls.
3. **Phase C:** Asset pipeline — request fingerprinting, safe download, integrity hashing, normalization, atomic storage, manifest schema.
4. **Phase D:** `AudioAssetVersion` registry and `Renderer.render` resolution from `StimulusRequest` to `RenderedStimulus`.
5. **Phase E:** Cost/quota controls and `mpe-audio` CLI.
6. **Phase F:** Pilot — 50–100 representative Hebrew items, multi-voice, rubric-based scoring. Gate before bulk generation.
7. **Phase G:** MPE runtime integration — payload extensions for `audio_asset_version_id`, replay-pinning tests, and a zero-provider-call adaptive session test.
8. **Phase H (ADR-gated):** Update `MPE_OPEN_DECISIONS.md` #7 and `MPE_HEBREW_PROVIDER_CONTRACT.md` to add `speechgen` as a candidate `renderer_id`, if the pilot selects it.

## 18. Risks and unresolved decisions

| Risk | Mitigation | Status |
|---|---|---|
| SpeechGen Hebrew quality on gutturals, sheva, stress, unpointed ambiguity | Pilot gate + mandatory human review | Open until Phase F |
| Provider drift (voice removal, pronunciation change) | Voice-profile versioning, periodic re-validation, local-copy independence | Accepted design |
| Playback-rate phonetic degradation | Conservative bounds + separately synthesized slow variants | Open until pilot |
| Duplicate billing on retries | Request fingerprint dedup before any paid re-issuance | Accepted design |
| Opus decoder availability on target players | Pilot validates; MP3 fallback retained | Open until Phase F |
| Master fidelity if provider returns lossy | `master_is_lossy` flag + human review | Accepted design |
| Conflict with `MPE_OPEN_DECISIONS.md` #7 (Piper/Azure) | Add SpeechGen as a candidate through ADR process | Unresolved external doc action |
| Event schema extension for `audio_asset_version_id` | Requires ADR before implementation; Phase A designs it only | Unresolved until ADR |
| Legacy `mantra/` and `hebrew/` top-level packages | `mpe_audio` is the production boundary; legacy prototypes may be lift-and-shift sources only | Accepted design |

## 19. Objective acceptance criteria

- [x] Contract-mapping table produced.
- [x] All conflicts between the Cloud design and MPE v1.1 contracts identified.
- [x] No provider-specific dictionaries, URLs, credentials, project IDs, or SpeechGen status codes leak into MPE core or protocol definitions.
- [x] Minimal shared contract surface between `mpe` and `mpe_audio` defined (`Renderer` Protocol, `StimulusRequest`, `RenderedStimulus`, `ContentItem` references).
- [x] `RenderedStimulus` contract clarified: it is the runtime resolution result; the approved asset is `AudioAssetVersion`.
- [x] Distinction among linguistic source, synthesis request, provider job, generated candidate, reviewed asset version, resolved runtime stimulus, and playback event defined.
- [x] Session-pinning and replay semantics defined.
- [x] Package dependency direction stated and circular-import-free.
- [x] Asset identity (`logical_audio_asset_id`, `audio_asset_version_id`) defined.
- [x] Storage, deduplication, codec, and dependency assessment documented.
- [x] Expected-reading model defined.
- [x] Remote deletion policy defined.
- [x] Security boundary defined.
- [x] EEG and adaptation boundary defined.
- [x] CLI namespace recommendation given.
- [x] `PROJECT_STATE.md` and `NEXT_TASK.md` were read and left unchanged per instructions.
- [x] No production code or tests written.
- [x] Modified Cloud design preserves original intent and records changes.

## 20. Final recommendation

APPROVE_AUDIO_PIPELINE_IMPLEMENTATION_SCOPE

The audio pipeline scope is architecturally sound once the reconciled Cloud design and this decision record are accepted and the unresolved external documentation actions (ADR update for `speechgen` as a candidate `renderer_id`, event payload extension ADR) are completed before implementation. Empirical parameters (loudness target, playback-rate bounds, Opus fallback, expected-reading conventions) must be finalized in the Phase F pilot, not encoded as permanent contracts before validation. Actual implementation requires explicit authorization outside this Phase A documentation task.
