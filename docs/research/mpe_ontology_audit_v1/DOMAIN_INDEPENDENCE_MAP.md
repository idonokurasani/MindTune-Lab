# Domain Independence Map v1

## Principle

The MPE core must be domain-neutral. All domain-specific knowledge lives in providers.

## What belongs in MPE core

- Session lifecycle management.
- Event scheduling and timestamp ownership.
- Event stream immutability and replay.
- Trial role orchestration.
- Response window management.
- Provider interface contracts.
- Safety rule execution.
- Versioning of `ProgramVersion` and `ProtocolVersion`.
- Scheduling decisions (algorithm, not content).
- Adaptation policy execution framework (policies themselves are pluggable).
- Outcome computation from events (formulas, not domain semantics).

## What belongs outside MPE core

| Concern | Owner in Hebrew domain | Owner in future domains |
|---|---|---|
| Content identity and metadata | `HebrewDomainProvider` | `MusicDomainProvider`, `MemoryDomainProvider`, etc. |
| Correctness and variants | `HebrewEvaluator` | Domain-specific evaluator |
| Audio rendering | `HebrewRenderer` / TTS adapter | Domain renderer |
| Response capture | `ButtonObservationProvider`, `MicrophoneObservationProvider` | Same or domain-specific |
| Response interpretation (ASR, button mapping) | `HebrewResponseInterpreter` | Domain response interpreter |
| Domain normalization | `HebrewDomainNormalizer` | Domain normalizer |
| Item scheduling policy | `HebrewItemPolicy` (e.g., spaced Hebrew verbs) | Domain item policy |
| EEG interpretation | `StateInferenceModel` (exploratory) | Same |

## MPE core must not contain

- Hebrew binyan, root, or niqqud logic.
- EEG band-power semantics (alpha, theta, beta, mu).
- Specific claims about attention, arousal, load, fatigue.
- Difficulty dimensions that depend on Hebrew morphology.
- Evaluation of Hebrew correctness.
- Audio generation details.
- Domain-specific content metadata interpretation.

## Provider contract table

| Interface | MPE core uses it for | Provider implements |
|---|---|---|
| `DomainProvider` | Content lookup and expected-answer retrieval | Content identity, metadata, scope, confidence |
| `Renderer` | Media production | TTS, recorded audio, sound synthesis |
| `ObservationProvider` | Raw input capture | Buttons, microphone, keyboard, sensors |
| `ResponseInterpreter` | Domain-agnostic extraction from observations | ASR, button label mapping, keystroke parsing |
| `DomainNormalizer` | Canonical domain form for evaluation | Hebrew spelling normalization, music interval canonicalization |
| `Evaluator` | Correctness verdict | Hebrew correctness, music interval correctness |
| `Scheduler` / `ItemPolicy` | Item selection | Spacing, difficulty, review logic |
| `StateInferenceModel` | Optional advisory state estimates | EEG/behavior feature models |

## Consequences

- Adding a new domain requires implementing the provider interfaces; MPE core is unchanged.
- Changing the Hebrew engine requires updating the Hebrew provider implementations; MPE core is unchanged.
- EEG interpretation can be replaced or disabled without touching session orchestration.
- Behavioral adaptation policies can be tested and deployed independently of sensor models.
