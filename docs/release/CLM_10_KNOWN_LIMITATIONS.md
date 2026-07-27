# CLM-10 Known Limitations

This document records the actual limitations identified during the CLM-10 release-candidate qualification.

## Architectural

- No production multi-user authorization or RBAC layer.
- No cloud deployment qualification; only macOS development and local container paths are exercised.
- Research Console is a single-page Vite application served from localhost.

## Scientific

- All scientific-study evidence is synthetic; no human-participant or clinical data were collected.
- No long-term retention or real-world efficacy evidence exists.
- Effect estimates are derived from deterministic fixtures.

## Hardware

- Real FC11 EEG hardware is not available in this environment; live FC11 validation is `blocked_by_hardware`.
- Raspberry Pi 5 BLE/field bridge is not physically tested.

## Sensor

- Replay and synthetic-live FC11 data paths are validated; real packet timing is not.

## Language-domain

- Hebrew curriculum is bounded to the 320-verb canonical set plus approved CLM-06B items.
- Pointed-text policy is preserved; UI does not permit editing linguistic truth.

## Audio

- Real local speaker playback is not exercised in CI; no-speaker deterministic mode is validated.
- New SpeechGen synthesis is not triggered in the fast loop; only pre-approved cached assets are used.

## Deployment

- Container image build is defined in `Dockerfile` but not built or run in this CI pass.
- Docker Compose stack is declared but not smoke-tested in this run.

## Performance

- No multi-hour soak test was executed in CI; the soak harness is present but runs in CI-short mode.
- Bounded load tests are run against synthetic fixtures only.

## Security

- Bearer token enforcement is present but not penetration tested.
- Restore and shutdown endpoints are disabled by default.
- Path-traversal and request-size checks are implemented and unit tested.

## Usability

- Researcher workflow review is desk-based only; no external user study was run.
- Some readiness messages are API-derived and assume familiarity with the protocol.

## Untested configurations

- Windows host, Linux bare-metal, and ARM container runtimes are untested.
- Real Oura API integration was not exercised; sample data only.
- Voice-cache eviction under disk pressure is not tested.
