# Security History Cleanup Plan — Oura Credentials

## Finding

- A live Oura `client_secret` is present in the working tree at `/Users/idonokurasani/Documents/Chatgpt/Biohacking/.oura_credentials`.
- `mindtune_console/.oura_credentials` has been tracked in Git history and was removed in commit `d22f03f` (`Remove tracked Oura credential file and add containment guards.`); the same commit exists in `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP` as `6f45e12e`.
- Because the file was once tracked, the secret bytes may exist in earlier Git commits and in any clones or forks.

## Required Immediate Actions (User Must Do)

1. **Rotate the Oura OAuth secret**
   - Log in to the Oura developer dashboard.
   - Revoke/regenerate the `client_secret` for client `9357d0ff-fa0e-4160-b15c-3e3ff08f796a`.
   - Update `.oura_credentials` (and `.oura_credentials.example` if it is a sanitized template) with the new secret.
   - Re-authenticate any devices/applications to obtain a fresh `.oura_token`.

2. **Delete the exposed working-tree file after rotation**
   - Remove `/Users/idonokurasani/Documents/Chatgpt/Biohacking/.oura_credentials` or move it to a credential manager/keyring.
   - Do not commit the new secret.

## Git History Cleanup (Separate Branch, After Rotation)

Do this on a dedicated branch, not on `CLM-01`.

### Option A — `git-filter-repo` (recommended)

```bash
# Install git-filter-repo
python3 -m pip install git-filter-repo

# Create a dedicated cleanup branch
cd /Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console
git checkout -b security/remove-oura-credential-history

# Remove .oura_credentials from the entire history
git filter-repo --path .oura_credentials --invert-paths

# Force-push to a new remote history (coordinate with all collaborators)
# git push --force-with-lease origin main
```

### Option B — BFG Repo-Cleaner

```bash
java -jar bfg.jar --delete-files .oura_credentials mindtune_console.git
cd mindtune_console.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### After History Rewrite

- Treat all clones/forks as compromised; require re-cloning.
- Confirm with:
  ```bash
  git log --all --full-history --source --name-only -- '.oura_credentials'
  ```
- Verify no `.oura_credentials` blob remains:
  ```bash
  git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | grep -E '^blob.*\.oura_credentials'
  ```

## Backup / Recovery Copies

Before archiving `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/`, `mindtune_eeg_github_recovery/`, and `mindtune_rescue/`, scan them for any `.oura_credentials` or `.oura_token` files and purge/rotate any secrets found. Treat these directories as confidential until verified.

## Notes

- History rewriting does **not** replace credential revocation. Revoke the secret first.
- Do not combine this cleanup with the `CLM-01` implementation branch to avoid mixing security-risk and feature commits.
- Update `tests/test_repository_integrity.py` to also check the Biohacking root `.oura_credentials` path, not only `mindtune_console/.oura_credentials`.
