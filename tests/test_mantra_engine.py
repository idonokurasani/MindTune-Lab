"""Automated tests for the MindTune Mantra Engine Phase 1 implementation."""
from __future__ import annotations

import os
import shutil
import tempfile
import unicodedata
import unittest
import wave
from pathlib import Path

from mantra.phase1.adaptation import AdaptationBoundary, AdaptationCommand, AdaptationError
from mantra.phase1.assembly import assemble_audio
from mantra.phase1.events import EventEmitter, MantraEventType
from mantra.phase1.fixtures import load_fixture_001_lichtov
from mantra.phase1.manifest import write_manifest
from mantra.phase1.playback import NullAudioPlayer, PlaybackController
from mantra.phase1.spec import (
    GrammaticalGroup,
    MantraForm,
    MantraSpecification,
    PauseConfig,
    SpeechConfig,
)
from mantra.phase1.timeline import SegmentType, compile_timeline
from mantra.phase1.tts import (
    FakeTTSProvider,
    SpeechGenTTSProvider,
    TTSCache,
    TTSRuntimeError,
    _cache_key,
)


class FaultyTTSProvider:
    """Test double that always fails synthesis."""

    name = "faulty"

    def synthesize(self, segment):
        raise TTSRuntimeError("Intentional synthesis failure")


class MantraSpecTests(unittest.TestCase):
    def test_valid_spec_from_fixture(self) -> None:
        spec = load_fixture_001_lichtov()
        self.assertEqual(spec.id, "mantra-001-lichtov")
        self.assertEqual(spec.language, "he-IL")
        self.assertEqual(spec.verb_id, "lichtov")
        self.assertTrue(spec.groups)

    def test_invalid_spec_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MantraSpecification(
                id="",
                version="1.0.0",
                language="he-IL",
                verb_id="x",
                hebrew_infinitive="לִכְתֹּב",
                lexical_root="כ-ת-ב",
                binyan="PA'AL",
                groups=[],
            )

        with self.assertRaises(ValueError):
            MantraSpecification(
                id="x",
                version="1.0.0",
                language="he-IL",
                verb_id="x",
                hebrew_infinitive="לִכְתֹּב",
                lexical_root="",
                binyan="",
                groups=[self._group()],
                repetitions_per_form=-1,
            )

    def test_unicode_normalization_deterministic(self) -> None:
        # Two different representations of the same Hebrew text;
        # normalization must collapse them to the same canonical form.
        decomposed = "\u05db\u05bc\u05b9\u05ea\u05b5\u05d1"
        precomposed = unicodedata.normalize("NFC", decomposed)
        spec = MantraSpecification(
            id="norm",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive=decomposed,
            lexical_root="",
            binyan="",
            groups=[self._group(precomposed)],
        )
        self.assertEqual(spec.hebrew_infinitive, precomposed)
        self.assertEqual(spec.groups[0].forms[0].hebrew_with_niqqud, precomposed)

    def test_niqqud_preserved(self) -> None:
        spec = load_fixture_001_lichtov()
        for group in spec.groups:
            for form in group.forms:
                # Niqqud are in the Hebrew marks range U+0591..U+05C7.
                has_niqqud = any("\u0591" <= c <= "\u05c7" for c in form.hebrew_with_niqqud)
                self.assertTrue(has_niqqud, f"No niqqud preserved in {form.hebrew_with_niqqud!r}")
                self.assertNotEqual(form.hebrew_with_niqqud, form.hebrew_plain)

    def test_manual_pronunciation_and_stress_override_preserved(self) -> None:
        form = MantraForm(
            form_key="test",
            hebrew_with_niqqud="שָׁלוֹם",
            pronunciation_override="ʃaˈlom",
            stress_override=2,
        )
        self.assertEqual(form.effective_tts_input(), "ʃaˈlom")
        self.assertEqual(form.effective_stress(), 2)

    @staticmethod
    def _group(text: str = "לִכְתֹּב") -> GrammaticalGroup:
        return GrammaticalGroup(
            tense="infinitive",
            forms=[
                MantraForm(
                    form_key="infinitive",
                    hebrew_with_niqqud=text,
                    italian_gloss="scrivere",
                )
            ],
        )


class TimelineTests(unittest.TestCase):
    def test_same_spec_same_timeline(self) -> None:
        spec = load_fixture_001_lichtov()
        t1 = compile_timeline(spec)
        t2 = compile_timeline(spec)
        self.assertEqual([s.segment_id for s in t1], [s.segment_id for s in t2])
        self.assertEqual([s.planned_start_time for s in t1], [s.planned_start_time for s in t2])

    def test_stable_segment_identity(self) -> None:
        spec = load_fixture_001_lichtov()
        timeline = compile_timeline(spec)
        for seg in timeline:
            self.assertTrue(seg.segment_id)
            self.assertEqual(seg.segment_id, seg.segment_id)

    def test_pause_durations_exact(self) -> None:
        spec = load_fixture_001_lichtov()
        timeline = compile_timeline(spec)
        for seg in timeline:
            if seg.segment_type == SegmentType.OPENING_SILENCE:
                self.assertEqual(seg.planned_duration, spec.pauses.opening_ms / 1000.0)
            elif seg.segment_type == SegmentType.CLOSING_SILENCE:
                self.assertEqual(seg.planned_duration, spec.pauses.closing_ms / 1000.0)
            elif seg.segment_type == SegmentType.INTER_FORM_SILENCE:
                self.assertEqual(seg.planned_duration, spec.pauses.between_forms_ms / 1000.0)
            elif seg.segment_type == SegmentType.GROUP_PAUSE:
                self.assertEqual(seg.planned_duration, spec.pauses.between_groups_ms / 1000.0)

    def test_repetition_and_cycle_counts_exact(self) -> None:
        spec = MantraSpecification(
            id="rep",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive="לִכְתֹּב",
            lexical_root="",
            binyan="",
            groups=[
                GrammaticalGroup(
                    tense="present",
                    forms=[
                        MantraForm(form_key="ms", hebrew_with_niqqud="כּוֹתֵב", italian_gloss="io scrivo")
                    ],
                )
            ],
            repetitions_per_form=2,
            repetitions_per_cycle=1,
            cycles=2,
            pauses=PauseConfig(
                opening_ms=0,
                closing_ms=0,
                between_forms_ms=0,
                between_groups_ms=0,
                between_cycles_ms=0,
                segment_pause_ms=0,
                italian_cue_pause_ms=0,
            ),
            include_italian_cue=False,
        )
        timeline = compile_timeline(spec)
        hebrew_forms = [s for s in timeline if s.segment_type == SegmentType.HEBREW_FORM]
        self.assertEqual(len(hebrew_forms), 2 * 2 * 1)  # cycles * reps * forms


class TTSTests(unittest.TestCase):
    def test_cache_keys_deterministic(self) -> None:
        k1 = _cache_key("שָׁלוֹם", "speechgen", "Avri", 0.85, 0.0, "wav", None, locale="he-IL")
        k2 = _cache_key("שָׁלוֹם", "speechgen", "Avri", 0.85, 0.0, "wav", None, locale="he-IL")
        self.assertEqual(k1, k2)

    def test_cache_reuse(self) -> None:
        spec = MantraSpecification(
            id="cache",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive="לִכְתֹּב",
            lexical_root="",
            binyan="",
            speech=SpeechConfig(provider="fake", voice="fake"),
            groups=[
                GrammaticalGroup(
                    tense="infinitive",
                    forms=[MantraForm(form_key="inf", hebrew_with_niqqud="שָׁלוֹם")],
                )
            ],
        )
        timeline = compile_timeline(spec)
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            cache_dir = Path(td) / "cache"
            provider = FakeTTSProvider()
            assemble_audio(spec, timeline, provider, out, cache_dir=cache_dir)
            cache = TTSCache(cache_dir)
            key = _cache_key("שָׁלוֹם", "fake", "fake", 1.0, 0.0, "wav", None, locale="he-IL")
            self.assertIsNotNone(cache.get(key))

    def test_failed_synthesis_detected(self) -> None:
        spec = MantraSpecification(
            id="fail",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive="לִכְתֹּב",
            lexical_root="",
            binyan="",
            groups=[
                GrammaticalGroup(
                    tense="infinitive",
                    forms=[MantraForm(form_key="inf", hebrew_with_niqqud="שָׁלוֹם")],
                )
            ],
            pauses=PauseConfig(opening_ms=0, closing_ms=0),
        )
        timeline = compile_timeline(spec)
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            with self.assertRaises(TTSRuntimeError):
                assemble_audio(spec, timeline, FaultyTTSProvider(), out)

    def test_speechgen_requires_credentials(self) -> None:
        # Ensure no credentials leak from the environment for this test.
        env_backup = {
            k: os.environ.pop(k, None)
            for k in ("SPEECHGEN_API_KEY", "SPEECHGEN_TOKEN", "SPEECHGEN_EMAIL")
        }
        try:
            provider = SpeechGenTTSProvider()
            with self.assertRaises(TTSRuntimeError) as ctx:
                # synthesize should fail before any network call
                from mantra.phase1.timeline import TimelineSegment

                segment = TimelineSegment(
                    segment_id="test",
                    segment_type=SegmentType.HEBREW_FORM,
                    source_text="שָׁלוֹם",
                    vocalized_text="שָׁלוֹם",
                    grammatical_metadata={},
                    repetition_index=0,
                    cycle_index=0,
                    group_index=0,
                    form_index=0,
                    planned_start_time=0.0,
                    planned_duration=1.0,
                    provider="speechgen",
                    voice="Avri",
                )
                provider.synthesize(segment)
            msg = str(ctx.exception)
            self.assertIn("SPEECHGEN_API_KEY", msg)
            self.assertIn("SPEECHGEN_EMAIL", msg)
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v


class AssemblyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_audio_assembly_follows_timeline_order(self) -> None:
        spec = load_fixture_001_lichtov()
        timeline = compile_timeline(spec)
        provider = FakeTTSProvider()
        assembly = assemble_audio(spec, timeline, provider, self.tmp / "out")
        self.assertTrue(assembly.output_path.exists())
        with wave.open(str(assembly.output_path), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertGreater(wf.getnframes(), 0)
        expected_duration = sum(s.actual_duration or 0 for s in timeline)
        with wave.open(str(assembly.output_path), "rb") as wf:
            actual_duration = wf.getnframes() / wf.getframerate()
        self.assertAlmostEqual(actual_duration, expected_duration, places=3)

    def test_manifest_matches_artifact(self) -> None:
        spec = load_fixture_001_lichtov()
        timeline = compile_timeline(spec)
        events = EventEmitter()
        provider = FakeTTSProvider()
        out_dir = self.tmp / "out"
        assembly = assemble_audio(spec, timeline, provider, out_dir, events=events)
        cache_dir = out_dir / "cache"
        manifest_path = write_manifest(spec, timeline, assembly, events, out_dir, cache_dir)
        self.assertTrue(manifest_path.exists())
        import json

        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(raw["status"], "completed")
        self.assertTrue(raw["validation_results"]["artifact_exists"])
        self.assertEqual(raw["actual_duration"], assembly.total_duration)

    def test_build_events_emitted_in_order(self) -> None:
        spec = MantraSpecification(
            id="events",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive="לִכְתֹּב",
            lexical_root="",
            binyan="",
            groups=[
                GrammaticalGroup(
                    tense="infinitive",
                    forms=[MantraForm(form_key="inf", hebrew_with_niqqud="שָׁלוֹם")],
                )
            ],
            pauses=PauseConfig(opening_ms=0, closing_ms=0),
        )
        timeline = compile_timeline(spec)
        events = EventEmitter()
        assemble_audio(spec, timeline, FakeTTSProvider(), self.tmp / "out", events=events)
        types = [e.event_type for e in events.events]
        self.assertIn(MantraEventType.AUDIO_ASSEMBLED, types)
        self.assertIn(MantraEventType.SEGMENT_REQUESTED, types)
        self.assertIn(MantraEventType.SEGMENT_GENERATED, types)


class PlaybackTests(unittest.TestCase):
    def test_playback_emits_segment_events(self) -> None:
        spec = MantraSpecification(
            id="play",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive="לִכְתֹּב",
            lexical_root="",
            binyan="",
            groups=[
                GrammaticalGroup(
                    tense="infinitive",
                    forms=[
                        MantraForm(form_key="inf", hebrew_with_niqqud="שָׁלוֹם", italian_gloss="pace")
                    ],
                )
            ],
            pauses=PauseConfig(opening_ms=10, closing_ms=10),
        )
        timeline = compile_timeline(spec)
        events = EventEmitter()
        out_dir = Path(tempfile.mkdtemp())
        try:
            assemble_audio(spec, timeline, FakeTTSProvider(base_duration=0.001), out_dir, events=EventEmitter())
            controller = PlaybackController(
                timeline,
                out_dir / "segments",
                NullAudioPlayer(),
                events,
                sleep_fn=lambda x: None,
            )
            controller.start()
            controller.wait_until_complete(timeout=5)
            types = [e.event_type for e in events.events]
            self.assertIn(MantraEventType.PLAYBACK_STARTED, types)
            self.assertIn(MantraEventType.SEGMENT_STARTED, types)
            self.assertIn(MantraEventType.SEGMENT_COMPLETED, types)
            self.assertIn(MantraEventType.PLAYBACK_COMPLETED, types)
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_pause_resume_stop(self) -> None:
        spec = MantraSpecification(
            id="play2",
            version="1.0.0",
            language="he-IL",
            verb_id="x",
            hebrew_infinitive="לִכְתֹּב",
            lexical_root="",
            binyan="",
            groups=[
                GrammaticalGroup(
                    tense="infinitive",
                    forms=[
                        MantraForm(form_key="inf", hebrew_with_niqqud="שָׁלוֹם", italian_gloss="pace")
                    ],
                )
            ],
            pauses=PauseConfig(opening_ms=10, closing_ms=10),
        )
        timeline = compile_timeline(spec)
        events = EventEmitter()
        out_dir = Path(tempfile.mkdtemp())
        try:
            assemble_audio(spec, timeline, FakeTTSProvider(base_duration=0.001), out_dir, events=EventEmitter())
            controller = PlaybackController(
                timeline,
                out_dir / "segments",
                NullAudioPlayer(),
                events,
                sleep_fn=lambda x: None,
            )
            controller.start()
            controller.pause()
            self.assertTrue(controller.state.paused)
            controller.resume()
            self.assertFalse(controller.state.paused)
            controller.stop()
            self.assertTrue(controller.state.stopped)
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)


class AdaptationTests(unittest.TestCase):
    def test_unsupported_command_rejected(self) -> None:
        boundary = AdaptationBoundary()
        with self.assertRaises(AdaptationError):
            boundary.apply("s1", "m1", "v1", "seg1", "skip_ahead", {"delta_ms": 100}, "reason", "p1")

    def test_out_of_bound_pause_delta_rejected(self) -> None:
        boundary = AdaptationBoundary(max_pause_extension_ms=500)
        with self.assertRaises(AdaptationError):
            boundary.apply(
                "s1",
                "m1",
                "v1",
                "seg1",
                AdaptationCommand.EXTEND_NEXT_PAUSE,
                {"delta_ms": 1000},
                "reason",
                "p1",
            )

    def test_valid_command_accepted(self) -> None:
        boundary = AdaptationBoundary()
        record = boundary.apply(
            "s1",
            "m1",
            "v1",
            "seg1",
            AdaptationCommand.HOLD_PROGRESSION,
            {},
            "eeg window noisy",
            "p1",
        )
        self.assertEqual(record.command, AdaptationCommand.HOLD_PROGRESSION)
        self.assertEqual(record.session_id, "s1")


if __name__ == "__main__":
    unittest.main()
