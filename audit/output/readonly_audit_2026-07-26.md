# Read-Only Audit — MindTune Console Hebrew / MPE Foundation

**Repository:** `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console`  
**Date:** 2026-07-26  
**Auditor:** Cascade (read-only, no source mutations)  
**HEAD:** `23ef2bb (HEAD -> feat/mindtune-lab-foundation) Remove Citizen Cafe and Streetwise Hebrew; integrate HeLP as canonical Hebrew source`  
**Working tree:** clean (`git status --short` empty)

---

## 1. Scope

This audit focused on the most recently active subsystems, consistent with the open documents and `AGENTS.md` guidance:

- Hebrew canonical lexical model (`HebrewLexicalEntity`)
- HeLP (Hebrew Lexicon Project) integration and repository
- Hebrew immediate-recall domain adapter and MPE protocol runner
- Legacy-source cleanup verification (Citizen Café / Streetwise Hebrew / Azure Speech)
- Hebrew audio asset inventory (`data/hebtts_eval/audio`, `output/mantra_global_tts_cache`)

No code was modified. All new content is confined to this report.

---

## 2. Repository state

| Check | Result |
|-------|--------|
| Branch | `feat/mindtune-lab-foundation` |
| Uncommitted changes | None |
| Tracked legacy data dirs | None (`citizen_cafe_all_courses`, `citizen_cafe_consolidation`, `hebrew_enrichment/streetwise_hebrew` removed) |
| Tracked legacy scripts | None (`build_citizen_cafe_all_courses.py`, `consolidate_citizen_cafe_corpus.py`, `import_streetwise_enrichment.py`, `test_azure_speech.py` removed) |
| Tracked Oura credential file | None; only `.oura_credentials.example` remains |

The most recent commit removed approximately **1.5 MB** of legacy Citizen Café / Streetwise / quizlet artifacts and replaced the runtime Hebrew source with HeLP evidence.

---

## 3. Files inspected

### Active implementation
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/canonical.py:1-74`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/adapter.py:1-134`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/fixtures.py:1-139`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/models.py:1-53`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/normalization.py:1-50`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/integration.py:1-111`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/help/repository.py:1-88`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/help/models.py:1-121`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/protocol/immediate_recall.py:1-461`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/protocol/providers_hebrew.py:1-212`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domain/base.py:1-100`

### Safeguards and tests
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/tests/test_forbidden_legacy_sources.py:1-117`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/tests/test_hebrew_domain.py:1-722`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/tests/test_help_integration.py:1-72`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/tests/test_hebrew_recovery.py:1-118`

### Reference documentation
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/HEBREW_SOURCE_CLEANUP_REPORT.md:1-77`
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/audits/final_independent_repository_audit.md:1-300`

---

## 4. Test results

All executed suites passed. Commands run:

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_forbidden_legacy_sources -v
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_shared_assets tests.test_mantra_engine tests.test_frontend_contracts tests.test_phase4d tests.test_curriculum_policy -v
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console:/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src .venv/bin/python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_hebrew_recovery tests.test_help_profiler -v
```

| Suite | Tests | Result |
|-------|-------|--------|
| `tests.test_forbidden_legacy_sources` | 4 | OK |
| Top-level selected policy/audio/contract suites | 75 | OK |
| `packages/mpe/tests` discovery | 224 | OK |
| `tests.test_hebrew_recovery` + `tests.test_help_profiler` | 10 | OK |

---

## 5. Static analysis

### Ruff

```bash
.venv/bin/ruff check packages/mpe/src/mpe/domains/hebrew \
                 packages/mpe/src/mpe/protocol/immediate_recall.py \
                 tests/test_forbidden_legacy_sources.py \
                 packages/mpe/tests/test_hebrew_domain.py \
                 packages/mpe/tests/test_help_integration.py
```

Result: `All checks passed!`

### mypy

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/mypy \
  packages/mpe/src/mpe/domains/hebrew \
  packages/mpe/src/mpe/protocol/immediate_recall.py \
  tests/test_forbidden_legacy_sources.py \
  packages/mpe/tests/test_hebrew_domain.py \
  packages/mpe/tests/test_help_integration.py
```

Result: 31 errors, **all in `packages/mpe/tests/test_hebrew_domain.py`**:
- `get_content_item` returns `HebrewContentItem | None`; tests call `build_prompt(item)` without a `None` guard, so mypy flags every such call.
- `run_hebrew_immediate_recall_session` is typed as returning `tuple[ImmediateRecallFixture, object]`; tests access `.runtime`, `.state`, `.events` on the `object` return.
- One comparison uses `int | None` without narrowing.

**Source files under `packages/mpe/src/mpe/domains/hebrew` and `packages/mpe/src/mpe/protocol/immediate_recall.py` reported no mypy errors.** The issues are test-side type precision, not runtime defects. `pyproject.toml` also reports unused `[tool.mypy]` module sections for `numpy`.

---

## 6. Legacy-source audit

### Active runtime / data scan

`tests/test_forbidden_legacy_sources.py` scans all text files outside declared historical exclusions. Result: **no active references** to `citizen cafe`, `citizen_cafe`, `streetwise hebrew`, `streetwise_hebrew`, `azure_speech`, or `azure speech`.

### Remaining historical mentions

Legacy names still appear only in documentation and audit artifacts that are intentionally excluded by the regression test:

- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/audits/final_independent_repository_audit.md` — records prior audit findings.
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/MPE_OPEN_DECISIONS.md` — lists `Azure` as a historical TTS candidate in an open decision.
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/specification/v1.1/MPE_AUDIO_PIPELINE_PHASE_A_DECISION_RECORD.md` — discusses SpeechGen-only design versus the older Azure/Piper options.
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/project/REPOSITORY_STRUCTURE.md` — migration notes for `azure_speech.py`.
- `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/MPE_PHASE_4_IMPLEMENTATION_PLAN.md` — mentions Azure/Piper renderer integration as a historical plan item.

These are documentation-only and do not affect runtime.

---

## 7. Audio asset inventory

### `data/hebtts_eval/audio`

- **Total files:** 52 (26 MP3, 26 WAV)
- **Total size:** 1.8 MB
- **Speakers / samples:**
  - `osim` — 40
  - `shaul` — 6
  - `geek` — 6

Sample contents include infinitive, past/present/future singular, sentence, repeat, and `topk` variants for verbs such as `להיות`, `לכתוב`, `לעשות`.

### `output/mantra_global_tts_cache`

- **Total files:** 110
- **Total size:** 7.8 MB
- Mix of `.wav` assets and `.meta.json` manifest files.

### `output/mantra_audio_assets.json`

- **Size:** 18 KB
- Shared audio asset registry referenced by `AGENTS.md`.

All `output/` directories are generated artifacts (ignored by `.gitignore`) and were treated as inventory only.

---

## 8. Architecture observations

### `HebrewLexicalEntity` / HeLP boundary

`@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/canonical.py:12-34` defines a frozen dataclass for canonical Hebrew lexical data. HeLP evidence is attached as read-only enrichment (`help_form_evidence`, `help_verb_summary`); learner state is explicitly excluded from the model. This matches the design rule that behavioral history, not psycholinguistic evidence, is authoritative.

`@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/help/repository.py:49-61` provides `enrich_entity`, which returns a new immutable entity rather than mutating the original.

### Domain-adapter boundary

`@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/adapter.py:21-117` implements the `DomainAdapter` contract:
- `build_prompt` is deterministic (SHA-256 over canonical JSON).
- `evaluate_response` produces a typed `DomainEvaluationResult`.
- `behavioral_evidence` strips Hebrew specifics and returns only `BehavioralEvidence`.

`@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/protocol/providers_hebrew.py:191-212` wires the adapter into a `ProviderSet`; the generic runtime in `immediate_recall.py` remains Hebrew-agnostic. Architectural guard tests in `test_hebrew_domain.py` confirm:
- `mpe/aggregates.py` contains no Hebrew labels.
- `mpe/protocol/immediate_recall.py` contains no Hebrew labels.
- The Hebrew domain module contains no `requests` or `http` imports.

### Immediate-recall runner

`@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/protocol/immediate_recall.py:81-112` is protocol-generic. It composes:
- `BoundedRepeatPlan`
- `CognitiveStateEstimator`
- `AdaptationPolicy`

and emits events through `TrialPipeline`. The Hebrew vertical slice reuses this runner unchanged via `run_hebrew_immediate_recall_session` in `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/integration.py:78-110`.

---

## 9. Findings

| # | Finding | Severity | Location / Evidence |
|---|---------|----------|---------------------|
| 1 | Legacy Citizen Café / Streetwise Hebrew / Azure Speech content fully removed from active runtime and tracked data. | Positive | `tests/test_forbidden_legacy_sources.py` passes; git diff shows ~1.5 MB deletions. |
| 2 | `HebrewLexicalEntity` is immutable and keeps HeLP evidence as read-only enrichment. | Positive | `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/canonical.py:11-34` |
| 3 | Hebrew domain adapter correctly isolates domain specifics from MPE runtime. | Positive | `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/domains/hebrew/adapter.py:102-116`, `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/protocol/providers_hebrew.py:191-212` |
| 4 | Immediate-recall runner is protocol-generic and reused for Hebrew. | Positive | `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src/mpe/protocol/immediate_recall.py:81-112` |
| 5 | Mypy reports test-only type errors in `test_hebrew_domain.py`; source code is clean. | Low | 31 errors in `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/tests/test_hebrew_domain.py` |
| 6 | Diagnostic scripts hardcode `Hannah` voice; this is consistent with `AGENTS.md` but bypasses `AudioProfile`. | Low / debt | Documented in `@/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/docs/audits/final_independent_repository_audit.md:209-216` |
| 7 | Historical docs still mention legacy providers; excluded from regression scan by design. | Informational | `docs/audits/`, `docs/project/`, `docs/specification/v1.1/`, `docs/MPE_OPEN_DECISIONS.md` |
| 8 | `pyproject.toml` has unused `[tool.mypy]` module sections for `numpy`. | Cleanup | mypy note: `unused section(s): module = ['numpy', 'numpy.*']` |

---

## 10. Recommendations

1. **Keep the legacy regression test.** `tests/test_forbidden_legacy_sources.py` is the canonical guard; ensure its exclusions remain accurate if historical docs are reorganized.
2. **Tighten test types.** Give `run_hebrew_immediate_recall_session` a proper return type (`tuple[ImmediateRecallFixture, ImmediateRecallResult]`) and add `assertIsNotNone` guards before `build_prompt` calls in `test_hebrew_domain.py` to eliminate the 31 mypy errors.
3. **Reconcile `AudioProfile` with diagnostics.** `scripts/build_lehitkasher_hannah_full_niqqud.py` and `scripts/build_compact_mantra_lehitkasher.py` intentionally use `Hannah` per `AGENTS.md`; consider loading this from a diagnostic profile fixture rather than hardcoding the voice string.
4. **Clean `pyproject.toml`.** Remove the unused `numpy` mypy module sections.
5. **No action required on output artifacts.** `output/` remains generated/ignored; the global TTS cache and asset registry are functioning as designed.

---

## 11. Verification commands

The following commands can be re-run to reproduce this audit:

```bash
cd /Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console

git status --short
git log --oneline -1

PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_forbidden_legacy_sources -v
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_shared_assets tests.test_mantra_engine tests.test_frontend_contracts tests.test_phase4d tests.test_curriculum_policy -v
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console:/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src .venv/bin/python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_hebrew_recovery tests.test_help_profiler -v

.venv/bin/ruff check packages/mpe/src/mpe/domains/hebrew packages/mpe/src/mpe/protocol/immediate_recall.py tests/test_forbidden_legacy_sources.py packages/mpe/tests/test_hebrew_domain.py packages/mpe/tests/test_help_integration.py
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/mypy packages/mpe/src/mpe/domains/hebrew packages/mpe/src/mpe/protocol/immediate_recall.py tests/test_forbidden_legacy_sources.py packages/mpe/tests/test_hebrew_domain.py packages/mpe/tests/test_help_integration.py

find data/hebtts_eval/audio -type f | wc -l
du -sh data/hebtts_eval/audio
find output/mantra_global_tts_cache -type f | wc -l
du -sh output/mantra_global_tts_cache
```
