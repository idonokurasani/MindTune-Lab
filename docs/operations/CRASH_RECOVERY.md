# Crash Recovery

On startup, `mindtune_clm.ops.recovery.run_crash_recovery` performs:

* Marks interrupted sessions explicitly (does not resume adaptive playback).
* Releases stale locks.
* Validates event sequence integrity.
* Reports pending playback as terminated.

Manual researcher confirmation is required before continuing an interrupted session.
