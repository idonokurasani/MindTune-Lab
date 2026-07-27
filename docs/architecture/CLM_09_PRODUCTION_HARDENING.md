# CLM-09 Production Hardening Architecture

## Overview

CLM-09 adds operational reliability, deployment, and recoverability to MindTune Lab without changing scientific behavior. The operational package `mindtune_clm.ops` provides configuration, release manifests, startup/shutdown, readiness/liveness, logging, metrics, resource limits, migrations, backup/restore, crash recovery, and diagnostics.

## Operational chain

```mermaid
graph LR
    A[Versioned release] --> B[Validated configuration]
    B --> C[Environment checks]
    C --> D[Startup phases]
    D --> E[Readiness/liveness]
    E --> F[Session operation]
    F --> G[Structured logs & metrics]
    G --> H[Bounded resources]
    H --> I[Fault detection]
    I --> J[Degradation/recovery]
    J --> K[Immutable audit]
    K --> L[Safe shutdown]
    L --> M[Backup/restore]
```

## Startup phases

```mermaid
graph LR
    P1[process_created] --> P2[configuration_loaded]
    P2 --> P3[configuration_validated]
    P3 --> P4[storage_checked]
    P4 --> P5[migrations_checked]
    P5 --> P6[event_store_checked]
    P6 --> P7[assets_checked]
    P7 --> P8[sensor_drivers_checked]
    P8 --> P9[playback_checked]
    P9 --> P10[API_ready]
    P10 --> P11[application_ready]
```

## Readiness dependencies

Readiness checks storage, migrations, event-store, assets, playback, sensors, and locks.

## Storage layout

```
data/
├── events/
├── sessions/
├── profiles/
├── studies/
├── exports/
├── cache/
├── logs/
├── backups/
└── tmp/
```

## Backup and restore

Backups are `tar.gz` archives with a JSON manifest containing checksums. Restore supports dry-run and release/schema compatibility checks.

## Crash recovery

Recovery marks interrupted sessions, terminates pending playback state, releases stale locks, and validates event sequence integrity without auto-resuming adaptive playback.

## Graceful shutdown

Shutdown phases are bounded by a timeout and executed in order: stop mutations, sessions, adaptive loops, playback, sensor disconnect, event flush, exports, lock release, storage close, receipt.

## Container deployment

The CLM container image is multi-stage, non-root, has no secrets, and mounts a persistent data volume. See `deploy/docker/Dockerfile.clm` and `deploy/compose/docker-compose.yml`.

## macOS / launchd

`deploy/launchd/com.mindtune.clm.plist` provides user-level launchd support with environment file and log paths.

## Raspberry Pi / systemd

`deploy/systemd/mindtune-clm.service` and `deploy/raspberry-pi/setup.sh` document headless service setup.

## Limitations

* Real FC11 BLE and audio playback remain host-dependent.
* Raspberry Pi hardware compatibility has not been manually verified.
* Prometheus output is optional; a local metrics endpoint is provided.
