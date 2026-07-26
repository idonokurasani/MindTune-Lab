"""SpeechGen provider client for CLM-03B Giuseppe/Aaron."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from typing import Any, Protocol

from mindtune_clm.voice.cache import VoiceCache
from mindtune_clm.voice.canonicalize import canonicalize_pcm
from mindtune_clm.voice.events import CLM03BEventType
from mindtune_clm.voice.models import (
    PedagogicalVoiceRequest,
    SpeechGenRequest,
    SynthesisParameters,
    VoiceAsset,
)
from mindtune_clm.voice.receipts import build_provider_receipt
from mindtune_clm.voice.routing import (
    VoiceRoute,
    build_speechgen_request_text,
    cache_key,
    default_synthesis_parameters,
    request_checksum,
    route,
)

HTTPResponse = tuple[int, str, bytes]


class HTTPTransport(Protocol):
    """Injectable HTTP transport for tests and live calls."""

    def __call__(
        self,
        method: str,
        url: str,
        data: bytes | None,
        headers: dict[str, str],
        timeout: int,
    ) -> HTTPResponse:
        ...


def default_http_transport(
    method: str,
    url: str,
    data: bytes | None,
    headers: dict[str, str],
    timeout: int,
) -> HTTPResponse:
    """Default urllib-based HTTP transport."""
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:2000]
        raise SpeechGenNetworkError(
            f"SpeechGen HTTP {exc.code} at {url}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SpeechGenNetworkError(f"SpeechGen request to {url} failed: {exc.reason}") from exc


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the SpeechGen payload with credentials removed."""
    return {k: v for k, v in payload.items() if k not in {"token", "email"}}


def _wav_info_from_bytes(data: bytes) -> tuple[int, float]:
    """Return (sample_rate, duration) from WAV bytes."""
    import io
    import wave
    with wave.open(io.BytesIO(data), "rb") as handle:
        n_frames = handle.getnframes()
        rate = handle.getframerate()
        return rate, n_frames / rate


class SpeechGenClient:
    """SpeechGen TTS client with content-addressed cache and injectable transport."""

    provider_client_version = "1.0.0"

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        transport: HTTPTransport | None = None,
        api_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("SPEECHGEN_API_KEY") or os.environ.get("SPEECHGEN_TOKEN")
        self.email = email or os.environ.get("SPEECHGEN_EMAIL")
        self.transport = transport or default_http_transport
        self.api_url = api_url or os.environ.get(
            "SPEECHGEN_API_URL",
            "https://speechgen.io/index.php?r=api/text",
        )

    def _require_credentials(self) -> None:
        if not self.api_key:
            raise SpeechGenAuthError("SPEECHGEN_API_KEY is missing")
        if not self.email:
            raise SpeechGenAuthError("SPEGEN_EMAIL is missing")

    def synthesize(
        self,
        request: PedagogicalVoiceRequest,
        cache: VoiceCache,
        runtime: Any | None = None,
        parameters: SynthesisParameters | None = None,
    ) -> VoiceAsset:
        """Return a VoiceAsset for request, using cache when valid.

        Accepts either a raw ``PedagogicalVoiceRequest`` or a validated Hebrew
        item.  Validated items are routed through ``validated_hebrew`` and
        carry their morphology/HeLP provenance into the produced asset.
        """
        if isinstance(request, PedagogicalVoiceRequest):
            validated_item: Any | None = None
        else:
            validated_item = request
            voice_request = validated_item.to_voice_request()
            request = voice_request
        selected_route: VoiceRoute = route(request)  # noqa: F841
        params = parameters or default_synthesis_parameters()
        tts_text = build_speechgen_request_text(request, selected_route)

        linguistic_identity_checksum = (
            validated_item.validation_checksum if validated_item else None
        )
        key = cache_key(
            selected_route,
            tts_text,
            params,
            linguistic_identity_checksum=linguistic_identity_checksum,
        )
        checksum = request_checksum(
            selected_route,
            tts_text,
            params,
            linguistic_identity_checksum=linguistic_identity_checksum,
        )

        sg_request = SpeechGenRequest(
            provider=selected_route.provider,
            provider_voice_id=selected_route.provider_voice_id,
            locale=selected_route.locale,
            synthesis_text=tts_text,
            output_format=params.format,
            parameters=params,
            request_checksum=checksum,
            cache_key=key,
            timeout_seconds=120,
            max_retries=3,
            provider_client_version=self.provider_client_version,
        )
        asdict(sg_request)

        if runtime is not None:
            runtime.emit(
                CLM03BEventType.PEDAGOGICAL_VOICE_REQUEST_CREATED,
                {
                    "request_id": request.request_id,
                    "language": request.language,
                    "locale": request.locale,
                    "voice": selected_route.provider_voice_id,
                    "source_text_checksum": request.source_text_checksum,
                    "tts_text_checksum": request.tts_text_checksum,
                },
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )
            runtime.emit(
                CLM03BEventType.VOICE_ROUTE_SELECTED,
                {
                    "request_id": request.request_id,
                    "provider": selected_route.provider,
                    "voice": selected_route.provider_voice_id,
                    "locale": selected_route.locale,
                },
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )
            runtime.emit(
                CLM03BEventType.SPEECHGEN_REQUEST_CREATED,
                {
                    "request_id": request.request_id,
                    "cache_key": key,
                    "provider": selected_route.provider,
                    "voice": selected_route.provider_voice_id,
                    "locale": selected_route.locale,
                    "tts_text_checksum": request.tts_text_checksum,
                },
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )

        cached = cache.get(key)
        if cached is not None:
            if runtime is not None:
                runtime.emit(
                    CLM03BEventType.SPEECHGEN_CACHE_HIT,
                    {
                        "request_id": request.request_id,
                        "cache_key": key,
                        "asset_id": cached.asset_id,
                    },
                    component="clm03b_voice",
                    component_version=self.provider_client_version,
                )
            return cached

        if runtime is not None:
            runtime.emit(
                CLM03BEventType.SPEECHGEN_CACHE_MISS,
                {"request_id": request.request_id, "cache_key": key},
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )
            runtime.emit(
                CLM03BEventType.SPEECHGEN_SYNTHESIS_STARTED,
                {"request_id": request.request_id, "cache_key": key},
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )

        provider_audio = self._fetch_audio(tts_text, selected_route.provider_voice_id, params, request)

        if runtime is not None:
            runtime.emit(
                CLM03BEventType.SPEECHGEN_AUDIO_VALIDATED,
                {
                    "request_id": request.request_id,
                    "cache_key": key,
                    "provider_audio_checksum": hashlib.sha256(provider_audio).hexdigest()[:32],
                },
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )

        canonical_pcm, sample_rate, sample_width, channels, frame_count, duration = canonicalize_pcm(
            provider_audio,
            target_rate=16000,
            target_width=2,
            target_channels=1,
        )
        canonical_audio_checksum = hashlib.sha256(canonical_pcm).hexdigest()

        receipt = build_provider_receipt(
            sg_request,
            provider_audio,
            canonical_audio_checksum,
            sample_rate,
            frame_count,
            duration,
            response_status=200,
        )

        asset = VoiceAsset(
            asset_id=f"voice-{request.request_id}-{key[:12]}",
            provider=selected_route.provider,
            voice_display_name=selected_route.voice_display_name,
            provider_voice_id=selected_route.provider_voice_id,
            locale=selected_route.locale,
            source_text=request.source_text,
            tts_text=tts_text,
            source_text_checksum=request.source_text_checksum,
            tts_text_checksum=request.tts_text_checksum,
            provider_audio_checksum=hashlib.sha256(provider_audio).hexdigest(),
            canonical_audio_checksum=canonical_audio_checksum,
            cache_key=key,
            sample_rate=sample_rate,
            sample_width=sample_width,
            channels=channels,
            frame_count=frame_count,
            duration=duration,
            provider_receipt_id=receipt.receipt_id,
            grammatical_entry_ids=(
                validated_item.source_entry_ids if validated_item else ()
            ),
            human_review_status=(
                validated_item.human_review_status if validated_item else "pending"
            ),
            reviewer_notes="",
            provenance={
                "request_id": request.request_id,
                "source_render_cycle_id": request.source_render_cycle_id,
                "source_actuation_receipt_id": request.source_actuation_receipt_id,
                "source_curriculum_item_id": request.source_curriculum_item_id,
                "curriculum_item_ids": (
                    list(validated_item.source_entry_ids)
                    if validated_item
                    else []
                ),
                "morphology_source_ids": (
                    list(validated_item.morphology_source_ids)
                    if validated_item
                    else []
                ),
                "pointing_source": (
                    list(validated_item.pointing_provenance)
                    if validated_item
                    else []
                ),
                "help_references": (
                    list(validated_item.help_references)
                    if validated_item
                    else []
                ),
                "linguistic_validation_status": (
                    validated_item.linguistic_validation_status
                    if validated_item
                    else ""
                ),
                "curriculum_status": (
                    validated_item.curriculum_status if validated_item else ""
                ),
                "validation_checksum": (
                    validated_item.validation_checksum if validated_item else ""
                ),
                "route": {
                    "provider": selected_route.provider,
                    "provider_voice_id": selected_route.provider_voice_id,
                    "locale": selected_route.locale,
                    "voice_display_name": selected_route.voice_display_name,
                },
                "parameters": asdict(params),
                "provider_audio_checksum": hashlib.sha256(provider_audio).hexdigest(),
            },
            canonical_pcm=canonical_pcm,
        )

        cache.put(asset)

        if runtime is not None:
            runtime.emit(
                CLM03BEventType.SPEECHGEN_SYNTHESIS_COMPLETED,
                {
                    "request_id": request.request_id,
                    "cache_key": key,
                    "asset_id": asset.asset_id,
                    "canonical_audio_checksum": canonical_audio_checksum[:32],
                },
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )
            runtime.emit(
                CLM03BEventType.VOICE_ASSET_CANONICALIZED,
                {
                    "request_id": request.request_id,
                    "asset_id": asset.asset_id,
                    "canonical_audio_checksum": canonical_audio_checksum[:32],
                    "frame_count": frame_count,
                    "duration": duration,
                },
                component="clm03b_voice",
                component_version=self.provider_client_version,
            )

        return asset

    def _fetch_audio(self, text: str, voice: str, params: SynthesisParameters, request: PedagogicalVoiceRequest) -> bytes:
        self._require_credentials()

        payload = {
            "token": self.api_key,
            "email": self.email,
            "voice": voice,
            "text": text,
            "format": params.format,
            "speed": params.rate,
            "pitch": params.pitch,
            "emotion": params.emotion,
            "sample_rate": params.sample_rate,
            "channels": params.channels,
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        body: bytes = b""
        content_type = ""
        for attempt in range(3):
            try:
                _status, content_type, body = self.transport("POST", self.api_url, data, headers, 120)
                break
            except SpeechGenNetworkError as exc:
                if attempt == 2:
                    raise SpeechGenSynthesisError(
                        f"SpeechGen synthesis failed after 3 attempts for {request.request_id}: {exc}"
                    ) from exc

        if not body:
            raise SpeechGenSynthesisError("SpeechGen returned empty synthesis response")

        if "application/json" not in content_type:
            raise SpeechGenSynthesisError(
                f"SpeechGen returned unexpected content-type {content_type!r}"
            )

        try:
            meta = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SpeechGenSynthesisError(f"SpeechGen returned non-JSON body: {exc}") from exc

        if meta.get("error"):
            raise SpeechGenSynthesisError(f"SpeechGen synthesis error: {meta['error']}")

        file_url = meta.get("file") or meta.get("file_cors")
        if not file_url:
            raise SpeechGenSynthesisError("SpeechGen response did not contain a download URL")

        audio_status, audio_content_type, audio_body = self.transport("GET", file_url, None, {}, 60)

        if not audio_body:
            raise SpeechGenSynthesisError("SpeechGen audio download was empty")

        if "audio" not in audio_content_type and not audio_body.startswith(b"RIFF"):
            raise SpeechGenSynthesisError(
                f"SpeechGen download is not audio: {audio_content_type!r}"
            )

        try:
            _wav_info_from_bytes(audio_body)
        except Exception as exc:
            raise SpeechGenSynthesisError(f"SpeechGen response is not a valid WAV file: {exc}") from exc

        return audio_body


class SpeechGenAuthError(Exception):
    """Raised when SpeechGen credentials are missing or invalid."""


class SpeechGenNetworkError(Exception):
    """Raised for network-level SpeechGen failures."""


class SpeechGenSynthesisError(Exception):
    """Raised for provider-reported synthesis failures."""
