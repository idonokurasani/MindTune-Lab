# Configuration

CLM-09 uses `CLM09Config` loaded from defaults, a JSON config file, environment variables, and CLI arguments.

## Precedence

1. Defaults
2. Config file
3. Environment variables (`CLM09_*`)
4. CLI arguments
5. Explicit overrides

## Sections

* `api`
* `research_console`
* `storage`
* `event_store`
* `sensor_access`
* `playback`
* `voice_cache`
* `calibration`
* `scientific_validation`
* `logging`
* `metrics`
* `security`
* `resource_limits`
* `shutdown`
* `backup`
* `deployment_mode`

## Example

```json
{
  "release_id": "clm09-local",
  "deployment_mode": "research_local",
  "api": {
    "host": "127.0.0.1",
    "port": 8005,
    "bearer_token": "FROM_ENV_ONLY"
  },
  "storage": {
    "root": "data"
  }
}
```

## Secrets

Secrets must be provided by environment variables or external files. Never commit secrets.
