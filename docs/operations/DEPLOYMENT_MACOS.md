# macOS Deployment

1. Install Python 3.11+ and Node.js.
2. Create `.venv` and install packages.
3. Configure via `CLM09_*` environment or `config/clm09.json`.
4. Load `deploy/launchd/com.mindtune.clm.plist` or run from the console.
5. Verify `/api/v1/health/ready`.
6. Run a replay session.
7. Create a backup and diagnostics bundle.
