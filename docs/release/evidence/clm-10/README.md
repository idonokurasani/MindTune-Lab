# CLM-10 Evidence Bundle Index

This directory contains the indexed evidence for the CLM-10 release candidate. Large runtime artifacts (raw recordings, paid audio, container images) are excluded and referenced by manifest path only.

## Structure

- `README.md` — this index
- `tests/` — aggregated test result summaries
- `replay-qualification/` — deterministic replay manifests and checksums
- `synthetic-live/` — synthetic-live scenario results
- `hardware/` — real FC11 validation status (blocked_by_hardware)
- `audio/` — local playback validation status (not_tested in CI)
- `hebrew/` — Hebrew adaptive session evidence
- `calibration/` — calibration qualification evidence
- `scientific-validation/` — synthetic preregistered study evidence
- `faults/` — fault-injection campaign summaries
- `safety/` — safety qualification evidence
- `performance/` — bounded load and latency results
- `soak/` — long-run soak results (CI-short mode)
- `backup-restore/` — backup, shutdown, restart, restore checksums
- `security/` — security check results
- `screenshots/` — Research Console screenshots (excluded from repository if they contain desktop content)

## Generation

Run `python scripts/build_release_candidate.py` to regenerate the release bundle and evidence summaries.

## Release identity

- Version: `0.10.0-rc.1`
- Branch: `feat/clm-10-release-candidate-field-validation`
- Base: `220b3de11b8b09eadd282805e33d1b4bf44be0b9`
