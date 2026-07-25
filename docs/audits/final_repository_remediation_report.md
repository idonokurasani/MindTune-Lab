# Final Repository Remediation Report

**Repository:** `idonokurasani/MindTune-Lab`  
**Branch:** `feat/mantra-engine-phase1`  
**Date:** 2026-07-25  
**Scope:** Critical blockers from the final independent Phase 4D repository audit.

---

## 1. Executive summary

The final independent audit identified two critical blockers preventing production readiness:

1. **Committed Oura client secret** in `.oura_credentials` (reachable in local history).
2. **Canonical curriculum identity broken** — duplicate `verb_id`s, non-NFC Hebrew strings, non-deterministic generation, ambiguous source lookup, and an unexplained empty `italian_infinitive` field.

This session remediated both blockers in the current working tree:

- Removed the secret from the index and working tree, added `.gitignore` guards, an example placeholder, and integrity tests.
- Prepared a formal history-purge plan (not executed; requires credential rotation + owner approval).
- Rebuilt the canonical curriculum with a stable identity contract, full source provenance, Unicode NFC normalization, deterministic generation, and an explicit migration map.
- Fixed source lookup in the audit to preserve all source records for homographic infinitives.
- Cleaned legacy `mantra/generator.py` and moved diagnostic builders off hard-coded voices onto the `AudioProfile` contract.
- All 70 targeted unit tests pass; `ruff` passes for changed files; `mypy` reports only pre-existing `hebrew/` warnings.

The repository is now **not production-ready until the history purge and Oura credential rotation are completed**, but the current tree and canonical artifacts are clean and deterministic.

---

## 2. Secret containment

### What changed

- Deleted `.oura_credentials` from Git index and working tree.
- Added `.oura_credentials` to `.gitignore`.
- Created `.oura_credentials.example` with placeholder values.
- Updated `docs/project/REPOSITORY_STRUCTURE.md` to document local-only credential handling.
- Created `tests/test_repository_integrity.py` with four guards:
  - `.oura_credentials` is never tracked by Git.
  - `.gitignore` ignores `.oura_credentials`.
  - `.oura_credentials` does not exist at the repository root (only the example file may).
  - Tracked JSON files do not contain a non-placeholder `client_secret`.

### What remains

The secret is still in the Git object store and reachable from local branches `main` and `feat/mantra-engine-phase1`. A formal history purge is documented in `docs/audits/HISTORY_PURGE_PLAN.md`. The repository owner must:

1. Revoke/rotate the Oura `client_secret` in the Oura developer console.
2. Approve and execute the purge plan (preferred tool: `git-filter-repo`).
3. Force-push rewritten branches and notify all clone holders.

---

## 3. Curriculum identity root cause

The audit found 142 of 320 curriculum entries blocked. Root causes:

| Symptom | Root cause | File |
|---|---|---|
| 22 duplicate `verb_id`s | `verb_id` was set to plain infinitive (`inf_plain`), which is shared across binyanim | `scripts/generate_curriculum_320.py` |
| 123 non-NFC strings | `vocalized_inflection` from CSV was used without Unicode normalization | `scripts/generate_curriculum_320.py` |
| Non-deterministic output | `datetime.now(timezone.utc).isoformat()` embedded in `generated_at` | `scripts/generate_curriculum_320.py` |
| Audit lost source records | `source_lookup` keyed by plain infinitive, overwriting homographs | `scripts/audit_curriculum_320.py` |
| `italian_infinitive == ""` everywhere | No authoritative source exists in Phase 3 data; generator wrote empty string | `scripts/generate_curriculum_320.py` |

---

## 4. Stable identity contract

Implemented in `mantra/phase1/curriculum.py`:

- `CurriculumVerb.verb_id` is now the unique `asset_id_prefix` (Latin transliteration slug).
- Added `CurriculumVerb.source_group_key` to link each entry to a deterministic source group (`{pattern}_{table_number}_{base_form}`).
- `italian_infinitive` is now `str | None` with default `None` — explicit absence instead of unexplained empty string.
- `CurriculumVerb.from_dict` normalizes `infinitive_pointed` and `infinitive_plain` to NFC on load, and converts legacy `""` Italian to `None`.
- `Curriculum.generated_at` is `str | None` and omitted from `to_dict` when `None`, removing the timestamp source of non-determinism.

In `scripts/generate_curriculum_320.py`:

- `verb_id = unique_prefix` (same as `asset_id_prefix`).
- `infinitive_pointed` and `infinitive_plain` normalized to NFC before use.
- `source_group_key` populated.
- `italian_infinitive = None`.
- `generated_at = None`.

---

## 5. Regenerated canonical artifacts

- `data/hebrew/curriculum_v1_320.json` regenerated.
- `data/hebrew/curriculum_v1_320_audit.json` regenerated.
- `docs/audits/curriculum_v1_320_audit.md` regenerated.
- `data/hebrew/curriculum_v1_320_id_migration.json` created.
- `data/audio_profiles/hannah.json` created.

Verified:

- 320 verbs, 320 unique `verb_id`s, 320 unique `asset_id_prefix`es.
- 0 duplicate `verb_id`s, 0 duplicate `asset_id_prefix`es.
- 0 blocking audit issues.
- 11 homographic infinitives (e.g., `לפנות` PA'AL and PI'EL) are retained with distinct `verb_id`s and full source records; they no longer block asset generation.
- All `infinitive_pointed` values are Unicode NFC.
- Generation and audit are byte-for-byte deterministic across independent processes.

---

## 6. Source lookup and provenance

`scripts/audit_curriculum_320.py` was rewritten:

- Loads source records keyed by `group_key` (not plain infinitive).
- Also indexes source records by plain infinitive to preserve all matching source groups for homographs.
- `CurriculumAuditEntry` now carries `source_records` (list of all matching source records) and `source_identifier` (primary group key).
- Homographic infinitives are flagged as `homographic_infinitive` / `possible_lexical_ambiguity` but do **not** block generation.
- `italian_infinitive_status` reports `absent_authoritative_source` instead of silently accepting an empty string.
- Removed `generated_at` timestamp from audit JSON and markdown.

---

## 7. Migration map

Created `data/hebrew/curriculum_v1_320_id_migration.json`.

- 309 unique old `verb_id`s (plain infinitives).
- 11 old `verb_id`s map to two new `verb_id`s because the old `verb_id` was ambiguous across binyanim.
- Every new `verb_id` is covered by the map.
- Example mapping:
  - `לפנות` -> `["lifnot", "lefanot"]`
  - `לגלות` -> `["legalot", "liglot"]`
  - `להתחיל` -> `["lehatchil", "lehitchael"]`

Existing learner state keyed by old ambiguous IDs is not silently reassigned. Consumers that need continuity must use this map explicitly.

---

## 8. Legacy audio cleanup

- Deleted `mantra/generator.py` (dead legacy code containing stale `he-IL-HilaNeural` SSML).
- Created `data/audio_profiles/hannah.json`.
- Updated `scripts/build_lehitkasher_hannah_full_niqqud.py` to load `AudioProfile.load("hannah")` and derive voice, locale, rate, pitch, output format, and sample rate from the profile.
- Updated `scripts/build_compact_mantra_lehitkasher.py` to load `AudioProfile.load("hannah")` and use profile-derived voices via `partial(registry.ensure, ...)`.
- Updated `mantra/phase1/assets.py` `ensure_tense_markers` to accept an optional `audio_profile` and use its Hebrew voice/locale.

---

## 9. Phase 4D compatibility

- `lichtov`, `lihyot`, and `lehavot` specifications load and validate by their new `verb_id` (`lichtov`, `lihyot`, `lehavot`) because these match the `asset_id_prefix`.
- `ReadinessEvaluator`, `MantraSelectionPolicy`, and `build_execution_plan` continue to operate correctly with the new unique `verb_id`s.
- All 70 targeted unit tests pass, including `test_phase4d` vertical-slice reconciliation tests.

---

## 10. Verification

### Commands run

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest \
  tests.test_curriculum_policy \
  tests.test_phase4d \
  tests.test_shared_assets \
  tests.test_shared_assets_and_domino \
  tests.test_repository_integrity \
  tests.test_curriculum_identity \
  -v
```

**Result:** 70 tests OK.

```bash
.venv/bin/ruff check scripts/generate_curriculum_320.py scripts/audit_curriculum_320.py \
  mantra/phase1/curriculum.py mantra/phase1/assets.py \
  scripts/build_compact_mantra_lehitkasher.py scripts/build_lehitkasher_hannah_full_niqqud.py \
  tests/test_repository_integrity.py tests/test_curriculum_identity.py
```

**Result:** All checks passed.

```bash
.venv/bin/mypy --exclude 'hebrew/' <changed files>
```

**Result:** Only pre-existing `hebrew/phase3/data_loader.py` and `hebrew/phase3/selection.py` warnings.

### Determinism check

Ran `generate_curriculum_320.py` and `audit_curriculum_320.py` in a separate process and compared SHA-256 hashes:

```
ca38ab954d985c6da755d6ae3caea7ac3a2738728a88270c7b87418fedd4bf16  data/hebrew/curriculum_v1_320.json
86f6857a81bfd51bd8d9507e9e5e3e3084ee1b3747e8d7c8fd11984923037f58  data/hebrew/curriculum_v1_320_audit.json
```

Hashes matched across independent processes.

---

## 11. Remaining work

1. **History purge** — execute `docs/audits/HISTORY_PURGE_PLAN.md` after credential rotation.
2. **Oura credential rotation** — must be performed by the repository owner in the Oura console.
3. **Italian infinitive sourcing** — the 320-verb curriculum now correctly reports `absent_authoritative_source`. When an authoritative Italian gloss source is identified, the generator can populate `italian_infinitive` and the asset pipeline will generate `it.{prefix}.infinitive` assets automatically.
4. **Broad test suite** — run any additional project-level test commands (`ruff`, `mypy`, full `unittest` discovery) before final release.

---

## 12. Files changed

### Added

- `.oura_credentials.example`
- `data/audio_profiles/hannah.json`
- `data/hebrew/curriculum_v1_320_id_migration.json`
- `docs/audits/HISTORY_PURGE_PLAN.md`
- `docs/audits/final_repository_remediation_report.md`
- `tests/test_repository_integrity.py`
- `tests/test_curriculum_identity.py`

### Modified

- `.gitignore`
- `data/hebrew/curriculum_v1_320.json`
- `data/hebrew/curriculum_v1_320_audit.json`
- `docs/audits/curriculum_v1_320_audit.md`
- `docs/project/REPOSITORY_STRUCTURE.md`
- `mantra/phase1/assets.py`
- `mantra/phase1/curriculum.py`
- `scripts/audit_curriculum_320.py`
- `scripts/build_compact_mantra_lehitkasher.py`
- `scripts/build_lehitkasher_hannah_full_niqqud.py`
- `scripts/generate_curriculum_320.py`

### Removed

- `.oura_credentials`
- `mantra/generator.py`
