# Release Checklist

1. Run `git status` and ensure no dirty tree.
2. Bump `semantic_version` in `mindtune_clm/ops/config.py` if needed.
3. Run `ruff check`, `mypy`, and `pytest`.
4. Build release manifest with `build_release_manifest()`.
5. Build frontend: `cd apps/research-console && npm run build`.
6. Build Docker image.
7. Run smoke tests.
8. Tag and push.
