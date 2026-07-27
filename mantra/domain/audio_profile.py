"""Versioned audio profile contract.

The audio profile centralizes provider, voice, locale, and synthesis settings.
Curriculum and linguistic specifications reference only the profile ID/version,
so switching voices never requires editing domain content.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

AUDIO_PROFILES_DIR = Path("data/audio_profiles")


@dataclass(frozen=True)
class AudioProfile:
    """Immutable versioned audio profile."""

    profile_id: str
    profile_version: str
    provider: str
    italian_locale: str
    italian_voice_id: str
    hebrew_locale: str
    hebrew_voice_id: str
    hebrew_text_policy: str  # e.g. "source_niqqud_preserved_tts_unpointed"
    output_format: str
    sample_rate: int
    channel_count: int
    synthesis_parameters: dict[str, Any]
    silence_durations: dict[str, float]
    cache_key_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioProfile":
        return cls(**data)

    def save(self, path: Path | None = None) -> None:
        target = path or AUDIO_PROFILES_DIR / f"{self.profile_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, profile_id: str, *, directory: Path = AUDIO_PROFILES_DIR) -> "AudioProfile":
        path = directory / f"{profile_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Audio profile not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def voice_for(self, language: str) -> tuple[str, str]:
        """Return (voice_id, locale) for a given language code."""
        lang = language.lower()
        if lang in ("it", "italian"):
            return (self.italian_voice_id, self.italian_locale)
        if lang in ("he", "hebrew"):
            return (self.hebrew_voice_id, self.hebrew_locale)
        raise ValueError(f"Unsupported language in audio profile: {language!r}")

    def cache_key_identity(
        self,
        language: str,
        tts_text: str,
        *,
        override: str = "",
    ) -> dict[str, Any]:
        """Return the deterministic cache-key payload for a synthesis request."""
        voice_id, locale = self.voice_for(language)
        return {
            "provider": self.provider,
            "voice": voice_id,
            "locale": locale,
            "text": tts_text,
            "format": self.output_format,
            "sample_rate": self.sample_rate,
            "channels": self.channel_count,
            "rate": self.synthesis_parameters.get("rate", 1.0),
            "pitch": self.synthesis_parameters.get("pitch", 0.0),
            "override": override,
            "cache_key_version": self.cache_key_version,
        }


PRODUCTION_PROFILE = AudioProfile(
    profile_id="production",
    profile_version="1.0.0",
    provider="speechgen",
    italian_locale="it-IT",
    italian_voice_id="Giuseppe",
    hebrew_locale="he-IL",
    hebrew_voice_id="Aaron",
    hebrew_text_policy="source_niqqud_preserved_tts_unpointed",
    output_format="wav",
    sample_rate=22050,
    channel_count=1,
    synthesis_parameters={"rate": 1.0, "pitch": 0.0},
    silence_durations={"inter_item_default": 0.3, "section_boundary": 0.0},
    cache_key_version="1",
)
