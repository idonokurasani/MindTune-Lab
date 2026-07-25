# Curriculum-to-Asset Contract Architecture

## 1. Purpose

This document defines the deterministic contract between curriculum selection,
reviewed linguistic specifications, asset preparation, and audio execution for
Phase 1 Hebrew mantras.  The goal is to make every decision reproducible and
every layer replaceable without cross-cutting changes.

## 2. Layer responsibilities

### Curriculum layer

- Owns the ordered list of verbs the learner may encounter.
- Stores only pedagogical metadata (verb_id, infinitive, binyan, frequency,
  priority, selection reason).
- Does **not** store voice identifiers, TTS text, or provider details.
- Exported as `data/hebrew/curriculum_v1_320.json`.

### Linguistic specification layer

- Owns the reviewed paradigm for a single verb.
- Stores `HebrewTextPair(source_text, tts_text)` for every form.
- Records review status independently for linguistics and audio.
- Provides `HebrewVerbSpecification` and `PedagogicalEntry`.

### Audio profile layer

- Owns provider, voice, locale, format, sample-rate, and synthesis parameters.
- Production profile resolves Italian to `Giuseppe` and Hebrew to `Aaron`.
- Switching voices requires changing only the profile file; curriculum and
  specifications are voice-independent.

### Asset requirement layer

- Builds `AudioAssetRequirement` objects from a specification and a profile.
- Produces deterministic asset IDs and cache keys.
- Does **not** call SpeechGen.

### Asset inventory layer

- Inspects existing assets and classifies each requirement.
- Distinguishes valid, missing, incompatible, unreviewed, and legacy states.
- Read-only; no TTS calls.

### Eligibility layer

- Combines curriculum, specification, profile, and inventory into a
  `VerbReadinessReport`.
- Separates *learner execution eligibility* from *asset preparation
  eligibility*.
- Emits stable rejection reason codes.

### Selection-policy layer

- Consumes `LearnerState` and readiness reports.
- Selects the next verb deterministically.
- Emits `verb_id`, `reason_code`, and `policy_version`.
- Never reads EEG, never calls TTS.

### Execution-plan layer

- Converts a selected verb into an ordered `MantraExecutionPlan`.
- Includes plan schema version, profile ID/version, curriculum version,
  specification version, and checksum.
- No SpeechGen client, EEG data, or mutable learner state.

### Audio runtime layer

- Accepts a validated `MantraExecutionPlan` and an `AudioAssetRegistry`.
- Resolves assets in plan order and assembles the final WAV.
- Rejects missing or incompatible assets.
- Does **not** choose verbs or generate conjugations.

## 3. Forbidden dependencies

| source layer | may not depend on |
|--------------|-------------------|
| Audio runtime | curriculum selection, linguistic generation, EEG |
| Selection policy | EEG, TTS, audio filesystem mutation |
| Curriculum | voice identifiers, TTS text |
| Specification | audio provider, voice identifiers |
| Asset requirement | SpeechGen client, runtime state |
| Inventory | selection policy, learner state |

## 4. Determinism guarantees

- Same curriculum + same state + same inventory → same `verb_id`.
- Same specification + same profile → same `AudioAssetRequirement` list.
- Same plan inputs → same JSON serialization.
- Cache keys change only when synthesis-affecting values change.

## 5. Cache-key schema

Cache identity includes:

- provider
- exact voice identifier
- locale
- tts_text (Unicode-normalized)
- output format
- sample rate
- channels
- rate, pitch
- cache-key version

Learner-facing niqqud is not in the cache key unless it is sent to the provider.
