# 17 — Security, Privacy, and Secrets Audit

## 1. CRITICAL: Oura Credentials in Working Tree

- **File:** `/Users/idonokurasani/Documents/Chatgpt/Biohacking/.oura_credentials`
- **Status:** Contains a live Oura `client_secret` (value redacted in this report).
- **Evidence:** File is present and not ignored at the Biohacking root; `test_repository_integrity.py` in `mindtune_console/tests/` checks the `mindtune_console/.oura_credentials` path, not the root file.
- **Remediation:** Rotate the secret immediately via the Oura developer dashboard. `.oura_credentials` was tracked in `mindtune_console` Git history and removed in commit `d22f03f`; therefore the secret may exist in earlier commits. Execute the dedicated history cleanup plan in `audit/master_v2/SECURITY_HISTORY_CLEANUP_PLAN.md` on a separate branch after rotation. History rewriting does not replace credential revocation.

## 2. SpeechGen Credentials

- Required environment variables: `SPEECHGEN_API_KEY`, `SPEECHGEN_EMAIL`.
- Used by `mantra/phase1/tts.py` and build scripts.
- Not present in tracked source files; correct pattern.

## 3. Azure Speech

- `azure_speech.py` is marked legacy/forbidden.
- `test_forbidden_legacy_sources.py` guards against reintroduction.
- `MINDTUNE_AZURE_SPEECH_KEY` etc. are no longer active.

## 4. Oura Token Storage

- `.oura_token` stores access/refresh tokens in plaintext JSON.
- No encryption at rest.

## 5. EEG / Behavioral Data Privacy

- Raw EEG CSV and `observation_received` payloads with raw audio are sensitive.
- `PERSISTENCE_BOUNDARIES.md` requires encryption at rest for raw audio/EEG and voice samples.
- Current implementation does not show explicit encryption.

## 6. Findings Summary

| Risk | Severity | Location | Recommendation |
|---|---|---|---|
| Live Oura secret in working tree and Git history | CRITICAL | `/Users/.../Biohacking/.oura_credentials`; `mindtune_console/.oura_credentials` tracked then removed in `d22f03f` | Revoke secret first, then run `SECURITY_HISTORY_CLEANUP_PLAN.md` on a dedicated branch |
| Plaintext Oura tokens | HIGH | `.oura_token` | Encrypt at rest |
| No EEG/audio encryption | MEDIUM | `mindtune_capture/`, `mpe/` | Implement at-rest encryption for sensitive payloads |
| Legacy Azure code | LOW | `azure_speech.py` references | Ensure forbidden tests remain active |

## 7. Disposition

- Security policies → **REWRITE** for V2 (keyring/env-only, encrypted data at rest).
- `test_repository_integrity.py` → **MIGRATE** and expand to cover all credential locations.
