"""CLM-03B Hebrew reconciliation tests.

These tests verify that CLM-03B no longer accepts arbitrary free-text Hebrew
and that the ``ValidatedHebrewPedagogicalItem`` adapter correctly consumes
approved ``data/hebrew/approved/*.json`` fixtures without calling Pealim,
Phonikud, HeLP, or the inflector.
"""

from __future__ import annotations

import array
import io
import json
import math
import tempfile
import unittest
import urllib.parse
import wave
from pathlib import Path

from mindtune_clm.voice import (
    SynthesisParameters,
    ValidatedHebrewPedagogicalItem,
    VoiceCache,
)
from mindtune_clm.voice.hebrew import HebrewTextError, has_niqqud, normalize_source
from mindtune_clm.voice.hebrew_validation import (
    HumanReviewPendingError,
    InconsistentMorphologyError,
    MissingCanonicalHebrewError,
    PointingProvenanceError,
    RejectedCurriculumError,
    UnresolvedMorphologyConflictError,
    UnvalidatedGeneratedFormError,
)
from mindtune_clm.voice.models import PedagogicalVoiceRequest, sha256_text
from mindtune_clm.voice.routing import HEBREW_LOCALE, HEBREW_VOICE_ID, cache_key, route
from mindtune_clm.voice.speechgen import SpeechGenClient

APPROVED_DIR = Path(__file__).resolve().parents[3] / "data" / "hebrew" / "approved"


def _synthetic_wav(text: str, sample_rate: int = 48000) -> bytes:
    """Generate a short deterministic WAV for mocking SpeechGen."""
    duration = 0.08 + 0.04 * len(text)
    n_frames = math.floor(sample_rate * duration)
    freq = 400 + (ord(text[0]) % 400) if text else 400
    amp = 0.3 * 32767
    samples = array.array("h")
    for i in range(n_frames):
        v = int(amp * math.sin(2 * math.pi * freq * i / sample_rate))
        samples.append(v)
    bio = io.BytesIO()
    with wave.open(bio, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.setnframes(n_frames)
        handle.writeframes(samples.tobytes())
    return bio.getvalue()


class FakeTransport:
    """Injectable HTTP transport for SpeechGen tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, bytes | None, dict[str, str], int]] = []
        self._audio: dict[str, bytes] = {}
        self._file_counter = 0

    def __call__(
        self,
        method: str,
        url: str,
        data: bytes | None,
        headers: dict[str, str],
        timeout: int,
    ) -> tuple[int, str, bytes]:
        self.calls.append((method, url, data, headers, timeout))
        if "r=api/text" in url:
            body = (data or b"").decode("utf-8", errors="ignore")
            parsed = urllib.parse.parse_qs(body)
            text = parsed.get("text", [""])[0]
            voice = parsed.get("voice", [""])[0]
            token = parsed.get("token", [""])[0]
            email = parsed.get("email", [""])[0]
            assert token, "API token must be present in request body"
            assert email, "email must be present in request body"
            self._file_counter += 1
            file_id = f"file-{voice}-{self._file_counter}"
            self._audio[file_id] = _synthetic_wav(text)
            return (
                200,
                "application/json",
                json.dumps({"file": f"https://speechgen.io/download/{file_id}.wav"}).encode("utf-8"),
            )
        if "/download/" in url:
            file_id = url.rsplit("/", 1)[-1].replace(".wav", "")
            audio = self._audio.get(file_id, b"")
            return (200, "audio/wav", audio)
        return (404, "text/plain", b"not found")

    def call_count(self) -> int:
        return len(self.calls)


class CLM03BHebrewReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        with (APPROVED_DIR / "לכתוב.json").open(encoding="utf-8") as handle:
            self.lichtov = json.load(handle)
        with (APPROVED_DIR / "לעשות.json").open(encoding="utf-8") as handle:
            self.laasot = json.load(handle)
        with (APPROVED_DIR / "להיות.json").open(encoding="utf-8") as handle:
            self.lihyot = json.load(handle)

    def test_lichtov_45_properties_from_approved_json(self) -> None:
        """At least 45 properties are correctly captured for an approved form."""
        item = ValidatedHebrewPedagogicalItem.from_approved_json(
            self.lichtov,
            form_key="infinitive",
            curriculum_version="1.0.0",
            pointed_contextual_sentence="הוּא רוֹצֶה לִכְתֹּב מִכְתָּב",
            unpointed_contextual_sentence="הוא רוצה לכתוב מכתב",
            italian_gloss="scrivere",
            italian_sentence="lui vuole scrivere una lettera",
        )

        # 45+ explicit property assertions
        self.assertTrue(item.item_id)
        self.assertEqual(item.curriculum_version, "1.0.0")
        self.assertIn("infinitive", item.source_entry_ids)
        self.assertIn("pealim", item.source_entry_ids)
        self.assertEqual(item.canonical_lemma, normalize_source("לִכְתֹּב"))
        self.assertEqual(item.pointed_lemma, normalize_source("לִכְתֹּב"))
        self.assertEqual(item.unpointed_lemma, "לכתוב")
        self.assertEqual(item.root, "כ-ת-ב")
        self.assertEqual(item.binyan, "PA'AL")
        self.assertEqual(item.tense, "infinitive")
        self.assertEqual(item.mood, "")
        self.assertEqual(item.person, "")
        self.assertEqual(item.gender, "")
        self.assertEqual(item.number, "")
        self.assertEqual(item.subject, "")
        self.assertEqual(item.register, "core_modern")
        self.assertEqual(item.formal_or_contemporary, "contemporary")
        self.assertEqual(item.canonical_pointed_surface, normalize_source("לִכְתֹּב"))
        self.assertEqual(item.canonical_unpointed_surface, "לכתוב")
        self.assertEqual(item.transliteration, "lichtov")
        self.assertEqual(item.pointed_contextual_sentence, "הוּא רוֹצֶה לִכְתֹּב מִכְתָּב")
        self.assertEqual(item.unpointed_contextual_sentence, "הוא רוצה לכתוב מכתב")
        self.assertEqual(item.italian_gloss, "scrivere")
        self.assertEqual(item.italian_sentence, "lui vuole scrivere una lettera")
        self.assertIn("pealim", item.morphology_source_ids)
        self.assertEqual(item.conflict_status, "")
        self.assertIn("pealim", item.pointing_provenance)
        self.assertEqual(item.help_references, ())
        self.assertEqual(item.curriculum_status, "approved")
        self.assertEqual(item.linguistic_validation_status, "validated")
        self.assertEqual(item.human_review_status, "pending")
        self.assertEqual(item.unicode_normalization_status, "NFC")
        self.assertTrue(item.validation_checksum)
        self.assertFalse(item.unpointed_exception_approved)
        self.assertEqual(item.unpointed_override_notes, "")

        # Aaron voice request defaults
        req = item.to_voice_request()
        self.assertIsInstance(req, PedagogicalVoiceRequest)
        self.assertEqual(req.locale, HEBREW_LOCALE)
        self.assertEqual(req.provider_voice_id, HEBREW_VOICE_ID)
        self.assertEqual(req.source_text, normalize_source("הוּא רוֹצֶה לִכְתֹּב מִכְתָּב"))
        self.assertEqual(req.tts_text, normalize_source("לִכְתֹּב"))
        self.assertTrue(has_niqqud(req.source_text))
        self.assertTrue(has_niqqud(req.tts_text))
        self.assertEqual(req.source_text_checksum, sha256_text(req.source_text))
        self.assertEqual(req.tts_text_checksum, sha256_text(req.tts_text))
        self.assertFalse(req.unpointed_exception_approved)
        self.assertEqual(req.grammatical_metadata["validation_checksum"], item.validation_checksum)
        self.assertIn("pealim", req.grammatical_metadata["morphology_source_ids"])
        self.assertEqual(req.semantic_metadata["italian_gloss"], "scrivere")

    def test_aaron_source_text_is_fully_pointed_sentence_and_tts_is_surface(self) -> None:
        item = ValidatedHebrewPedagogicalItem.from_approved_json(
            self.lichtov,
            form_key="present_masculine_singular",
            pointed_contextual_sentence="הוּא כּוֹתֵב מִכְתָּב",
        )
        req = item.to_voice_request()
        self.assertEqual(req.source_text, normalize_source("הוּא כּוֹתֵב מִכְתָּב"))
        self.assertEqual(req.tts_text, normalize_source("כּוֹתֵב"))
        self.assertTrue(has_niqqud(req.source_text))
        self.assertTrue(has_niqqud(req.tts_text))

    def test_unpointed_exception_only_allowed_when_explicitly_approved(self) -> None:
        item = ValidatedHebrewPedagogicalItem.from_approved_json(
            self.lichtov,
            form_key="infinitive",
            unpointed_exception_approved=False,
        )
        # Default to_voice_request uses pointed surface and succeeds.
        req = item.to_voice_request()
        self.assertFalse(req.unpointed_exception_approved)

        # Forcing unpointed tts without the exception flag raises HebrewTextError
        # (caught here as ValueError subclass).
        with self.assertRaises(HebrewTextError):
            item.to_voice_request(tts_text="לכתוב")

    def test_validation_rejects_unapproved_curriculum(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["approval_status"] = "candidate"
        with self.assertRaises(RejectedCurriculumError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_validation_rejects_unresolved_morphology_conflict(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["unresolved_conflicts"] = [{"field_name": "surface_vocalized"}]
        with self.assertRaises(UnresolvedMorphologyConflictError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_validation_rejects_missing_canonical_pointed_hebrew(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["surface_vocalized"] = "לכתוב"  # missing niqqud
        with self.assertRaises(MissingCanonicalHebrewError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_validation_rejects_inconsistent_lemma_and_surface(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["surface_plain"] = "לשון"  # does not strip from surface_vocalized
        with self.assertRaises(InconsistentMorphologyError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_validation_rejects_rejected_human_review(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["reviewer_status"] = "rejected"
        with self.assertRaises(HumanReviewPendingError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_validation_rejects_unvalidated_llm_generated_form(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["approval_status"] = "candidate"
        form["curriculum_status"] = "approved"
        form["linguistic_status"] = "raw"
        with self.assertRaises(UnvalidatedGeneratedFormError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_validation_rejects_missing_pointing_provenance(self) -> None:
        form = self.lichtov["paradigm"]["forms"]["infinitive"].copy()
        form["source_evidence"] = []
        form["applied_overrides"] = []
        with self.assertRaises(PointingProvenanceError):
            ValidatedHebrewPedagogicalItem.from_approved_json(form)

    def test_three_approved_fixtures_all_validate(self) -> None:
        for name, data in (
            ("לכתוב", self.lichtov),
            ("לעשות", self.laasot),
            ("להיות", self.lihyot),
        ):
            with self.subTest(name=name):
                item = ValidatedHebrewPedagogicalItem.from_approved_json(
                    data, form_key="infinitive"
                )
                self.assertEqual(item.curriculum_status, "approved")
                self.assertTrue(item.pointing_provenance)

    def test_cache_key_includes_linguistic_identity_checksum(self) -> None:
        item = ValidatedHebrewPedagogicalItem.from_approved_json(
            self.lichtov, form_key="infinitive"
        )
        req = item.to_voice_request()
        selected_route = route(req)
        params = SynthesisParameters()
        base_key = cache_key(selected_route, req.tts_text, params)
        validated_key = cache_key(
            selected_route,
            req.tts_text,
            params,
            linguistic_identity_checksum=item.validation_checksum,
        )
        self.assertNotEqual(base_key, validated_key)

    def test_speechgen_synthesizes_validated_item_and_records_full_provenance(self) -> None:
        item = ValidatedHebrewPedagogicalItem.from_approved_json(
            self.lichtov,
            form_key="infinitive",
            pointed_contextual_sentence="הוּא רוֹצֶה לִכְתֹּב",
        )
        cache_dir = Path(tempfile.mkdtemp())
        cache = VoiceCache(cache_dir)
        transport = FakeTransport()
        client = SpeechGenClient(
            api_key="fake-token", email="fake@example.com", transport=transport
        )
        asset = client.synthesize(item, cache)

        self.assertEqual(asset.provider_voice_id, HEBREW_VOICE_ID)
        self.assertEqual(asset.source_text, normalize_source("הוּא רוֹצֶה לִכְתֹּב"))
        self.assertEqual(asset.tts_text, item.canonical_pointed_surface)
        self.assertTrue(has_niqqud(asset.tts_text))
        self.assertIn("pealim", asset.provenance["morphology_source_ids"])
        self.assertIn("pealim", asset.provenance["pointing_source"])
        self.assertEqual(asset.provenance["validation_checksum"], item.validation_checksum)
        self.assertEqual(asset.provenance["source_curriculum_item_id"], item.item_id)
        self.assertEqual(asset.human_review_status, "pending")

        audio_asset = asset.to_audio_asset()
        provenance_text = "\n".join(audio_asset.provenance)
        self.assertIn("morphology_source_ids=pealim", provenance_text)
        self.assertIn("pointing_source=pealim", provenance_text)
        self.assertIn("validation_checksum=", provenance_text)
        self.assertIn("source_curriculum_item_id=", provenance_text)

        # No live network credentials or absolute paths leaked.
        self.assertNotIn("fake-token", provenance_text)
        self.assertNotIn("fake@example.com", provenance_text)
        self.assertNotIn(str(cache_dir), provenance_text)

        # Clean up temp cache directory.
        import shutil

        shutil.rmtree(cache_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
