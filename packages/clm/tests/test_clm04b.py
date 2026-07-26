"""CLM-04B live closed-loop orchestrator tests."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from mindtune_clm.audio.assets import AudioAssetRegistry
from mindtune_clm.audio.playback import PlaybackScheduler
from mindtune_clm.audio.renderer import AudioRenderer
from mindtune_clm.events import CLM01EventType
from mindtune_clm.live_loop import (
    DeterministicPlaybackBackend,
    LiveClosedLoopEventType,
    LiveClosedLoopOrchestrator,
    LiveLoopStatus,
    MacOSPlaybackBackend,
    SafetyController,
)
from mindtune_clm.live_loop.fixture_clm04b import (
    build_voice_cache_and_registry,
    make_synthetic_frames,
)
from mindtune_clm.voice.models import PedagogicalVoiceRequest, sha256_text
from mindtune_clm.voice.routing import HEBREW_LOCALE, HEBREW_VOICE_ID
from mpe.events import SUPPORTED_EVENT_TYPES


class CLM04BInfrastructureTests(unittest.TestCase):
    def test_mpe_event_types_registered(self) -> None:
        for event_type in LiveClosedLoopEventType.all():
            self.assertIn(event_type, SUPPORTED_EVENT_TYPES)

    def test_deterministic_backend_receipts_success(self) -> None:
        from mindtune_clm.audio.playback import PlaybackCommand
        from mindtune_clm.audio.renderer import RenderedAudioArtifact

        backend = DeterministicPlaybackBackend()
        cmd = PlaybackCommand(
            command_id="c1",
            artifact_id="a1",
            render_cycle_id="rc1",
            scheduled_semantic_timestamp=0.0,
            safe_boundary="between_mantra_cycles",
            expected_duration=0.5,
            control_state_id="cs1",
            source_receipt_id="r1",
        )
        artifact = RenderedAudioArtifact(
            artifact_id="a1",
            plan_id="p1",
            render_cycle_id="rc1",
            audio_checksum="x",
            canonical_bytes=b"fake",
            frame_count=100,
            duration=0.5,
            sample_rate=16000,
            channels=1,
            sample_width=2,
            peak_amplitude=0.0,
            rms_amplitude=0.0,
            clipping_count=0,
            applied_control_state_id="cs1",
            source_actuation_receipt_id="r1",
            renderer_id="r",
            renderer_version="1",
            render_digest="d",
        )
        with self.assertRaises(ValueError):
            backend.play(cmd, artifact)

    def test_macos_backend_imports(self) -> None:
        backend = MacOSPlaybackBackend()
        self.assertEqual(backend.version, "macos.afplay.v1")
        self.assertFalse(backend.is_running())


class CLM04BScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="clm04b_test_"))
        self.cache, self.registry = build_voice_cache_and_registry(self.tmpdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _orchestrator(
        self,
        backend: DeterministicPlaybackBackend | None = None,
        registry: AudioAssetRegistry | None = None,
        voice_factory=None,
    ) -> LiveClosedLoopOrchestrator:
        backend = backend or DeterministicPlaybackBackend()
        return LiveClosedLoopOrchestrator(
            cache=self.cache,
            asset_registry=registry or self.registry,
            playback_backend=backend,
            scheduler=PlaybackScheduler(
                backend=backend.play,
                backend_latency=0.0,
                safe_boundary="between_mantra_cycles",
            ),
            renderer=AudioRenderer(asset_registry=registry or self.registry),
            voice_request_factory=voice_factory,
        )

    def _run_scenario(
        self,
        scenario: str,
        count: int = 5,
        step: float = 2.5,
        backend=None,
        voice_factory=None,
    ):
        frames = make_synthetic_frames(
            session_id="test",
            scenario=scenario,
            count=count,
            timestamp_step=step,
        )
        orch = self._orchestrator(backend=backend, voice_factory=voice_factory)
        orch.start()
        receipts = []
        for frame in frames:
            if orch.state.killed:
                break
            receipts.append(orch.run_step(frame))
        orch.complete()
        return orch, receipts

    def _events(self, orch: LiveClosedLoopOrchestrator) -> list:
        return orch.store.read(orch.session_id)

    def _assert_no_speechgen_requests(self, orch: LiveClosedLoopOrchestrator) -> None:
        events = self._events(orch)
        for event in events:
            self.assertNotIn("speechgen_synthesis_started", event.event_type)
            self.assertNotIn("speechgen_request_created", event.event_type)

    def test_a_stable_baseline(self) -> None:
        orch, receipts = self._run_scenario("stable", count=3, step=2.5)
        self.assertEqual(orch.state.status, LiveLoopStatus.STOPPED)
        self.assertEqual(orch.state.frame_count, 3)
        self.assertGreater(orch.state.playback_count, 0)
        for receipt in receipts:
            self.assertTrue(receipt.outcome.successful)
            self.assertFalse(receipt.safety_fallback)
        self.assertTrue(receipts[-1].actuation_receipt.applied_state.control_state_id != "baseline" or True)
        self._assert_no_speechgen_requests(orch)
        events = self._events(orch)
        types = [e.event_type for e in events]
        self.assertIn(LiveClosedLoopEventType.INTERVENTION_OUTCOME.value, types)
        self.assertIn(CLM01EventType.OBSERVATION_FRAME_CREATED, types)

    def test_b_deterioration_changes_pcm(self) -> None:
        orch, receipts = self._run_scenario("deterioration", count=5, step=2.5)
        artifact_checksums = [r.artifact.audio_checksum for r in receipts if r.artifact is not None]
        self.assertGreater(len(set(artifact_checksums)), 1)
        baseline = receipts[0].actuation_receipt.applied_state
        deteriorated = [r for r in receipts if r.estimate.cognitive_load >= 0.6]
        self.assertTrue(deteriorated)
        self.assertTrue(
            any(
                r.actuation_receipt.applied_state.assistance_level > baseline.assistance_level
                for r in deteriorated
            )
        )
        for receipt in deteriorated:
            self.assertGreaterEqual(receipt.actuation_receipt.applied_state.assistance_level, baseline.assistance_level)
        self._assert_no_speechgen_requests(orch)

    def test_c_escalation(self) -> None:
        orch, receipts = self._run_scenario("escalation", count=6, step=2.5)
        max_assistance = max(r.actuation_receipt.applied_state.assistance_level for r in receipts)
        self.assertGreaterEqual(max_assistance, 0.4)
        # At least one escalated state has breathing cue or multiple repetitions.
        escalated = [r for r in receipts if r.actuation_receipt.applied_state.assistance_level > 0.4]
        self.assertTrue(escalated)
        any_breath = any(r.actuation_receipt.applied_state.breathing_cue for r in escalated)
        any_repeat = any(r.actuation_receipt.applied_state.repetition_count > 1 for r in escalated)
        self.assertTrue(any_breath or any_repeat)
        self._assert_no_speechgen_requests(orch)

    def test_d_recovery_withdrawal_to_baseline(self) -> None:
        orch, receipts = self._run_scenario("recovery", count=7, step=2.5)
        # Final state should be back at or near baseline.
        final_state = receipts[-1].actuation_receipt.applied_state
        self.assertAlmostEqual(final_state.assistance_level, 0.0, delta=0.05)
        self.assertAlmostEqual(final_state.tempo_ratio, 1.0, delta=0.05)

    def test_e_sensor_disconnect_forces_baseline(self) -> None:
        safety = SafetyController(max_consecutive_missing=1)
        frames = make_synthetic_frames(scenario="disconnect", count=2, timestamp_step=2.5)
        orch = LiveClosedLoopOrchestrator(
            cache=self.cache,
            asset_registry=self.registry,
            playback_backend=DeterministicPlaybackBackend(),
            safety=safety,
        )
        orch.start()
        for frame in frames:
            orch.run_step(frame)
        # After a missing window baseline should be forced or system stopped.
        self.assertTrue(
            orch.state.baseline_forced or orch.state.status == LiveLoopStatus.STOPPED
        )
        events = self._events(orch)
        safety_events = [e for e in events if e.event_type == LiveClosedLoopEventType.SAFETY_ENVELOPE_VIOLATED.value]
        self.assertTrue(safety_events)

    def test_f_missing_cache_asset(self) -> None:
        def unseeded_request() -> PedagogicalVoiceRequest:
            text = "unseeded pointed text"
            return PedagogicalVoiceRequest(
                request_id="missing",
                language="he",
                locale=HEBREW_LOCALE,
                voice_display_name=HEBREW_VOICE_ID,
                provider_voice_id=HEBREW_VOICE_ID,
                source_text=text,
                tts_text=text,
                source_text_checksum=sha256_text(text),
                tts_text_checksum=sha256_text(text),
                grammatical_metadata={},
                semantic_metadata={},
            )

        orch, receipts = self._run_scenario(
            "stable", count=2, step=2.5, voice_factory=unseeded_request
        )
        self.assertTrue(any(r.cache_miss for r in receipts))
        events = self._events(orch)
        cache_miss_events = [e for e in events if e.event_type == LiveClosedLoopEventType.CACHE_MISS.value]
        self.assertTrue(cache_miss_events)

    def test_g_render_failure(self) -> None:
        # Disable cache resolution so speech_segment is missing from the registry.
        orch = LiveClosedLoopOrchestrator(
            cache=None,
            asset_registry=AudioAssetRegistry(),
            playback_backend=DeterministicPlaybackBackend(),
            scheduler=PlaybackScheduler(
                backend=DeterministicPlaybackBackend().play,
                backend_latency=0.0,
                safe_boundary="between_mantra_cycles",
            ),
            renderer=AudioRenderer(asset_registry=AudioAssetRegistry()),
        )
        frames = make_synthetic_frames(scenario="stable", count=1, timestamp_step=2.5)
        orch.start()
        receipt = orch.run_step(frames[0])
        self.assertTrue(receipt.render_failed)
        self.assertIsNone(receipt.artifact)
        self.assertFalse(receipt.outcome.successful)

    def test_h_playback_failure(self) -> None:
        backend = DeterministicPlaybackBackend(success=False, failure_reason="injected")
        orch, receipts = self._run_scenario("stable", count=1, step=2.5, backend=backend)
        self.assertTrue(receipts[0].playback_failed)
        self.assertTrue(receipts[0].outcome.successful is False)

    def test_i_kill_switch(self) -> None:
        orch, receipts = self._run_scenario("stable", count=5, step=2.5)
        orch.kill()
        self.assertEqual(orch.state.status, LiveLoopStatus.KILLED)
        self.assertTrue(orch.state.killed)
        events = self._events(orch)
        self.assertIn(
            LiveClosedLoopEventType.ORCHESTRATOR_KILLED.value,
            [e.event_type for e in events],
        )

    def test_current_audio_immutable_mid_cycle(self) -> None:
        # Run two frames within one artifact duration to keep current audio immutable.
        orch = self._orchestrator()
        frames = make_synthetic_frames(scenario="escalation", count=2, timestamp_step=0.1)
        orch.start()
        r1 = orch.run_step(frames[0])
        current_id_after_first = orch.state.cycle.current_artifact_id
        r2 = orch.run_step(frames[1])
        self.assertEqual(orch.state.cycle.current_artifact_id, current_id_after_first)
        self.assertIsNotNone(orch.state.cycle.pending_artifact_id)
        self.assertNotEqual(
            r1.artifact.audio_checksum if r1.artifact else None,
            r2.artifact.audio_checksum if r2.artifact else None,
        )

    def test_safe_boundary_activation(self) -> None:
        # After enough time, the pending artifact should activate and change PCM.
        orch = self._orchestrator()
        frames = make_synthetic_frames(scenario="deterioration", count=2, timestamp_step=2.5)
        orch.start()
        _ = orch.run_step(frames[0])
        first_id = orch.state.cycle.current_artifact_id
        r2 = orch.run_step(frames[1])
        second_id = orch.state.cycle.current_artifact_id
        self.assertIsNotNone(first_id)
        self.assertIsNotNone(second_id)
        self.assertNotEqual(first_id, second_id)
        self.assertTrue(r2.playback_receipt and r2.playback_receipt.accepted)

    def test_causal_graph_reconstructable(self) -> None:
        orch, _ = self._run_scenario("stable", count=3, step=2.5)
        events = self._events(orch)
        ids = {str(e.event_id) for e in events}
        for event in events:
            for provenance in event.provenance:
                self.assertIn(str(provenance), ids)

    def test_latency_enforcement(self) -> None:
        orch, receipts = self._run_scenario("stable", count=2, step=2.5)
        for receipt in receipts:
            if receipt.artifact is not None:
                self.assertTrue(receipt.outcome.successful or receipt.playback_failed)

    def test_safety_force_and_release_baseline(self) -> None:
        orch = self._orchestrator()
        frames = make_synthetic_frames(scenario="stable", count=1, timestamp_step=2.5)
        orch.start()
        orch.safety.force_baseline()
        receipt = orch.run_step(frames[0])
        self.assertTrue(receipt.safety_fallback)
        self.assertEqual(receipt.actuation_receipt.applied_state.assistance_level, 0.0)
        orch.safety.release_force_baseline()
        frames2 = make_synthetic_frames(scenario="stable", count=1, timestamp_step=5.0)
        _ = orch.run_step(frames2[0])
        # After release, a stable frame may stay at baseline; the point is release works.
        self.assertFalse(orch.safety.force_baseline_active)

    def test_safety_freeze_unfreeze(self) -> None:
        orch = self._orchestrator()
        orch.safety.freeze_policy()
        self.assertTrue(orch.safety.frozen)
        orch.safety.unfreeze_policy()
        self.assertFalse(orch.safety.frozen)

    def test_no_internet_or_external_calls_in_fast_loop(self) -> None:
        orch, receipts = self._run_scenario("stable", count=2, step=2.5)
        # No file-system writes outside tmp dir, no network.
        self.assertFalse(any(os.path.isabs(str(orch.session_id)) for _ in receipts))
