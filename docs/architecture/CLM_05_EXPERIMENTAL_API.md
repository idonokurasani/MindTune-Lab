# CLM-05 Experimental API and Control Plane

## Scope

CLM-05 exposes the existing closed-loop mantra (CLM) and MindTune Protocol Engine (MPE) building blocks as an experimental HTTP control plane. It is intentionally thin: all core engines (event stores, live-loop orchestrator, sensor gateway, audio renderer, and voice cache) are reused from earlier CLM modules rather than duplicated.

## Reused Modules

| Capability | Reused Component |
|------------|------------------|
| Event persistence | `mpe.event_store.InMemoryEventStore`, `mpe.persistence.store.SQLiteEventStore` |
| Live closed-loop orchestration | `mindtune_clm.live_loop.orchestrator.LiveClosedLoopOrchestrator` with `LiveClosedLoopState` and `SafetyController` |
| Sensor abstraction | `mindtune_clm.live.gateway.LiveSensorGateway` plus `SyntheticLiveSource` and `FC11LiveSource` |
| Voice cache | `mindtune_clm.voice.cache.VoiceCache` and `mindtune_clm.voice.models.ValidatedHebrewPedagogicalItem` |
| Audio assets | `mindtune_clm.audio.assets`, `AudioProfile` routing, `AudioAssetRegistry` |
| Audio rendering | `mindtune_clm.audio.renderer` with `PlaybackScheduler` and `PlaybackReceipt` |
| Schemas | MPE `Runtime` / `Event` / `EventType` |

## API Contract

Base path: `/api/v1/`

### Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service health and readiness summary |
| GET | `/api/v1/health/live` | Liveness probe |
| GET/POST | `/api/v1/experiments` | Experiment registration and listing |
| GET | `/api/v1/experiments/{id}` | Fetch experiment |
| DELETE | `/api/v1/experiments/{id}` | Delete experiment |
| GET | `/api/v1/protocols` | Supported protocol versions |
| GET | `/api/v1/protocols/{id}` | Protocol detail |
| POST | `/api/v1/sessions` | Create a session |
| GET | `/api/v1/sessions` | List sessions |
| GET/DELETE | `/api/v1/sessions/{id}` | Get or delete session |
| GET | `/api/v1/sessions/{id}/readiness` | Readiness report |
| POST | `/api/v1/sessions/{id}/control` | Control command (`prepare`, `start`, `step`, `pause`, `resume`, `stop`, `kill`) |
| GET | `/api/v1/sessions/{id}/events` | Paginated events |
| GET | `/api/v1/sessions/{id}/events/stream` | SSE event stream with heartbeat |
| GET | `/api/v1/sessions/{id}/export/events` | Export session events (JSON/JSONL) |
| GET | `/api/v1/sessions/{id}/export/summary` | Export summary |
| GET | `/api/v1/sessions/{id}/export/manifest` | Export manifest |
| POST | `/api/v1/sessions/{id}/exports` | Request export bundle |
| POST/GET | `/api/v1/sensors` | Register and list sensors |
| POST | `/api/v1/sensors/{id}/connect` | Connect sensor |
| POST | `/api/v1/sensors/{id}/disconnect` | Disconnect sensor |
| GET | `/api/v1/stimuli` | List stimuli for a session |
| GET | `/api/v1/stimuli/{id}` | Get stimulus detail |

### Pydantic Models

Request and response bodies are defined in `packages/clm/src/mindtune_clm/api/models.py` using Pydantic v2. Key models include `SessionCreate`, `SessionResponse`, `ControlCommand`, `ControlResponse`, `SensorRegister`, `SensorResponse`, `EventList`, `ExportRequest`, `ExportResponse`, and `ErrorResponse`.

### Typed Errors

`packages/clm/src/mindtune_clm/api/errors.py` defines a uniform `CLM05APIError` with fields:

- `code` — stable machine-readable error code
- `message` — human-readable description
- `request_id` — request correlation id
- `resource_id` — affected resource, if any
- `retryable` — whether the client may retry
- `details` — safe, non-sensitive additional context

An exception handler in `app.py` serializes these as JSON with the appropriate HTTP status.

### Idempotency

All mutating routes accept an optional `idempotency_key`. The `CLM05Service` stores the first successful response under `(key, request payload)` and replays it on identical subsequent requests. A repeated key with a changed payload returns `idempotency_conflict` (422).

## Session State Machine

```
created → prepared → ready → starting → running
                         ↓       ↓        ↓
                       completed aborted failed
```

`prepare` builds the orchestrator, creates synthetic frames, and acquires the `playback_backend` lock. It lands in `ready` if all readiness conditions pass, otherwise `prepared` with blocking reasons. `start` connects the sensor source and transitions to `running`. `step` advances one frame. `pause`/`resume` toggle `paused` and `running`. `stop` completes the session and releases locks. `kill` aborts immediately and releases locks.

## Readiness Report

`GET /api/v1/sessions/{id}/readiness` returns:

```json
{
  "ready": true,
  "blocking_reasons": [],
  "warnings": []
}
```

Blocking reasons include `missing_aaron_asset`, `voice_cache_unavailable`, and `orchestrator_not_prepared`. Warnings include `sensor_not_connected` and `baseline_forced`.

## Security

- Loopback requests (`127.0.0.1`, `::1`, `localhost`) are allowed without a token by default.
- Optional static bearer token via `CLM05_API_TOKEN`.
- Constant-time token comparison with `hmac.compare_digest`.
- All mutation routes enforce the token when configured.
- Request size limit middleware (default 1 MB).
- CORS configured without wildcards; allowed origins must be explicitly listed.

## Resource Locks

The `CLM05Service` maintains exclusive per-resource locks for `playback_backend` and `fc11_source`. A session must release its owned locks on `stop`, `kill`, or `delete` so another session can `prepare`.

## Event Streaming and Pagination

Paginated events return `EventList` with `page`, `page_size`, `total`, and `items`. The SSE endpoint emits newline-delimited server-sent events with a periodic `:heartbeat` comment and respects `last_event_id` so reconnects resume without replaying already-delivered events.

## Exports and Privacy

Event exports are available as JSON or JSONL. Exports are redacted: participant ids, tokens, API keys, MAC addresses, absolute paths, and IP-looking strings are replaced with `[REDACTED]` or `[REDACTED_PATH]`. Manifest and summary exports include per-field checksums and a `redacted` flag.

## Launch

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/clm/src:/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console/packages/mpe/src .venv/bin/python scripts/run_clm05_api.py --help
```

Optional environment variables:

- `CLM05_API_STORE` — SQLite file path or parent directory
- `CLM05_API_TOKEN` — static bearer token
- `CLM05_API_HOST` / `CLM05_API_PORT` — bind address (defaults `127.0.0.1:8005`)
- `CLM05_API_MAX_REQUEST_BYTES` — max request body bytes (default `1_000_000`)

## Tests

The acceptance suite `packages/clm/tests/test_clm05.py` exercises the scenarios required for CLM-05:

- deterministic step idempotency (replay behavior)
- synthetic live session reaching `live_closed_loop_intervention_outcome`
- readiness failure when the Aaron asset is missing
- sensor disconnect forcing baseline lock
- kill through the API
- idempotency conflict detection
- SSE reconnect skipping prior events
- mutation authorization and request-size limits
- export redaction and manifest generation

## Files

- `packages/clm/src/mindtune_clm/api/__init__.py` — package public API
- `packages/clm/src/mindtune_clm/api/app.py` — FastAPI application factory and lifespan
- `packages/clm/src/mindtune_clm/api/config.py` — runtime configuration
- `packages/clm/src/mindtune_clm/api/dependencies.py` — FastAPI dependency provider
- `packages/clm/src/mindtune_clm/api/models.py` — Pydantic request/response models
- `packages/clm/src/mindtune_clm/api/errors.py` — typed errors and exception handler
- `packages/clm/src/mindtune_clm/api/commands.py` — control command enum
- `packages/clm/src/mindtune_clm/api/services.py` — `CLM05Service` with session lifecycle, events, exports, and locks
- `packages/clm/src/mindtune_clm/api/security.py` — auth, request size limit, CORS constants
- `packages/clm/src/mindtune_clm/api/health.py` — health routes
- `packages/clm/src/mindtune_clm/api/experiments.py` — experiment routes
- `packages/clm/src/mindtune_clm/api/protocols.py` — protocol routes
- `packages/clm/src/mindtune_clm/api/sessions.py` — session routes
- `packages/clm/src/mindtune_clm/api/sensors.py` — sensor routes
- `packages/clm/src/mindtune_clm/api/stimuli.py` — stimulus discovery routes
- `packages/clm/src/mindtune_clm/api/control.py` — control routes
- `packages/clm/src/mindtune_clm/api/events.py` — event pagination and SSE
- `packages/clm/src/mindtune_clm/api/exports.py` — export routes
- `packages/clm/src/mindtune_clm/api/fixture_clm05.py` — `TestClient` fixture for tests
- `packages/clm/tests/test_clm05.py` — acceptance test suite
- `scripts/run_clm05_api.py` — manual API launch script
- `docs/architecture/CLM_05_EXPERIMENTAL_API.md` — this document
