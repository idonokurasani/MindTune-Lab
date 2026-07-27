# Security

* Loopback-only default (`host: 127.0.0.1`).
* No wildcard CORS.
* Request-size limits via `api.max_request_bytes`.
* Bearer tokens redacted in logs and config output.
* Secret files checked for group/other readability.
* Operational endpoints disabled by default.
* Restore and shutdown endpoints require explicit enablement.
* No shell interpolation for subprocess or paths.
