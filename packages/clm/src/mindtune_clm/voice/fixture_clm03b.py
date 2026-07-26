"""CLM-03B bilingual fixture and smoke-test data."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from mindtune_clm.audio.assets import AudioAsset, AudioRole
from mindtune_clm.audio.transforms import silence_transform
from mindtune_clm.voice.hebrew import normalize_source as normalize_hebrew
from mindtune_clm.voice.models import (
    PedagogicalVoiceRequest,
    SynthesisParameters,
    sha256_text,
)
from mindtune_clm.voice.routing import (
    HEBREW_LOCALE,
    HEBREW_VOICE_ID,
    ITALIAN_LOCALE,
    ITALIAN_VOICE_ID,
    PROVIDER,
)

HEBREW_SENTENCE_RAW = "הוּא מְהַוֶּה דֻּגְמָה טוֹבָה"
HEBREW_FORM_RAW = "מְהַוֶּה"

# Bilingual fixture texts (pointed Hebrew preserved for source and TTS).
ITALIAN_LABEL = "Presente, maschile singolare"
HEBREW_SENTENCE_SOURCE = normalize_hebrew(HEBREW_SENTENCE_RAW)
HEBREW_SENTENCE_TTS = HEBREW_SENTENCE_SOURCE
HEBREW_FORM_SOURCE = normalize_hebrew(HEBREW_FORM_RAW)
HEBREW_FORM_TTS = HEBREW_FORM_SOURCE

DEFAULT_PARAMS = SynthesisParameters(
    rate=1.0,
    pitch=0.0,
    format="wav",
    emotion="good",
    sample_rate=22050,
    channels=1,
)


def _request(
    request_id: str,
    language: str,
    locale: str,
    voice: str,
    source_text: str,
    tts_text: str,
    entry_id: str,
) -> PedagogicalVoiceRequest:
    return PedagogicalVoiceRequest(
        request_id=request_id,
        language=language,
        locale=locale,
        voice_display_name=voice,
        provider_voice_id=voice,
        source_text=source_text,
        tts_text=tts_text,
        source_text_checksum=sha256_text(source_text),
        tts_text_checksum=sha256_text(tts_text),
        grammatical_metadata={"entry_id": entry_id},
        semantic_metadata={"fixture": "clm03b_bilingual"},
        source_curriculum_item_id=entry_id,
        source_render_cycle_id="rc-fixture",
        source_actuation_receipt_id="rcpt-fixture",
    )


def italian_label_request() -> PedagogicalVoiceRequest:
    """Giuseppe Italian label request."""
    return _request(
        "clm03b_it_label",
        "it",
        ITALIAN_LOCALE,
        ITALIAN_VOICE_ID,
        ITALIAN_LABEL,
        ITALIAN_LABEL,
        "it_label_presente_maschile_singolare",
    )


def hebrew_sentence_request() -> PedagogicalVoiceRequest:
    """Aaron Hebrew contextual sentence request."""
    return _request(
        "clm03b_he_sentence",
        "he",
        HEBREW_LOCALE,
        HEBREW_VOICE_ID,
        HEBREW_SENTENCE_SOURCE,
        HEBREW_SENTENCE_TTS,
        "he_sentence_mehave_dugma_tova",
    )


def hebrew_form_request() -> PedagogicalVoiceRequest:
    """Aaron Hebrew isolated form request."""
    return _request(
        "clm03b_he_form",
        "he",
        HEBREW_LOCALE,
        HEBREW_VOICE_ID,
        HEBREW_FORM_SOURCE,
        HEBREW_FORM_TTS,
        "he_form_mehave",
    )


def sample_requests() -> list[PedagogicalVoiceRequest]:
    """Return all three fixture voice requests."""
    return [
        italian_label_request(),
        hebrew_sentence_request(),
        hebrew_form_request(),
    ]


def _concat_pcm(parts: list[bytes]) -> bytes:
    return b"".join(parts)


def build_bilingual_audio_asset(
    label_asset: AudioAsset,
    sentence_asset: AudioAsset,
    form_asset: AudioAsset,
    inter_item_silence_ms: int = 300,
    final_silence_ms: int = 600,
) -> AudioAsset:
    """Assemble the bilingual fixture into a single CLM-03 AudioAsset."""
    sr = 16000
    parts: list[bytes] = [
        label_asset.canonical_pcm,
        silence_transform(inter_item_silence_ms, sr),
        sentence_asset.canonical_pcm,
        silence_transform(inter_item_silence_ms, sr),
        form_asset.canonical_pcm,
        silence_transform(final_silence_ms, sr),
    ]
    combined_pcm = _concat_pcm(parts)
    frame_count = len(combined_pcm) // 2
    duration = frame_count / sr
    return AudioAsset(
        asset_id="bilingual_clm03b_fixture",
        content_checksum=hashlib.sha256(combined_pcm).hexdigest(),
        role=AudioRole.SPEECH_SEGMENT,
        label="bilingual_clm03b_fixture",
        sample_rate=sr,
        sample_width=2,
        channels=1,
        frame_count=frame_count,
        duration=duration,
        source_type="voice_fixture_composite",
        provenance=[
            f"provider={PROVIDER}",
            f"voices={ITALIAN_VOICE_ID},{HEBREW_VOICE_ID},{HEBREW_VOICE_ID}",
            f"locales={ITALIAN_LOCALE},{HEBREW_LOCALE},{HEBREW_LOCALE}",
            f"component_pointers={label_asset.asset_id},{sentence_asset.asset_id},{form_asset.asset_id}",
        ],
        semantic_tags=frozenset(["bilingual", "fixture"]),
        canonical_pcm=combined_pcm,
    )


@dataclass
class SmokeTestData:
    """Input data for the manual non-CI smoke test."""

    italian_label: PedagogicalVoiceRequest
    hebrew_sentence: PedagogicalVoiceRequest
    hebrew_form: PedagogicalVoiceRequest
    params: SynthesisParameters
