# History Purge Plan — `.oura_credentials` secret removal

**Status:** prepared, not executed  
**Prepared:** 2026-07-25  
**Repository:** `idonokurasani/MindTune-Lab` (`feat/mantra-engine-phase1`)

---

## 1. Exposure summary

| Item | Finding |
|------|---------|
| Affected file | `.oura_credentials` (committed) |
| First introducing commit | `dc26badabdaf492d03a13ecb7765ab948a86e468` (`Baseline after MPE Phase 4C.1`) |
| Latest commit containing the file in its tree | `e1cec11cdc565917e27379d735bec8882463c0f3` |
| Current `HEAD` | `8c79cab300f090fa238a53c5d68feff12875ce93` (tree no longer contains `.oura_credentials`, but object-store history still does) |
| Reachable local branches | `refs/heads/main`, `refs/heads/feat/mantra-engine-phase1` |
| Reachable remote branches | none — `git ls-remote` shows only `refs/heads/main` at `866a5279` (`Initial commit`), which does not contain the secret commit |
| Reachable tags | none |
| Other tracked files with real credentials | none confirmed |
| Backup/log/venv copies | none found outside the Git object store |

**Conclusion:** the secret is currently reachable only in the local Git object store. A local history rewrite is sufficient to remove it from all local branches, after which the rewritten branches can be force-pushed. The repository owner must still rotate/revoke the Oura client secret in the Oura developer console — Git cleanup does not invalidate the credential.

---

## 2. Prerequisites (must be completed before any history rewrite)

1. **Credential rotation.** The repository owner must revoke or rotate the exposed Oura `client_secret` in the Oura developer console. Do not rely on Git cleanup for revocation.
2. **Full repository backup.** Clone or `rsync` the current repository to an external/secure location:
   ```bash
   cp -R /Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console /Volumes/Backup/mindtune_console-pre-purge-$(date +%Y%m%d)
   ```
3. **Warn all consumers.** Notify anyone with a clone of `MindTune-Lab` that a force-push is coming.
4. **Disable branch protection temporarily** on `main` (if enabled) so force-push can complete, or use repository-owner privileges.

---

## 3. Affected refs

```
refs/heads/main                      contains dc26bada
refs/heads/feat/mantra-engine-phase1 contains dc26bada
refs/remotes/origin/main             at 866a5279 (initial commit, does NOT contain dc26bada)
refs/tags/*                          none
```

---

## 4. Proposed purge command (preferred: git-filter-repo)

### 4.1 Install git-filter-repo

```bash
python3 -m pip install git-filter-repo
```

### 4.2 Run the purge

```bash
cd /Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console
git filter-repo \
  --path .oura_credentials \
  --invert-paths \
  --force
```

`git-filter-repo` rewrites all branches and tags automatically, removing every commit that touched `.oura_credentials`. It also updates `refs/remotes/origin/main` references stored in `.git` if any exist.

---

## 5. Alternative purge command (if git-filter-repo unavailable)

```bash
cd /Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console

git filter-branch \
  --force \
  --index-filter 'git rm --cached --ignore-unmatch .oura_credentials' \
  --prune-empty \
  --tag-name-filter cat \
  -- --all

# Remove backup refs created by filter-branch
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Note:** `git filter-branch` is deprecated, slower, and more error-prone. Prefer `git-filter-repo`.

---

## 6. Validation commands

After the purge, every one of these checks must return empty / no matches:

```bash
# 1. No commit history for the file on any ref
git log --all --full-history -- .oura_credentials

# 2. No object in the object store references the file
git rev-list --all | xargs -I{} git ls-tree -r {} --name-only | grep -F .oura_credentials || true

# 3. No blob contains the known client_secret pattern
git rev-list --all | xargs -I{} git grep -l "client_secret" {} -- || true

# 4. No reflog entry
git reflog --all | grep -i oura || true

# 5. Secret-scan helper (install if desired)
# python3 -m pip install truffleHog
# trufflehog filesystem . --only-verified
```

---

## 7. Push coordination

Because the remote `origin/main` is currently only at the initial commit and `feat/mantra-engine-phase1` is not on the remote yet, the safest push sequence is:

```bash
# Ensure the local rewrite is complete and verified
git status --short

# Push rewritten main with lease protection
git push --force-with-lease origin main

# Push the feature branch (it did not exist remotely before)
git push -u origin feat/mantra-engine-phase1
```

If `origin/main` has advanced since this plan was prepared, replace `--force-with-lease` with manual reconciliation or rebase first.

---

## 8. Tag handling

No tags contain the secret commit. If any tags are added before the purge, add `--tag-name-filter cat` to `git-filter-repo` or include tags in the validation step.

---

## 9. Branch protection

If GitHub branch protection is enabled for `main`, a force-push will be rejected. Options:
- Temporarily disable protection (repository owner).
- Use a repository-owner account with bypass privileges.
- Do not use a pull request for a history rewrite; it must be a direct force-push.

---

## 10. CI / deployment credential replacement

After the purge:
- Remove any `.oura_credentials` copy from CI secrets, deployment artifacts, or Docker images.
- Configure CI to use environment variables (`OURA_CLIENT_ID`, `OURA_CLIENT_SECRET`) or a short-lived injected file.
- Rotate CI secrets that may have been derived from the exposed credential.

---

## 11. Instructions for other clones

Every clone of the repository should be treated as potentially contaminated:

```bash
# For team members with existing clones
git fetch origin
git checkout main
git reset --hard origin/main

# Or, safest, delete and re-clone
rm -rf /path/to/mindtune_console
git clone https://github.com/idonokurasani/MindTune-Lab.git /path/to/mindtune_console
```

---

## 12. Final secret scan

Run one of:

```bash
# Basic grep across the object store (after purge)
git rev-list --all | xargs -I{} git grep -l "client_secret" {} --

# Or use a secret scanner
python3 -m pip install truffleHog
trufflehog git file:///Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console --only-verified
```

---

## 13. Rollback / abort

If anything fails before push:
- Do **not** force-push.
- Restore from the backup created in §2.
- Re-run the purge from a fresh copy.

---

**This plan must not be executed until the repository owner confirms credential rotation and approves the force-push.**
