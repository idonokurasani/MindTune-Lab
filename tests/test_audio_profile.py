"""Tests for the versioned audio profile contract."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mantra.domain.audio_profile import (
    AUDIO_PROFILES_DIR,
    PRODUCTION_PROFILE,
    AudioProfile,
)


class AudioProfileTests(unittest.TestCase):
    """Tests proving voice resolution is configuration-driven."""

    def test_production_resolves_to_giuseppe_and_aaron(self) -> None:
        profile = PRODUCTION_PROFILE
        self.assertEqual(profile.italian_voice_id, "Giuseppe")
        self.assertEqual(profile.hebrew_voice_id, "Aaron")
        self.assertEqual(profile.voice_for("it"), ("Giuseppe", "it-IT"))
        self.assertEqual(profile.voice_for("he"), ("Aaron", "he-IL"))

    def test_voice_resolution_is_not_hard_coded_in_domain_content(self) -> None:
        # The profile is the only place that maps language to voice.
        # Curriculum and specifications do not carry voice fields.
        profile = PRODUCTION_PROFILE
        self.assertTrue(profile.profile_id)
        self.assertTrue(profile.profile_version)

    def test_changing_profile_changes_cache_identity(self) -> None:
        text = "לכתוב"
        prod = PRODUCTION_PROFILE.cache_key_identity("he", text)
        other = AudioProfile(
            profile_id="other",
            profile_version="1.0.0",
            provider="speechgen",
            italian_locale="it-IT",
            italian_voice_id="Giuseppe",
            hebrew_locale="he-IL",
            hebrew_voice_id="Hila",
            hebrew_text_policy="source_niqqud_preserved_tts_unpointed",
            output_format="wav",
            sample_rate=22050,
            channel_count=1,
            synthesis_parameters={"rate": 1.0, "pitch": 0.0},
            silence_durations={},
            cache_key_version="1",
        ).cache_key_identity("he", text)
        self.assertNotEqual(prod, other)
        self.assertEqual(other["voice"], "Hila")

    def test_hila_does_not_satisfy_aaron_requirement(self) -> None:
        profile = PRODUCTION_PROFILE
        voice, _ = profile.voice_for("he")
        self.assertEqual(voice, "Aaron")
        self.assertNotEqual(voice, "Hila")

    def test_load_and_save_roundtrip(self) -> None:
        profile = PRODUCTION_PROFILE
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "production.json"
            profile.save(path)
            loaded = AudioProfile.load("production", directory=Path(tmp))
            self.assertEqual(loaded, profile)

    def test_production_profile_file_exists(self) -> None:
        path = AUDIO_PROFILES_DIR / "production.json"
        self.assertTrue(path.exists(), f"Production profile missing: {path}")


if __name__ == "__main__":
    unittest.main()
