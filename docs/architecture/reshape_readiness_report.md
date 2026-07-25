# MindTune Lab Reshape Readiness Report

## 1. Scope

This report classifies each proposed future MindTune layer as ready,
partially ready, or blocked after Phase 4D.

## 2. Layer readiness

| Layer | Status | Evidence / Blockers |
|-------|--------|---------------------|
| Core protocol layer | partially ready | MPE protocol engine exists; integration with new asset contract in progress. |
| Curriculum Engine | ready | Versioned `curriculum_v1_320.json` and generator in place; audited. |
| Hebrew Domain Adapter | ready | Existing morphology/phase3 selection; new `mantra/domain/hebrew` specification layer added. |
| Linguistic Specification Repository | partially ready | Repository interface and vertical-slice fixtures created; full 320 specifications not yet produced. |
| Asset Contract | partially ready | `AudioProfile`, `AudioAssetRequirement`, and cache-key schema defined; inventory classification implemented for registry-backed assets. |
| Audio Profile Registry | ready | `data/audio_profiles/production.json` resolves Giuseppe/Aaron via configuration. |
| Asset Preparation Pipeline | partially ready | `build_asset_preparation_plan` separate from execution; SpeechGen client isolated. |
| Audio Runtime | partially ready | `build_compact_mantra` executes asset sequences; enhanced validation for plan metadata pending. |
| Review Engine | blocked | Human audio review metadata not yet populated; no human approval claimed. |
| Scheduling Engine | partially ready | `MantraSelectionPolicy` precedence implemented; EEG not used. |
| EEG Adapter | blocked | EEG not an input to Phase 1, by design. |
| Broader cross-domain reshape | blocked | Requires review engine, EEG adapter, and full 320 verb specifications. |

## 3. Production readiness

- 320-verb curriculum is generated and audited.
- Audio profile resolves to Giuseppe (Italian) and Aaron (Hebrew) through
  configuration, not hard-coded domain logic.
- Vertical-slice specifications exist for `לכתוב` (`lichtov`) and `להיות`
  (`lihyot`, referred to as `להוות` in planning documents).
- Asset requirement and inventory contracts are implemented.
- Selection policy is deterministic and EEG-free.

## 4. Remaining blockers before full reshape

1. Human linguistic and audio review metadata must be filled for all new
   assets.
2. Asset inventory must be validated against actual on-disk WAV metadata for
   sample-rate and voice mismatches.
3. Full 320 reviewed linguistic specifications are not generated.
4. EEG adapter is explicitly out of scope for Phase 1.
5. Audio runtime validation against profile metadata must be completed and
   tested.
