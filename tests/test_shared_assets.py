"""Tests for shared audio assets, compact mantra, and Domino tense rules."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from mantra.phase1.assets import (
    TENSE_MARKER_ASSETS,
    AudioAssetRegistry,
    build_compact_mantra,
    domino_feedback_asset_id,
    ensure_tense_markers,
)
from mantra.phase1.sheva import DIACRITICS
from mantra.phase1.tts import FakeTTSProvider, _cache_key
from mantra.phase1.utils import normalize_unicode


class CountingProvider(FakeTTSProvider):
    """Fake provider that counts synthesis calls."""

    def __init__(self) -> None:
        super().__init__(sample_rate=22050, base_duration=0.05)
        self.calls: list[str] = []

    def synthesize(self, segment: Any) -> Any:
        text = getattr(segment, "tts_text", "") or getattr(segment, "source_text", "")
        self.calls.append(text)
        return super().synthesize(segment)


class SharedAudioAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cache_dir = self.tmp / "cache"
        self.registry_path = self.tmp / "assets.json"
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        # Redirect global paths to temp dir for tests.
        self.cache_patcher = patch("mantra.phase1.assets.GLOBAL_CACHE_DIR", self.cache_dir)
        self.registry_patcher = patch(
            "mantra.phase1.assets.ASSET_REGISTRY_PATH", self.registry_path
        )
        self.cache_patcher.start()
        self.registry_patcher.start()

    def tearDown(self) -> None:
        self.registry_patcher.stop()
        self.cache_patcher.stop()

    def _registry(self) -> AudioAssetRegistry:
        return AudioAssetRegistry(self.registry_path)

    def test_cache_key_includes_voice_text_and_settings(self) -> None:
        k1 = _cache_key("שָׁלוֹם", "speechgen", "Hannah", 1.0, 0.0, "wav", None, locale="he-IL")
        k2 = _cache_key("שָׁלוֹם", "speechgen", "Aaron", 1.0, 0.0, "wav", None, locale="he-IL")
        k3 = _cache_key("שָׁלוֹם", "speechgen", "Hannah", 0.9, 0.0, "wav", None, locale="he-IL")
        k4 = _cache_key("שָׁלוֹם", "speechgen", "Hannah", 1.0, 0.0, "wav", None, locale="he-IL")
        self.assertNotEqual(k1, k2)
        self.assertNotEqual(k1, k3)
        self.assertEqual(k1, k4)

    def test_ensure_does_not_synthesize_same_text_twice(self) -> None:
        provider = CountingProvider()
        registry = self._registry()

        registry.ensure("he.test.one", "בְּרֵאשִׁית", "Hannah", "he-IL", provider=provider)
        registry.ensure("he.test.two", "בְּרֵאשִׁית", "Hannah", "he-IL", provider=provider)

        self.assertEqual(len(provider.calls), 1)

    def test_domino_feedback_resolves_same_target_asset(self) -> None:
        target = "he.lehitkasher.past.1sg"
        self.assertEqual(domino_feedback_asset_id(target), target)

    def test_tense_markers_are_global_and_shared(self) -> None:
        provider = CountingProvider()
        registry = self._registry()
        ensure_tense_markers(registry, provider=provider)

        for asset_id, text in TENSE_MARKER_ASSETS.items():
            asset = registry.get(asset_id)
            self.assertIsNotNone(asset)
            assert asset is not None
            self.assertEqual(asset.text, normalize_unicode(text))
            self.assertEqual(asset.source_text, text)
            self.assertEqual(asset.voice, "Hannah")

    def test_exact_hebrew_unicode_survives_roundtrip(self) -> None:
        provider = CountingProvider()
        registry = self._registry()
        text = "אֲנִי הִתְקַשַּׁרְתִּי"
        registry.ensure(
            "he.roundtrip", text, "Hannah", "he-IL", source_text=text, provider=provider
        )

        # Reload registry from disk.
        registry2 = self._registry()
        asset = registry2.get("he.roundtrip")
        self.assertIsNotNone(asset)
        assert asset is not None
        self.assertEqual(asset.source_text, text)
        self.assertEqual(asset.text, normalize_unicode(text))
        path = registry2.resolve_path("he.roundtrip")
        self.assertIsNotNone(path)
        assert path is not None
        self.assertTrue(path.exists())

    def test_reassembly_with_different_pauses_does_not_resynthesize(self) -> None:
        provider = CountingProvider()
        registry = self._registry()
        text = "לְהִתְקַשֵּׁר"
        registry.ensure("he.inf", text, "Hannah", "he-IL", provider=provider)

        items: list[tuple[str, float | None]] = [("he.inf", None), ("he.inf", None)]
        output1 = self.tmp / "mantra1.wav"
        output2 = self.tmp / "mantra2.wav"
        build_compact_mantra(registry, items, output1, default_pause=0.2)
        build_compact_mantra(registry, items, output2, default_pause=0.8)

        # Only one synthesis call for the single unique text.
        self.assertEqual(len(provider.calls), 1)
        self.assertTrue(output1.exists())
        self.assertTrue(output2.exists())
        self.assertNotEqual(output1.stat().st_size, output2.stat().st_size)


class CompactMantraOutputTests(unittest.TestCase):
    """Tests that inspect the generated lehitkasher compact mantra artifacts."""

    OUTPUT_DIR = Path("output/mantra_phase1_lehitkasher_hannah_full_niqqud")

    @classmethod
    def setUpClass(cls) -> None:
        if not (cls.OUTPUT_DIR / "compact_manifest.json").exists():
            raise unittest.SkipTest("compact mantra has not been built yet")

    def test_one_italian_intro_and_no_grammatical_labels(self) -> None:
        manifest = json.loads(
            (self.OUTPUT_DIR / "compact_manifest.json").read_text(encoding="utf-8")
        )
        asset_ids = manifest.get("asset_ids", [])

        italian_ids = [aid for aid in asset_ids if aid.startswith("it.")]
        self.assertEqual(
            len(italian_ids), 1, "Only one Italian utterance is allowed in a compact mantra"
        )
        self.assertEqual(italian_ids[0], "it.lehitkasher.infinitive")

        forbidden = (
            "Passato",
            "Presente",
            "Futuro",
            "Imperativo",
            "prima persona",
            "seconda persona",
            "terza persona",
        )
        registry = AudioAssetRegistry()
        for aid in asset_ids:
            asset = registry.get(aid)
            if asset and asset.voice == "Giuseppe":
                text = asset.text
                self.assertFalse(
                    any(f in text for f in forbidden),
                    f"Italian grammatical label found in {aid}: {text!r}",
                )

    def test_hebrew_sequence_fully_pointed(self) -> None:
        registry = AudioAssetRegistry()
        manifest = json.loads(
            (self.OUTPUT_DIR / "compact_manifest.json").read_text(encoding="utf-8")
        )
        for aid in manifest.get("asset_ids", []):
            asset = registry.get(aid)
            if not asset or asset.voice != "Hannah":
                continue
            self.assertTrue(
                any(c in DIACRITICS for c in asset.text),
                f"Hebrew asset {aid} lacks niqqud: {asset.text!r}",
            )
            self.assertEqual(asset.text, asset.source_text)

    def test_combined_plural_lines_use_ve_and_no_separate_duplicates(self) -> None:
        registry = AudioAssetRegistry()
        manifest = json.loads(
            (self.OUTPUT_DIR / "compact_manifest.json").read_text(encoding="utf-8")
        )
        asset_ids = manifest.get("asset_ids", [])

        # Combined plural lines should appear.
        combined_targets = [
            "he.lehitkasher.past.3pl",
            "he.lehitkasher.future.2pl",
            "he.lehitkasher.future.3pl",
        ]
        for aid in combined_targets:
            self.assertIn(aid, asset_ids)
            asset = registry.get(aid)
            assert asset is not None
            self.assertIn("וְ", asset.text)

        # Separate duplicate masculine/feminine plural lines are absent.
        self.assertNotIn("he.lehitkasher.past.3mpl", asset_ids)
        self.assertNotIn("he.lehitkasher.past.3fpl", asset_ids)
        self.assertNotIn("he.lehitkasher.future.2mpl", asset_ids)
        self.assertNotIn("he.lehitkasher.future.2fpl", asset_ids)
        self.assertNotIn("he.lehitkasher.future.3mpl", asset_ids)
        self.assertNotIn("he.lehitkasher.future.3fpl", asset_ids)

    def test_domino_exercises_use_only_canonical_tense_markers(self) -> None:
        exercises = json.loads(
            (self.OUTPUT_DIR / "domino_exercises.json").read_text(encoding="utf-8")
        )
        allowed_markers = {"בֶּעָבָר", "בַּהוֹוֶה", "בֶּעָתִיד"}
        forbidden_temporal = [
            "una settimana fa",
            "ieri",
            "l'anno scorso",
            "domani",
            "fra un anno",
            "la settimana prossima",
        ]
        for ex in exercises:
            self.assertIn(ex["tense_marker_text"], allowed_markers)
            for forbidden in forbidden_temporal:
                self.assertNotIn(forbidden, ex.get("target_text", "").lower())
            self.assertEqual(ex["feedback_asset_id"], ex["target_asset_id"])

    def test_domino_tense_markers_match_global_assets(self) -> None:
        registry = AudioAssetRegistry()
        exercises = json.loads(
            (self.OUTPUT_DIR / "domino_exercises.json").read_text(encoding="utf-8")
        )
        tense_markers = {ex["tense_marker_asset_id"] for ex in exercises}
        self.assertEqual(tense_markers, {"he.tense.past", "he.tense.present", "he.tense.future"})
        for marker in tense_markers:
            self.assertIsNotNone(registry.resolve_path(marker))


if __name__ == "__main__":
    unittest.main()
