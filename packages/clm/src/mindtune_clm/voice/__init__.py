"""CLM-03B — SpeechGen Giuseppe/Aaron bilingual voice asset pipeline."""

from mindtune_clm.voice.cache import VoiceCache
from mindtune_clm.voice.events import CLM03BEventType
from mindtune_clm.voice.hebrew import HebrewTextError
from mindtune_clm.voice.hebrew_validation import HebrewValidationError
from mindtune_clm.voice.models import (
    PedagogicalVoiceRequest,
    ProviderReceipt,
    SynthesisParameters,
    VoiceAsset,
    normalize_text,
    sha256_text,
)
from mindtune_clm.voice.routing import (
    HEBREW_LOCALE,
    HEBREW_VOICE_ID,
    ITALIAN_LOCALE,
    ITALIAN_VOICE_ID,
    PROVIDER,
    VoiceRoute,
    VoiceRoutingError,
    default_synthesis_parameters,
    route,
)
from mindtune_clm.voice.speechgen import (
    SpeechGenAuthError,
    SpeechGenClient,
    SpeechGenNetworkError,
    SpeechGenSynthesisError,
)
from mindtune_clm.voice.validated_hebrew import ValidatedHebrewPedagogicalItem

__all__ = [
    "CLM03BEventType",
    "HEBREW_LOCALE",
    "HEBREW_VOICE_ID",
    "HebrewTextError",
    "HebrewValidationError",
    "ITALIAN_LOCALE",
    "ITALIAN_VOICE_ID",
    "PedagogicalVoiceRequest",
    "PROVIDER",
    "ProviderReceipt",
    "SpeechGenAuthError",
    "SpeechGenClient",
    "SpeechGenNetworkError",
    "SpeechGenSynthesisError",
    "SynthesisParameters",
    "ValidatedHebrewPedagogicalItem",
    "VoiceAsset",
    "VoiceCache",
    "VoiceRoute",
    "VoiceRoutingError",
    "default_synthesis_parameters",
    "normalize_text",
    "route",
    "sha256_text",
]
