"""Deterministic audio digest helpers for CLM-03."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Deterministic JSON suitable for digest computation."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def audio_digest(
    source_asset_checksums: list[str],
    plan_dict: dict[str, Any],
    rendered_pcm_bytes: bytes,
    control_state: dict[str, Any],
    decision_id: str,
    actuation_receipt_id: str,
    render_cycle_id: str,
    audio_config: dict[str, Any],
    planner_version: str,
    renderer_version: str,
) -> str:
    """Compute a canonical digest over the complete rendered audio context."""
    payload = {
        "source_asset_checksums": sorted(source_asset_checksums),
        "plan": plan_dict,
        "pcm_checksum": hashlib.sha256(rendered_pcm_bytes).hexdigest(),
        "control_state": control_state,
        "decision_id": decision_id,
        "actuation_receipt_id": actuation_receipt_id,
        "render_cycle_id": render_cycle_id,
        "audio_config": audio_config,
        "planner_version": planner_version,
        "renderer_version": renderer_version,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
