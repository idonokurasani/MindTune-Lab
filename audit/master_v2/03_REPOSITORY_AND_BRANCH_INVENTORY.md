# 03 — Repository and Branch Inventory

## Directories Under `/Users/idonokurasani/Documents/Chatgpt/Biohacking`

32 top-level directories (excluding files):

```
B2_4_64a79f1_regate_artifacts/
FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/
MindTune Lab.app/
athena_mac_wrappers/
brainlab_protocols/
data/
devin_handoff_citizen_b2_3/
devin_handoffs/
docs/
exports/
firmware_analysis/
forensic_audit_20260618_025114/
mindtune-learning-framework/
mindtune_archives/
mindtune_capture/
mindtune_console/
mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/
mindtune_diagnostics/
mindtune_eeg_github_recovery/
mindtune_lab/
mindtune_native/
mindtune_reports/
mindtune_rescue/
pi_mnt/
remote_scripts/
scripts/
systemd/
tests/
tmp/
tools/
vendor_reverse_work/
wordpress/
```

## Git Repositories

| Repository | Path | Current Branch | HEAD | Dirty | Stashes | Worktrees | Disposition |
|---|---|---|---|---|---|---|---|
| mindtune_console | `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console` | `feat/mindtune-lab-foundation` | `23ef2bb` | `?? audit/` | none | self `23ef2bb [feat/mindtune-lab-foundation]`; `/Users/.../mindtune_eeg_github_recovery f7c8784 [recovery/eeg-focuscalm-mantra-20260725]`; `/Users/.../mindtune_rescue 8af3b95 [rescue/eeg-engine]` | KEEP (canonical) |
| mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP | `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP` | `feat/mantra-engine-phase1` | `a6701d97` | clean | none | self `a6701d97 [feat/mantra-engine-phase1]` | ARCHIVE |
| mindtune_eeg_github_recovery | `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_eeg_github_recovery` | n/a (worktree checkout, no `.git` dir here) | `f7c8784` | — | — | registered as worktree of `mindtune_console` | ARCHIVE |
| mindtune_rescue | `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_rescue` | n/a (worktree checkout, no `.git` dir here) | `8af3b95` | — | — | registered as worktree of `mindtune_console` | ARCHIVE |

Note: `mindtune-learning-framework/`, `mindtune_capture/`, `mindtune_lab/`, `mindtune_native/`, `mindtune_diagnostics/`, and `mindtune_reports/` contain `.gitignore` files but no `.git` directory; they are not Git repositories in this working tree.

## Recent Commits (`mindtune_console`)

```
23ef2bb Remove Citizen Cafe and Streetwise Hebrew; integrate HeLP as canonical Hebrew source
9ceb7b1 Implement Hebrew immediate-recall domain adapter (Phase 4D)
cbc8989 Implement deterministic cognitive closed loop
4127b4c Exclude local environments and generated model artifacts
55b3882 Remove invalid lehavot specification alias
```

## Recent Commits (`mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP`)

```
a6701d97 Remove invalid lehavot specification alias
6aff9f07 Clean up stale documentation and ruff config.
8c79cab3 Fix canonical curriculum identity, source provenance, and legacy audio.
6f45e12e Remove tracked Oura credential file and add containment guards.
e1cec11c Complete Phase 4D vertical slice and MPE shared-layer extraction.
```

## Important Untracked / Generated Directories

- `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/audit/` — created by this audit (untracked).
- `/Users/idonokurasani/Documents/Chatgpt/Biohacking/.pnpm-store/` — Node package cache; discard.
- `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/.venv/`, `.venv_hebtts/`, `.venv_phonikud/` — virtual environments.
- `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_archives/` and `/Users/idonokurasani/Documents/Chatgpt/Biohacking/tmp/` — app bundle archives.

## Inaccessible / Missing Expected Components

- `.raspberry_bridge/` and `pi_mnt/` are referenced by `server.py` but the bridge directory is absent; `pi_mnt/` is empty.
- `/mnt/biohacking/sqlite/health_data.db` (authoritative per `BIOHACKING_MASTERPLAN.md`) is outside the inspected working tree and could not be located.
- Some `.venv*` directories may be symlinked or contain architecture-specific wheels not inspected.
