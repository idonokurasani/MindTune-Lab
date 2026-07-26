"""Provider receipt helpers for CLM-03B."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from mindtune_clm.voice.models import ProviderReceipt, SpeechGenRequest


def build_provider_receipt(
    request: SpeechGenRequest,
    provider_audio_bytes: bytes,
    canonical_audio_checksum: str,
    sample_rate: int,
    frame_count: int,
    duration: float,
    response_status: int = 200,
    provider_response: dict[str, Any] | None = None,
) -> ProviderReceipt:
    """Build a redacted ProviderReceipt without credentials."""
    return ProviderReceipt(
        receipt_id=f"pfr-{request.request_checksum[:16]}",
        provider=request.provider,
        provider_voice_id=request.provider_voice_id,
        locale=request.locale,
        synthesis_text=request.synthesis_text,
        provider_audio_checksum=hashlib.sha256(provider_audio_bytes).hexdigest(),
        canonical_audio_checksum=canonical_audio_checksum,
        sample_rate=sample_rate,
        frame_count=frame_count,
        duration=duration,
        cache_key=request.cache_key,
        response_status=response_status,
        timestamp=time.time(),
        provider_response=provider_response or {},
    )
