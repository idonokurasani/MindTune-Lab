# Troubleshooting

| Symptom | Check | Action |
|---|---|---|
| Startup blocked | `mindtune_clm.ops.startup.run_startup` blocker | Review config and storage permissions |
| Readiness false | `/api/v1/health/ready` blockers | Resolve migration, event-store, or storage issues |
| Event corruption | `data/events/.corruption_detected` | Diagnose and restore from backup |
| High memory | `resource_limits` config | Lower active session limits |
| Backup fails | `data/backups` permissions | Ensure writable and not full |
