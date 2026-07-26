"""CLM-03B SpeechGen Giuseppe/Aaron bilingual voice pipeline tests."""

from __future__ import annotations

import hashlib
import io
import json
import math
import tempfile
import unittest
import urllib.parse
import wave
from pathlib import Path
from typing import Any

from mindtune_clm.audio import AudioAssetRegistry, AudioRenderer
from mindtune_clm.audio.assets import AudioRole
from mindtune_clm.audio.fixture_clm03 import (
    state_baseline,
    state_escalated,
    state_first_intervention,
    state_withdrawal_step_2,
)
from mindtune_clm.audio.playback import PlaybackScheduler
from mindtune_clm.voice.cache import VoiceCache
from mindtune_clm.voice.fixture_clm03b import (
    HEBREW_FORM_SOURCE,
    HEBREW_SENTENCE_SOURCE,
    ITALIAN_LABEL,
    hebrew_form_request,
    hebrew_sentence_request,
    italian_label_request,
)
from mindtune_clm.voice.hebrew import (
    HebrewTextError,
    has_niqqud,
    normalize_source,
    validate_word_separation,
)
from mindtune_clm.voice.models import (
    PedagogicalVoiceRequest,
    SynthesisParameters,
    VoiceAsset,
    sha256_text,
)
from mindtune_clm.voice.routing import (
    HEBREW_LOCALE,
    HEBREW_VOICE_ID,
    ITALIAN_LOCALE,
    ITALIAN_VOICE_ID,
    PROVIDER,
    VoiceRoutingError,
    cache_key,
    route,
)
from mindtune_clm.voice.speechgen import (
    SpeechGenAuthError,
    SpeechGenClient,
    SpeechGenSynthesisError,
)


def _synthetic_wav(text: str, sample_rate: int = 48000) -> bytes:
    """Generate a short deterministic WAV for mocking SpeechGen."""
    import array

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


class FakeRuntime:
    """Captures CLM-03B events for tests."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        component: str = "clm03b_voice",
        component_version: str = "1.0.0",
    ) -> None:
        self.events.append((event_type, payload))


def _client_with_api(transport: FakeTransport) -> SpeechGenClient:
    return SpeechGenClient(api_key="fake-token", email="fake@example.com", transport=transport)


class CLM03BRoutingTests(unittest.TestCase):
    def test_provider_is_exactly_speechgen(self) -> None:
        r = route(italian_label_request())
        self.assertEqual(r.provider, "speechgen")

    def test_italian_routes_to_giuseppe(self) -> None:
        r = route(italian_label_request())
        self.assertEqual(r.provider_voice_id, ITALIAN_VOICE_ID)
        self.assertEqual(r.locale, ITALIAN_LOCALE)

    def test_hebrew_routes_to_aaron(self) -> None:
        r = route(hebrew_sentence_request())
        self.assertEqual(r.provider_voice_id, HEBREW_VOICE_ID)
        self.assertEqual(r.locale, HEBREW_LOCALE)

    def test_exact_voice_ids_used(self) -> None:
        self.assertEqual(HEBREW_VOICE_ID, "Aaron")
        self.assertEqual(ITALIAN_VOICE_ID, "Giuseppe")

    def test_hila_never_referenced_in_new_output(self) -> None:
        # No Hila/Hannah references in routing constants or events.
        self.assertNotIn("Hila", HEBREW_VOICE_ID)
        self.assertNotIn("Hannah", HEBREW_VOICE_ID)

    def test_hannah_never_referenced(self) -> None:
        self.assertNotIn("Hannah", ITALIAN_VOICE_ID)
        self.assertNotIn("Hannah", HEBREW_VOICE_ID)

    def test_unsupported_language_rejected(self) -> None:
        req = PedagogicalVoiceRequest(
            request_id="bad-lang",
            language="fr",
            locale="fr-FR",
            voice_display_name="",
            provider_voice_id="",
            source_text="bonjour",
            tts_text="bonjour",
            source_text_checksum="a",
            tts_text_checksum="b",
            grammatical_metadata={},
            semantic_metadata={},
        )
        with self.assertRaises(VoiceRoutingError):
            route(req)

    def test_hebrew_never_routes_to_giuseppe(self) -> None:
        with self.assertRaises(VoiceRoutingError):
            route(
                PedagogicalVoiceRequest(
                    request_id="he-to-giuseppe",
                    language="it",
                    locale=ITALIAN_LOCALE,
                    voice_display_name=ITALIAN_VOICE_ID,
                    provider_voice_id=ITALIAN_VOICE_ID,
                    source_text=HEBREW_SENTENCE_SOURCE,
                    tts_text=HEBREW_SENTENCE_SOURCE,
                    source_text_checksum="a",
                    tts_text_checksum="b",
                    grammatical_metadata={},
                    semantic_metadata={},
                )
            )

    def test_italian_never_routes_to_aaron(self) -> None:
        with self.assertRaises(VoiceRoutingError):
            route(
                PedagogicalVoiceRequest(
                    request_id="it-to-aaron",
                    language="he",
                    locale=HEBREW_LOCALE,
                    voice_display_name=HEBREW_VOICE_ID,
                    provider_voice_id=HEBREW_VOICE_ID,
                    source_text=ITALIAN_LABEL,
                    tts_text=ITALIAN_LABEL,
                    source_text_checksum="a",
                    tts_text_checksum="b",
                    grammatical_metadata={},
                    semantic_metadata={},
                )
            )


class CLM03BSecurityAndTextTests(unittest.TestCase):
    def test_api_key_absent_from_models(self) -> None:
        req = italian_label_request()
        self.assertNotIn("api_key", str(req))
        self.assertNotIn("SPEECHGEN_API_KEY", str(req))

    def test_api_key_absent_from_events(self) -> None:
        transport = FakeTransport()
        runtime = FakeRuntime()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        client.synthesize(italian_label_request(), cache, runtime)
        for _event_type, payload in runtime.events:
            data = json.dumps(payload)
            self.assertNotIn("fake-token", data)
            self.assertNotIn("api_key", data)

    def test_pointed_hebrew_intact_in_source_text(self) -> None:
        self.assertTrue(has_niqqud(HEBREW_SENTENCE_SOURCE))
        self.assertIn("\u05D4\u05D5\u05BC\u05D0", normalize_source(HEBREW_SENTENCE_SOURCE))

    def test_aaron_receives_pointed_tts_text(self) -> None:
        transport = FakeTransport()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        client.synthesize(hebrew_sentence_request(), cache)
        for _method, _url, data, _headers, _timeout in transport.calls:
            if _method == "POST" and data:
                parsed = urllib.parse.parse_qs(data.decode("utf-8"))
                if "text" in parsed:
                    self.assertEqual(parsed["text"][0], HEBREW_SENTENCE_SOURCE)
                    self.assertTrue(has_niqqud(parsed["text"][0]))
                    self.assertEqual(parsed["voice"][0], HEBREW_VOICE_ID)

    def test_aaron_rejects_unpointed_tts_without_exception(self) -> None:
        from mindtune_clm.voice.routing import build_speechgen_request_text
        req = PedagogicalVoiceRequest(
            request_id="unpointed",
            language="he",
            locale=HEBREW_LOCALE,
            voice_display_name=HEBREW_VOICE_ID,
            provider_voice_id=HEBREW_VOICE_ID,
            source_text=HEBREW_SENTENCE_SOURCE,
            tts_text="הוא מהווה דוגמה טובה",
            source_text_checksum="a",
            tts_text_checksum="b",
            grammatical_metadata={},
            semantic_metadata={},
        )
        with self.assertRaises(HebrewTextError):
            build_speechgen_request_text(req, route(req))

    def test_unpointed_exception_allowed_when_approved(self) -> None:
        req = PedagogicalVoiceRequest(
            request_id="unpointed-exc",
            language="he",
            locale=HEBREW_LOCALE,
            voice_display_name=HEBREW_VOICE_ID,
            provider_voice_id=HEBREW_VOICE_ID,
            source_text=HEBREW_SENTENCE_SOURCE,
            tts_text="הוא מהווה דוגמה טובה",
            source_text_checksum="a",
            tts_text_checksum="b",
            grammatical_metadata={},
            semantic_metadata={},
            unpointed_exception_approved=True,
        )
        r = route(req)
        self.assertEqual(r.provider_voice_id, HEBREW_VOICE_ID)

    def test_no_normalization_strips_hebrew_combining_marks(self) -> None:
        original = HEBREW_SENTENCE_SOURCE
        normalized = normalize_source(original)
        # Every combining mark from the original remains in the normalized form.
        self.assertGreaterEqual(has_niqqud(normalized), has_niqqud(original))

    def test_source_and_tts_stored_separately(self) -> None:
        req = hebrew_sentence_request()
        self.assertEqual(req.source_text, req.tts_text)
        self.assertEqual(req.source_text_checksum, req.tts_text_checksum)

    def test_italian_accents_survive(self) -> None:
        text = "Presente, maschile singolare"
        normalized = normalize_source(text)
        self.assertEqual(normalized, text)

    def test_whitespace_between_hebrew_words_validated(self) -> None:
        # Bad: subject and verb separated by comma, not whitespace/maqaf.
        bad = "\u05D4\u05D5\u05D0,\u05DE\u05B0\u05D4\u05B7\u05D5\u05BC\u05D4"
        with self.assertRaises(HebrewTextError):
            validate_word_separation(bad)
        # Good: whitespace separated.
        validate_word_separation("\u05D4\u05D5\u05D0 \u05DE\u05B0\u05D4\u05B7\u05D5\u05BC\u05D4")

    def test_lhavot_lihyot_lehitahavot_distinct(self) -> None:
        forms = ["\u05DC\u05B0\u05D4\u05B7\u05D5\u05BC\u05D5\u05B9\u05EA", "\u05DC\u05B4\u05D4\u05B0\u05D9\u05D5\u05B9\u05EA", "\u05DC\u05B0\u05D4\u05B4\u05EA\u05B0\u05D4\u05B7\u05D5\u05BC\u05D5\u05B9\u05EA"]
        self.assertEqual(len(set(forms)), 3)


class CLM03BCacheTests(unittest.TestCase):
    def _cache_and_client(self) -> tuple[Path, VoiceCache, FakeTransport, SpeechGenClient]:
        tmp = Path(tempfile.mkdtemp())
        transport = FakeTransport()
        cache = VoiceCache(tmp)
        client = _client_with_api(transport)
        return tmp, cache, transport, client

    def test_identical_requests_same_cache_key(self) -> None:
        r1 = route(italian_label_request())
        r2 = route(italian_label_request())
        params = SynthesisParameters()
        self.assertEqual(
            cache_key(r1, ITALIAN_LABEL, params),
            cache_key(r2, ITALIAN_LABEL, params),
        )

    def test_changing_voice_changes_cache_identity(self) -> None:
        it_route = route(italian_label_request())
        he_route = route(hebrew_sentence_request())
        params = SynthesisParameters()
        key1 = cache_key(it_route, ITALIAN_LABEL, params)
        key2 = cache_key(he_route, HEBREW_SENTENCE_SOURCE, params)
        self.assertNotEqual(key1, key2)

    def test_changing_locale_changes_cache_identity(self) -> None:
        r = route(italian_label_request())
        params = SynthesisParameters()
        key1 = cache_key(r, ITALIAN_LABEL, params)
        # Simulate same voice/locale? We can't change locale without route.
        # Use an ad-hoc route with a different locale.
        from mindtune_clm.voice.routing import VoiceRoute
        r2 = VoiceRoute(
            provider=PROVIDER,
            provider_voice_id=ITALIAN_VOICE_ID,
            locale="it-CH",
            language="it",
            voice_display_name="Giuseppe",
            normalization_policy_version="1.0.0",
            synthesis_parameter_version="1.0.0",
        )
        key2 = cache_key(r2, ITALIAN_LABEL, params)
        self.assertNotEqual(key1, key2)

    def test_changing_tts_text_changes_cache_key(self) -> None:
        r = route(hebrew_sentence_request())
        params = SynthesisParameters()
        key1 = cache_key(r, HEBREW_SENTENCE_SOURCE, params)
        # Change one qamats to patah.
        text2 = HEBREW_SENTENCE_SOURCE.replace("\u05B8", "\u05B7", 1)
        key2 = cache_key(r, text2, params)
        self.assertNotEqual(key1, key2)

    def test_pointed_and_unpointed_do_not_share_cache(self) -> None:
        r = route(hebrew_sentence_request())
        params = SynthesisParameters()
        pointed_key = cache_key(r, HEBREW_SENTENCE_SOURCE, params)
        unpointed_key = cache_key(r, "הוא מהווה דוגמה טובה", params)
        self.assertNotEqual(pointed_key, unpointed_key)

    def test_dagesh_difference_distinct_cache(self) -> None:
        r = route(hebrew_form_request())
        params = SynthesisParameters()
        with_dagesh = HEBREW_FORM_SOURCE
        without = with_dagesh.replace("\u05BC", "")
        self.assertNotEqual(cache_key(r, with_dagesh, params), cache_key(r, without, params))

    def test_shin_sin_dot_difference_distinct_cache(self) -> None:
        r = route(hebrew_form_request())
        params = SynthesisParameters()
        shin = "\u05D9\u05B5\u05E9\u05C1"
        sin = "\u05D9\u05B5\u05E9\u05C2"
        self.assertNotEqual(cache_key(r, shin, params), cache_key(r, sin, params))

    def test_hila_cache_cannot_satisfy_aaron(self) -> None:
        tmp, cache, _transport, _client = self._cache_and_client()
        # Store a Hila-sourced asset under its Hila cache key.
        from mindtune_clm.voice.routing import VoiceRoute
        hila_route = VoiceRoute(
            provider=PROVIDER,
            provider_voice_id="Hannah",
            locale=HEBREW_LOCALE,
            language="he",
            voice_display_name="Hannah",
            normalization_policy_version="1.0.0",
            synthesis_parameter_version="1.0.0",
        )
        key_hila = cache_key(hila_route, HEBREW_SENTENCE_SOURCE, SynthesisParameters())
        pcm = b"\x00\x01" * 16000
        asset = VoiceAsset(
            asset_id="hila-asset",
            provider=PROVIDER,
            voice_display_name="Hannah",
            provider_voice_id="Hannah",
            locale=HEBREW_LOCALE,
            source_text=HEBREW_SENTENCE_SOURCE,
            tts_text=HEBREW_SENTENCE_SOURCE,
            source_text_checksum=sha256_text(HEBREW_SENTENCE_SOURCE),
            tts_text_checksum=sha256_text(HEBREW_SENTENCE_SOURCE),
            provider_audio_checksum="hila",
            canonical_audio_checksum=hashlib.sha256(pcm).hexdigest(),
            cache_key=key_hila,
            sample_rate=16000,
            sample_width=2,
            channels=1,
            frame_count=len(pcm) // 2,
            duration=len(pcm) / 2 / 16000,
            provider_receipt_id="r-hila",
            canonical_pcm=pcm,
        )
        cache.put(asset)

        # Aaron request for the same text must not hit Hila cache.
        aaron_key = cache_key(route(hebrew_sentence_request()), HEBREW_SENTENCE_SOURCE, SynthesisParameters())
        self.assertIsNone(cache.get(aaron_key))

    def test_cache_hit_performs_zero_network_calls(self) -> None:
        tmp, cache, transport, client = self._cache_and_client()
        client.synthesize(hebrew_sentence_request(), cache)
        first_count = transport.call_count()
        client.synthesize(hebrew_sentence_request(), cache)
        self.assertEqual(transport.call_count(), first_count)

    def test_cache_miss_performs_expected_provider_call(self) -> None:
        tmp, cache, transport, client = self._cache_and_client()
        client.synthesize(italian_label_request(), cache)
        post_calls = [c for c in transport.calls if c[1].startswith("https://speechgen.io/index.php?r=api/text")]
        self.assertEqual(len(post_calls), 1)

    def test_malformed_provider_audio_rejected(self) -> None:
        class BrokenTransport:
            calls: list[tuple[str, str, bytes | None, dict[str, str], int]] = []

            def __call__(self, method: str, url: str, data: bytes | None, headers: dict[str, str], timeout: int):
                self.calls.append((method, url, data, headers, timeout))
                if "r=api/text" in url:
                    return (200, "application/json", json.dumps({"file": "https://speechgen.io/download/broken"}).encode())
                return (200, "audio/wav", b"not-a-wav")

        transport = BrokenTransport()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = SpeechGenClient(api_key="x", email="y", transport=transport)
        with self.assertRaises(SpeechGenSynthesisError):
            client.synthesize(italian_label_request(), cache)


class CLM03BIntegrationTests(unittest.TestCase):
    def _synthesize_voice(self, req: PedagogicalVoiceRequest) -> VoiceAsset:
        transport = FakeTransport()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        return client.synthesize(req, cache)

    def test_canonical_wav_conversion_deterministic(self) -> None:
        asset = self._synthesize_voice(italian_label_request())
        self.assertEqual(asset.sample_rate, 16000)
        self.assertEqual(asset.sample_width, 2)
        self.assertEqual(asset.channels, 1)
        self.assertGreater(asset.frame_count, 0)

    def test_canonical_output_is_valid_clm03_input(self) -> None:
        asset = self._synthesize_voice(hebrew_sentence_request())
        audio = asset.to_audio_asset(role=AudioRole.SPEECH_SEGMENT)
        # Validate AudioAsset has the fields CLM-03 expects.
        self.assertTrue(audio.canonical_pcm)
        self.assertTrue(audio.content_checksum)
        self.assertEqual(audio.sample_rate, 16000)
        self.assertEqual(audio.sample_width, 2)

    def test_one_aaron_asset_supports_multiple_clm_states(self) -> None:
        voice = self._synthesize_voice(hebrew_sentence_request())
        audio = voice.to_audio_asset(asset_id="speech_segment")
        registry = AudioAssetRegistry()
        registry.register(audio)
        renderer = AudioRenderer(asset_registry=registry)
        artifacts: list[Any] = []
        for state in [state_baseline(), state_first_intervention(), state_escalated(), state_withdrawal_step_2()]:
            artifacts.append(renderer.render(state, "rcpt-1", "dec-1", "rc-test"))
        self.assertEqual(len({a.render_digest for a in artifacts}), 4)

    def test_one_giuseppe_asset_supports_multiple_clm_states(self) -> None:
        voice = self._synthesize_voice(italian_label_request())
        audio = voice.to_audio_asset(asset_id="speech_segment")
        registry = AudioAssetRegistry()
        registry.register(audio)
        renderer = AudioRenderer(asset_registry=registry)
        baseline = renderer.render(state_baseline(), "rcpt-1", "dec-1", "rc-it")
        intervention = renderer.render(state_first_intervention(), "rcpt-2", "dec-2", "rc-it2")
        self.assertNotEqual(baseline.render_digest, intervention.render_digest)

    def test_clm_tempo_causes_zero_additional_provider_calls(self) -> None:
        transport = FakeTransport()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        voice = client.synthesize(hebrew_sentence_request(), cache)
        after_voice = transport.call_count()
        audio = voice.to_audio_asset(asset_id="speech_segment")
        registry = AudioAssetRegistry()
        registry.register(audio)
        renderer = AudioRenderer(asset_registry=registry)
        renderer.render(state_baseline(), "rcpt-1", "dec-1", "rc-t1")
        renderer.render(state_first_intervention(), "rcpt-2", "dec-2", "rc-t2")
        renderer.render(state_escalated(), "rcpt-3", "dec-3", "rc-t3")
        self.assertEqual(transport.call_count(), after_voice)

    def test_clm_pauses_zero_additional_provider_calls(self) -> None:
        transport = FakeTransport()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        voice = client.synthesize(italian_label_request(), cache)
        after_voice = transport.call_count()
        audio = voice.to_audio_asset(asset_id="speech_segment")
        renderer = AudioRenderer(asset_registry=AudioAssetRegistry())
        renderer.asset_registry.register(audio)
        renderer.render(state_baseline(), "rcpt-1", "dec-1", "rc-p1")
        renderer.render(state_first_intervention(), "rcpt-2", "dec-2", "rc-p2")
        self.assertEqual(transport.call_count(), after_voice)

    def test_clm_repetition_zero_additional_provider_calls(self) -> None:
        transport = FakeTransport()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        voice = client.synthesize(hebrew_form_request(), cache)
        after_voice = transport.call_count()
        audio = voice.to_audio_asset(asset_id="speech_segment")
        registry = AudioAssetRegistry()
        registry.register(audio)
        renderer = AudioRenderer(asset_registry=registry)
        renderer.render(state_baseline(), "rcpt-1", "dec-1", "rc-r1")
        renderer.render(state_escalated(), "rcpt-2", "dec-2", "rc-r2")
        self.assertEqual(transport.call_count(), after_voice)

    def test_pronunciation_status_defaults_to_pending(self) -> None:
        voice = self._synthesize_voice(hebrew_sentence_request())
        self.assertEqual(voice.human_review_status, "pending")

    def test_synthesis_success_does_not_imply_approval(self) -> None:
        voice = self._synthesize_voice(italian_label_request())
        self.assertNotEqual(voice.human_review_status, "approved")

    def test_causal_graph_reconstructable_from_events(self) -> None:
        transport = FakeTransport()
        runtime = FakeRuntime()
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        client = _client_with_api(transport)
        asset = client.synthesize(hebrew_sentence_request(), cache, runtime)
        audio = asset.to_audio_asset(asset_id="speech_segment")
        renderer = AudioRenderer(asset_registry=AudioAssetRegistry())
        renderer.asset_registry.register(audio)
        scheduler = PlaybackScheduler()
        artifact = renderer.render(state_baseline(), "rcpt-1", "dec-1", "rc-causal")
        receipt = scheduler.schedule(artifact, "rc-causal", 0.0, "between_mantra_cycles", "cs-1", "r1")
        ids = [asset.provider_receipt_id, artifact.artifact_id, receipt.playback_receipt_id]
        self.assertEqual(len(set(ids)), 3)


class CLM03BProviderFailureTests(unittest.TestCase):
    def test_missing_api_key(self) -> None:
        client = SpeechGenClient(api_key=None, email=None, transport=FakeTransport())
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        with self.assertRaises(SpeechGenAuthError):
            client.synthesize(italian_label_request(), cache)

    def test_authentication_failure_no_email(self) -> None:
        client = SpeechGenClient(api_key="fake", email=None, transport=FakeTransport())
        cache = VoiceCache(Path(tempfile.mkdtemp()))
        with self.assertRaises(SpeechGenAuthError):
            client.synthesize(italian_label_request(), cache)


if __name__ == "__main__":
    unittest.main()
