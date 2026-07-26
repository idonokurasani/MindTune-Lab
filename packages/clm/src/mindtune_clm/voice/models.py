"""CLM-03B SpeechGen Giuseppe/Aaron voice pipeline models."""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.audio.assets import AudioAsset, AudioRole


@dataclass(frozen=True)
class SynthesisParameters:
    """SpeechGen synthesis parameters that are part of cache identity."""

    rate: float = 1.0
    pitch: float = 0.0
    format: str = "wav"
    emotion: str = "good"
    sample_rate: int = 22050
    channels: int = 1


@dataclass(frozen=True)
class PedagogicalVoiceRequest:
    """A pedagogical voice request preserving both pointed and optionally unpointed forms."""

    request_id: str
    language: str
    locale: str
    voice_display_name: str
    provider_voice_id: str
    source_text: str
    tts_text: str
    source_text_checksum: str
    tts_text_checksum: str
    grammatical_metadata: dict[str, Any]
    semantic_metadata: dict[str, Any]
    register: str = "default"
    source_curriculum_item_id: str | None = None
    source_render_cycle_id: str | None = None
    source_actuation_receipt_id: str | None = None
    normalization_policy_version: str = "1.0.0"
    synthesis_parameter_version: str = "1.0.0"
    unpointed_exception_approved: bool = False
    unpointed_override_notes: str = ""

    def __post_init__(self) -> None:
        if not self.source_text:
            raise ValueError("source_text must not be empty")
        if not self.tts_text:
            raise ValueError("tts_text must not be empty")


@dataclass(frozen=True)
class SpeechGenRequest:
    """Normalized SpeechGen request used for synthesis and cache identity."""

    provider: str
    provider_voice_id: str
    locale: str
    synthesis_text: str
    output_format: str
    parameters: SynthesisParameters
    request_checksum: str
    cache_key: str
    timeout_seconds: int = 120
    max_retries: int = 3
    provider_client_version: str = "1.0.0"


@dataclass(frozen=True)
class ProviderReceipt:
    """A redacted, credential-free provider receipt."""

    receipt_id: str
    provider: str
    provider_voice_id: str
    locale: str
    synthesis_text: str
    provider_audio_checksum: str
    canonical_audio_checksum: str
    sample_rate: int
    frame_count: int
    duration: float
    cache_key: str
    response_status: int
    timestamp: float = 0.0
    provider_response: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VoiceAsset:
    """A canonicalized voice asset that can be registered with CLM-03."""

    asset_id: str
    provider: str
    voice_display_name: str
    provider_voice_id: str
    locale: str
    source_text: str
    tts_text: str
    source_text_checksum: str
    tts_text_checksum: str
    provider_audio_checksum: str
    canonical_audio_checksum: str
    cache_key: str
    sample_rate: int
    sample_width: int
    channels: int
    frame_count: int
    duration: float
    provider_receipt_id: str
    grammatical_entry_ids: tuple[str, ...] = ()
    human_review_status: str = "pending"
    reviewer_notes: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    canonical_pcm: bytes = b""

    def to_audio_asset(
        self,
        asset_id: str | None = None,
        role: AudioRole = AudioRole.SPEECH_SEGMENT,
        label: str | None = None,
    ) -> AudioAsset:
        """Return a CLM-03 AudioAsset wrapping this canonical PCM."""
        asset_id = asset_id or self.asset_id
        label = label or asset_id
        return AudioAsset(
            asset_id=asset_id,
            content_checksum=hashlib.sha256(self.canonical_pcm).hexdigest(),
            role=role,
            label=label,
            sample_rate=self.sample_rate,
            sample_width=self.sample_width,
            channels=self.channels,
            frame_count=self.frame_count,
            duration=self.duration,
            source_type="synthetic_voice",
            provenance=[
                f"provider={self.provider}",
                f"voice={self.provider_voice_id}",
                f"locale={self.locale}",
                f"tts_text_checksum={self.tts_text_checksum}",
                f"source_text_checksum={self.source_text_checksum}",
                f"provider_audio_checksum={self.provider_audio_checksum}",
                f"canonical_audio_checksum={self.canonical_audio_checksum}",
                f"cache_key={self.cache_key}",
                f"human_review_status={self.human_review_status}",
                f"provider_receipt_id={self.provider_receipt_id}",
                f"grammatical_entry_ids={','.join(self.grammatical_entry_ids)}",
            ],
            semantic_tags=frozenset([self.locale, self.provider, self.provider_voice_id]),
            canonical_pcm=self.canonical_pcm,
        )

    def with_review(self, status: str, notes: str = "") -> "VoiceAsset":
        """Return a copy with updated human-review metadata."""
        return VoiceAsset(
            asset_id=self.asset_id,
            provider=self.provider,
            voice_display_name=self.voice_display_name,
            provider_voice_id=self.provider_voice_id,
            locale=self.locale,
            source_text=self.source_text,
            tts_text=self.tts_text,
            source_text_checksum=self.source_text_checksum,
            tts_text_checksum=self.tts_text_checksum,
            provider_audio_checksum=self.provider_audio_checksum,
            canonical_audio_checksum=self.canonical_audio_checksum,
            cache_key=self.cache_key,
            sample_rate=self.sample_rate,
            sample_width=self.sample_width,
            channels=self.channels,
            frame_count=self.frame_count,
            duration=self.duration,
            provider_receipt_id=self.provider_receipt_id,
            grammatical_entry_ids=self.grammatical_entry_ids,
            human_review_status=status,
            reviewer_notes=notes,
            provenance=self.provenance,
            canonical_pcm=self.canonical_pcm,
        )


def sha256_text(text: str) -> str:
    """Return SHA-256 hex of a Unicode text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    """Deterministic Unicode NFC normalization; never removes Hebrew marks."""
    return unicodedata.normalize("NFC", text)
