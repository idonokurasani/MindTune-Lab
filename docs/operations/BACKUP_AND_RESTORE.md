# Backup and Restore

## Backup

```bash
curl -X POST http://127.0.0.1:8005/api/v1/ops/backups -H "Authorization: Bearer $TOKEN"
```

Backups are stored in `data/backups/` as `tar.gz` with a checksum manifest. Cache and secrets are excluded by default.

## Restore

```bash
curl -X POST http://127.0.0.1:8005/api/v1/ops/restores/validate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"archive": "clm09-<id>.tar.gz"}'
```

Use `mindtune_clm.ops.restore.restore_backup(archive, target, dry_run=True)` for dry-run.
