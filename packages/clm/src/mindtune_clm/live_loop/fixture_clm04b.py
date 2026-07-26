"""Deterministic fixtures for CLM-04B live closed-loop tests."""

from __future__ import annotations

import hashlib
import io
import math
import tempfile
import wave
from pathlib import Path
from typing import Any

from mindtune_clm.audio.assets import AudioAsset, AudioAssetRegistry, AudioRole
from mindtune_clm.audio.fixture_clm03 import default_registry as _default_audio_registry
from mindtune_clm.audio.transforms import silence_transform
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.voice.cache import VoiceCache
from mindtune_clm.voice.canonicalize import build_canonical_wav_bytes, canonicalize_pcm
from mindtune_clm.voice.fixture_clm03b import (
    DEFAULT_PARAMS,
    hebrew_form_request,
    hebrew_sentence_request,
    italian_label_request,
)
from mindtune_clm.voice.models import VoiceAsset, sha256_text
from mindtune_clm.voice.routing import build_speechgen_request_text, cache_key, route

FC11_HEADER = (
    "timestamp,packet_index,eeg_scaled,attention_score_smoothed,"
    "meditation_score_smoothed,signal_quality,artifact_flag,movement_flag,packet_loss"
)


def _synthetic_wav_bytes(text: str, sample_rate: int = 22050) -> bytes:
    """Create a short deterministic WAV fixture from a text seed."""
    duration = 0.08 + 0.04 * max(1, len(text))
    n_frames = math.floor(sample_rate * duration)
    freq = 400 + (ord(text[0]) % 400) if text else 400
    amp = 0.3 * 32767
    samples = bytearray()
    for i in range(n_frames):
        v = int(amp * math.sin(2.0 * math.pi * freq * i / sample_rate))
        samples.extend(v.to_bytes(2, "little", signed=True))
    return build_canonical_wav_bytes(bytes(samples), sample_rate, 2, 1)


def _voice_asset_from_request(
    request: Any,
    asset_id: str,
    provider_receipt_id: str = "synthetic-receipt",
) -> VoiceAsset:
    """Build a deterministic VoiceAsset and the key SpeechGen would use."""
    voice_route = route(request)
    tts_text = build_speechgen_request_text(request, voice_route)
    key = cache_key(voice_route, tts_text, DEFAULT_PARAMS)
    provider_wav = _synthetic_wav_bytes(tts_text, DEFAULT_PARAMS.sample_rate)
    canonical_pcm, _, _, _, frame_count, duration = canonicalize_pcm(provider_wav)
    return VoiceAsset(
        asset_id=asset_id,
        provider=voice_route.provider,
        voice_display_name=voice_route.voice_display_name,
        provider_voice_id=voice_route.provider_voice_id,
        locale=voice_route.locale,
        source_text=request.source_text,
        tts_text=tts_text,
        source_text_checksum=sha256_text(request.source_text),
        tts_text_checksum=sha256_text(tts_text),
        provider_audio_checksum=hashlib.sha256(provider_wav).hexdigest(),
        canonical_audio_checksum=hashlib.sha256(canonical_pcm).hexdigest(),
        cache_key=key,
        sample_rate=16000,
        sample_width=2,
        channels=1,
        frame_count=frame_count,
        duration=duration,
        provider_receipt_id=provider_receipt_id,
        grammatical_entry_ids=(),
        human_review_status="approved",
        reviewer_notes="synthetic fixture",
        provenance={"fixture": "clm04b", "route": voice_route.voice_display_name},
        canonical_pcm=canonical_pcm,
    )


def _composite_audio_asset(
    label_asset: AudioAsset,
    sentence_asset: AudioAsset,
    form_asset: AudioAsset,
) -> AudioAsset:
    """Assemble the Giuseppe/Aaron composite as the CLM-03 speech segment."""
    sr = 16000
    parts = [
        label_asset.canonical_pcm,
        silence_transform(300, sr),
        sentence_asset.canonical_pcm,
        silence_transform(300, sr),
        form_asset.canonical_pcm,
        silence_transform(600, sr),
    ]
    full_pcm = b"".join(parts)
    frame_count = len(full_pcm) // 2
    duration = frame_count / sr
    with io.BytesIO() as bio:
        with wave.open(bio, "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sr)
            handle.setnframes(frame_count)
            handle.writeframes(full_pcm)
        canonical_bytes = bio.getvalue()
    return AudioAsset(
        asset_id="speech_segment",
        content_checksum=hashlib.sha256(canonical_bytes).hexdigest(),
        role=AudioRole.SPEECH_SEGMENT,
        label="giuseppe_aaron_bilingual_fixture",
        sample_rate=sr,
        sample_width=2,
        channels=1,
        frame_count=frame_count,
        duration=duration,
        source_type="synthetic_voice_composite",
        provenance=[
            "provider=speechgen",
            "voices=Giuseppe,Aaron,Aaron",
            "locales=it-IT,he-IL,he-IL",
            f"component_pointers={label_asset.asset_id},{sentence_asset.asset_id},{form_asset.asset_id}",
        ],
        semantic_tags=frozenset(["bilingual", "fixture", "clm04b"]),
        canonical_pcm=full_pcm,
    )


def build_voice_cache_and_registry(cache_dir: Path | None = None) -> tuple[VoiceCache, AudioAssetRegistry]:
    """Seed a VoiceCache and AudioAssetRegistry with synthetic Giuseppe/Aaron assets."""
    cache_dir = cache_dir or Path(tempfile.mkdtemp(prefix="clm04b_voice_cache_"))
    cache = VoiceCache(cache_dir)

    label_asset = _voice_asset_from_request(italian_label_request(), "giuseppe_label")
    sentence_asset = _voice_asset_from_request(hebrew_sentence_request(), "aaron_sentence")
    form_asset = _voice_asset_from_request(hebrew_form_request(), "aaron_form")

    for asset in (label_asset, sentence_asset, form_asset):
        cache.put(asset)

    speech = _composite_audio_asset(
        label_asset.to_audio_asset("giuseppe_label", role=AudioRole.SPEECH_SEGMENT, label="Italian label"),
        sentence_asset.to_audio_asset("aaron_sentence", role=AudioRole.SPEECH_SEGMENT, label="Aaron sentence"),
        form_asset.to_audio_asset("aaron_form", role=AudioRole.SPEECH_SEGMENT, label="Aaron form"),
    )

    registry = _default_audio_registry()
    registry.register(speech)
    return cache, registry


def make_synthetic_csv(
    duration: float = 2.5,
    packet_interval: float = 0.1,
    base_eeg: float = 78.5,
) -> str:
    """Return a deterministic CSV string compatible with FC11LiveSource."""
    lines = [FC11_HEADER]
    count = int(duration / packet_interval)
    for i in range(count):
        t = round(i * packet_interval, 3)
        noise = 0.0 if i % 2 == 0 else 0.02
        eeg = round(base_eeg + noise, 3)
        lines.append(f"{t:.3f},{i},{eeg},48.0,55.0,5,0,0,0")
    return "\n".join(lines) + "\n"


def _frame(
    session_id: str,
    seq: int,
    timestamp: float,
    eeg_stability: float | None,
    eeg_quality: str | None,
    behavioral_latency_ms: float | None = None,
    hesitation_score: float | None = None,
    error_score: float | None = None,
    modalities: list[str] | None = None,
) -> ObservationFrame:
    return ObservationFrame(
        observation_frame_id=f"obs-{session_id}-{seq}",
        control_cycle_id=f"cc-{session_id}-{seq}",
        session_id=session_id,
        sequence_number=seq,
        observation_timestamp=timestamp,
        behavioral_latency_ms=behavioral_latency_ms,
        hesitation_score=hesitation_score,
        error_score=error_score,
        eeg_stability=eeg_stability,
        eeg_quality=eeg_quality,
        respiration_stability=0.8,
        voice_stability=0.8,
        available_modalities=list(modalities) if modalities is not None else ["eeg"],
        source_event_ids=[f"src-{session_id}-{seq}"],
    )


def make_synthetic_frames(  # noqa: C901
    session_id: str = "clm04b-fixture",
    scenario: str = "stable",
    count: int = 10,
    timestamp_step: float = 1.0,
) -> list[ObservationFrame]:
    """Return deterministic ObservationFrames for a named scenario."""
    frames: list[ObservationFrame] = []
    for i in range(1, count + 1):
        t = float(i) * timestamp_step
        modalities: list[str] | None = None
        if scenario == "stable":
            eeg = 0.95
            quality = "5"
        elif scenario == "deterioration":
            eeg = 0.95 if i < 3 else 0.2
            quality = "5"
        elif scenario == "escalation":
            eeg = 0.1
            quality = "5"
        elif scenario == "recovery":
            eeg = 0.2 if i < 4 else 0.95
            quality = "5"
        elif scenario == "disconnect":
            eeg = None
            quality = None
            modalities = []
        elif scenario == "missing_cache":
            eeg = 0.5
            quality = "5"
        elif scenario == "render_failure":
            eeg = 0.5
            quality = "5"
        elif scenario == "playback_failure":
            eeg = 0.5
            quality = "5"
        elif scenario == "kill":
            eeg = 0.95
            quality = "5"
        else:
            eeg = 0.95
            quality = "5"
        frames.append(
            _frame(
                session_id,
                i,
                t,
                eeg_stability=eeg,
                eeg_quality=quality,
                modalities=modalities,
            )
        )
    return frames
