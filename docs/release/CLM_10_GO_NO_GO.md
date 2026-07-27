# CLM-10 Go / No-Go Framework

## Final decision: `CONDITIONAL_GO`

The release candidate is accepted for bounded research use under the limitations documented in `CLM_10_KNOWN_LIMITATIONS.md`. It is not approved for unrestricted production deployment or clinical use.

## Gate evaluation

| Gate | Criteria | Evidence | Pass / Fail / Conditional | Limitations | Required follow-up | Owner | Blocking |
|---|---|---|---|---|---|---|---|
| A — Build reproducibility | Exact branch, base SHA, clean or approved tree, deterministic manifest | `scripts/build_release_candidate.py`, `RELEASE_MANIFEST.json` | Conditional | Tree may be dirty during local dev build; build tool allows explicit `--allow-dirty` | Final manifest must be produced from a committed SHA | Release engineer | No |
| B — Application visibility | Research Console launches; all primary pages render; API responds | `npm run test`, `npm run build`, `python scripts/run_mindtune_demo.py` | Conditional | Real browser opening depends on desktop environment | Capture final screenshots from production build | Frontend lead | No |
| C — Closed-loop correctness | Replay and synthetic-live pipelines deterministic; safety controls work | `packages/clm/tests/test_clm04*.py`, `test_clm05.py` | Conditional | Real FC11 not run | Run FC11 field validation when hardware available | CLM engineer | No |
| D — Hebrew learning correctness | Curriculum pinned, Aaron/Giuseppe routing exact, no linguistic edits in UI | `packages/clm/tests/test_clm06*.py`, `test_curriculum_policy.py` | Pass | Full browser workflow not re-recorded | End-to-end browser smoke in production build | Hebrew lead | No |
| E — Calibration integrity | Config checksum deterministic, raw observations preserved, invalid profiles rejected | `packages/clm/tests/test_clm07.py` | Pass | None | — | Calibration lead | No |
| F — Scientific reproducibility | Preregistered plan immutable, repeated analyses identical | `packages/clm/tests/test_clm08.py` | Pass | Synthetic data only | Human study IRB and data collection | Science lead | No |
| G — Safety | Kill clears pending audio, no auto-resume, no stale sensor escalation | `packages/clm/tests/test_clm05.py`, `test_clm09.py` | Pass | Real audio kill not exercised | Live audio safety smoke | Safety reviewer | No |
| H — Operational recovery | Backup, restore, shutdown, crash recovery produce consistent state | `packages/clm/tests/test_clm09.py` | Pass | Restore endpoints disabled by default | Document enable-restore procedure | Ops lead | No |
| I — Privacy and secrets | No credentials committed, token redaction, no real identities in exports | `.gitignore`, secret scanning, `tests/test_clm05.py` | Pass | Secret scanning is pattern-based | Periodic audit | Security lead | No |
| J — Field validation | Real FC11 and local playback validated | Not available | Fail | Hardware unavailable; audio playback not exercised in CI | Acquire FC11 hardware and run bounded field validation | Field lead | Yes, resolved by conditional scope |

## Rationale

All code-level gates (A–I) pass or pass with documented, non-blocking limitations. Gate J (field validation) is intentionally scoped out of this release because FC11 hardware is not available. The release is therefore `CONDITIONAL_GO` for bounded research use, with the explicit condition that no clinical, multi-user, or real-hardware claims are made until Gate J is satisfied and a follow-up release candidate is produced.
