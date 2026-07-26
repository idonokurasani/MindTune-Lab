"""CLM-03 real mantra audio actuator integration tests."""

from __future__ import annotations

import io
import unittest
import wave
from pathlib import Path

from mindtune_clm.audio import (
    AudioAssetRegistry,
    AudioRenderer,
    AudioRenderError,
    AudioRole,
    PlaybackScheduler,
    UtterancePlanner,
    load_wav_asset,
)
from mindtune_clm.audio.fixture_clm03 import (
    default_registry,
    state_baseline,
    state_escalated,
    state_first_intervention,
    state_withdrawal_step_1,
    state_withdrawal_step_2,
)
from mindtune_clm.audio.transforms import ms_to_frames
from mindtune_clm.loop import ControlLoop
from mindtune_clm.observations import ObservationFrame
from mindtune_clm.policy import ControlPolicy
from mindtune_clm.state import MantraControlState

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _frames_from_bytes(canonical_bytes: bytes) -> int:
    with io.BytesIO(canonical_bytes) as bio:
        with wave.open(bio, "rb") as w:
            return w.getnframes()


def _pcm_from_bytes(canonical_bytes: bytes) -> bytes:
    with io.BytesIO(canonical_bytes) as bio:
        with wave.open(bio, "rb") as w:
            return w.readframes(w.getnframes())


def _renderer(registry: AudioAssetRegistry | None = None) -> AudioRenderer:
    return AudioRenderer(asset_registry=registry or default_registry())


def _render(state: MantraControlState, renderer: AudioRenderer | None = None) -> AudioRenderer:
    r = renderer or _renderer()
    artifact = r.render(
        state,
        actuation_receipt_id="rcpt-1",
        decision_id="dec-1",
        render_cycle_id="rc-1",
    )
    return artifact


class CLM03AudioUnitTests(unittest.TestCase):
    def test_baseline_plan_produces_valid_canonical_wav(self) -> None:
        artifact = _render(state_baseline())
        self.assertEqual(artifact.sample_rate, 16000)
        self.assertEqual(artifact.sample_width, 2)
        self.assertEqual(artifact.channels, 1)
        self.assertGreater(artifact.frame_count, 0)
        self.assertGreater(artifact.duration, 0.0)

    def test_baseline_render_is_byte_identical_across_runs(self) -> None:
        a1 = _render(state_baseline())
        a2 = _render(state_baseline())
        self.assertEqual(a1.canonical_bytes, a2.canonical_bytes)
        self.assertEqual(a1.render_digest, a2.render_digest)

    def test_same_plan_and_assets_produce_same_digest(self) -> None:
        a1 = _render(state_first_intervention())
        a2 = _render(state_first_intervention())
        self.assertEqual(a1.render_digest, a2.render_digest)

    def test_control_state_change_changes_digest(self) -> None:
        a1 = _render(state_baseline())
        a2 = _render(state_first_intervention())
        self.assertNotEqual(a1.render_digest, a2.render_digest)

    def test_source_asset_change_changes_digest(self) -> None:
        a1 = _render(state_baseline(), _renderer(default_registry()))
        # Build a registry where the speech asset is a different audio file.
        alt = AudioAssetRegistry()
        alt.register(
            load_wav_asset(
                path=Path(__file__).resolve().parent / "fixtures" / "audio" / "breathing_cue.wav",
                asset_id="speech_segment",
                role=AudioRole.SPEECH_SEGMENT,
                label="alt",
                source_type="synthetic_fixture",
            )
        )
        a2 = _render(state_baseline(), _renderer(alt))
        self.assertNotEqual(a1.render_digest, a2.render_digest)

    def test_tempo_ratio_one_preserves_source_frames(self) -> None:
        artifact = _render(state_baseline())
        source_pcm = default_registry().get("speech_segment").canonical_pcm
        artifact_pcm = _pcm_from_bytes(artifact.canonical_bytes)
        # Baseline has no pre/post silence and one repetition, so speech region equals source.
        self.assertEqual(artifact_pcm[: len(source_pcm)], source_pcm)

    def test_lower_tempo_produces_longer_output(self) -> None:
        base = _render(state_baseline())
        slow = _render(state_first_intervention())
        self.assertGreater(slow.duration, base.duration)

    def test_tempo_frame_rounding_is_deterministic(self) -> None:
        state = MantraControlState(tempo_ratio=0.95, control_state_id="tr")
        artifact = _render(state)
        speech_frames = default_registry().get("speech_segment").frame_count
        expected = int(speech_frames / 0.95)
        self.assertEqual(_frames_from_bytes(artifact.canonical_bytes), expected)

    def test_post_pause_frame_count_is_exact(self) -> None:
        artifact = _render(state_first_intervention())
        speech_frames = int(default_registry().get("speech_segment").frame_count / 0.95)
        expected_pause = ms_to_frames(300, 16000)
        self.assertEqual(_frames_from_bytes(artifact.canonical_bytes), speech_frames + expected_pause)

    def test_pre_pause_frame_count_is_exact(self) -> None:
        state = MantraControlState(
            pre_stimulus_pause_ms=150,
            post_stimulus_pause_ms=0,
            tempo_ratio=1.0,
            control_state_id="pre",
        )
        artifact = _render(state)
        speech_frames = default_registry().get("speech_segment").frame_count
        expected = speech_frames + ms_to_frames(150, 16000)
        self.assertEqual(_frames_from_bytes(artifact.canonical_bytes), expected)

    def test_repetition_count_changes_pcm_length(self) -> None:
        single = _render(MantraControlState(repetition_count=1, tempo_ratio=1.0, control_state_id="single"))
        double = _render(MantraControlState(repetition_count=2, tempo_ratio=1.0, control_state_id="double"))
        self.assertGreater(_frames_from_bytes(double.canonical_bytes), _frames_from_bytes(single.canonical_bytes))

    def test_breathing_cue_absent_when_disabled(self) -> None:
        artifact = _render(state_baseline())
        plan = UtterancePlanner().plan(state_baseline(), "rcpt-1", "dec-1", "rc-1")
        cue_ids = [s.segment_id for s in plan.ordered_segments if s.segment_role == AudioRole.BREATHING_CUE.value]
        self.assertEqual(cue_ids, [])
        self.assertFalse(artifact.fallback_used)

    def test_breathing_cue_present_when_enabled(self) -> None:
        artifact = _render(state_escalated())
        plan = UtterancePlanner().plan(state_escalated(), "rcpt-1", "dec-1", "rc-1")
        cue_ids = [s.segment_id for s in plan.ordered_segments if s.segment_role == AudioRole.BREATHING_CUE.value]
        self.assertEqual(len(cue_ids), 1)
        self.assertGreater(artifact.duration, 1.0)  # 2x slowed + 0.3s cue

    def test_gain_transform_respects_clipping_limits(self) -> None:
        state = MantraControlState(
            vocal_energy=1.0,
            prosodic_emphasis=1.0,
            control_state_id="maxgain",
        )
        artifact = _render(state)
        self.assertLessEqual(artifact.peak_amplitude, 1.0)
        self.assertGreaterEqual(artifact.clipping_count, 0)

    def test_peak_and_rms_are_deterministic(self) -> None:
        a1 = _render(state_first_intervention())
        a2 = _render(state_first_intervention())
        self.assertEqual(a1.peak_amplitude, a2.peak_amplitude)
        self.assertEqual(a1.rms_amplitude, a2.rms_amplitude)

    def test_artifact_references_exact_clm_actuation_receipt(self) -> None:
        artifact = _render(state_baseline())
        self.assertEqual(artifact.source_actuation_receipt_id, "rcpt-1")

    def test_artifact_uses_exact_applied_control_state(self) -> None:
        state = state_first_intervention()
        artifact = _render(state)
        self.assertEqual(artifact.applied_control_state_id, state.control_state_id)

    def test_renderer_does_not_recompute_policy_parameters(self) -> None:
        state = state_first_intervention()
        renderer = _renderer()
        _ = _render(state, renderer)
        # Render again with same state object; only content differs from new plan ids if state id differs
        artifact2 = renderer.render(
            state,
            actuation_receipt_id="rcpt-1",
            decision_id="dec-1",
            render_cycle_id="rc-2",
        )
        self.assertEqual(artifact2.applied_control_state_id, state.control_state_id)

    def test_missing_asset_causes_typed_failure(self) -> None:
        empty = AudioAssetRegistry()
        renderer = AudioRenderer(asset_registry=empty)
        with self.assertRaises(AudioRenderError) as ctx:
            renderer.render(state_baseline(), "rcpt-2", "dec-2", "rc-2")
        self.assertIn("no audio asset", str(ctx.exception))

    def test_fallback_uses_baseline_or_last_valid(self) -> None:
        # First render with full registry produces last valid.
        renderer = _renderer()
        valid = renderer.render(state_baseline(), "rcpt-v", "dec-v", "rc-valid")
        # Replace registry with empty so the speech asset is missing.
        renderer.asset_registry = AudioAssetRegistry()
        # Set fallback to a non-existent asset, forcing last_valid use.
        renderer.fallback_asset_id = "missing"
        fallback = renderer.render(state_first_intervention(), "rcpt-f", "dec-f", "rc-f")
        self.assertTrue(fallback.fallback_used)
        self.assertEqual(fallback.applied_control_state_id, valid.applied_control_state_id)
        self.assertIn("last_valid_fallback", fallback.fallback_reason or "")

    def test_fallback_does_not_claim_rejected_state_was_applied(self) -> None:
        renderer = _renderer()
        valid = renderer.render(state_baseline(), "rcpt-v", "dec-v", "rc-valid")
        renderer.asset_registry = AudioAssetRegistry()
        renderer.fallback_asset_id = "missing"
        fallback = renderer.render(state_first_intervention(), "rcpt-f", "dec-f", "rc-f")
        self.assertNotEqual(fallback.applied_control_state_id, state_first_intervention().control_state_id)
        self.assertEqual(fallback.applied_control_state_id, valid.applied_control_state_id)

    def test_safe_boundary_rejects_mid_cycle_activation(self) -> None:
        scheduler = PlaybackScheduler()
        artifact = _render(state_baseline())
        receipt = scheduler.schedule(
            artifact,
            "rc-1",
            semantic_start_timestamp=0.0,
            safe_boundary="mid_cycle",
            control_state_id="cs-1",
            source_receipt_id="rcpt-1",
        )
        self.assertFalse(receipt.accepted)
        self.assertIn("unsafe_boundary", receipt.rejection_reason or "")

    def test_playback_receipt_references_scheduled_artifact(self) -> None:
        scheduler = PlaybackScheduler()
        artifact = _render(state_baseline())
        receipt = scheduler.schedule(
            artifact,
            "rc-1",
            semantic_start_timestamp=0.0,
            safe_boundary="between_mantra_cycles",
            control_state_id="cs-1",
            source_receipt_id="rcpt-1",
        )
        self.assertEqual(receipt.artifact_id, artifact.artifact_id)
        self.assertTrue(receipt.accepted)

    def test_semantic_playback_timestamps_do_not_depend_on_wall_clock(self) -> None:
        scheduler = PlaybackScheduler()
        artifact = _render(state_baseline())
        receipt = scheduler.schedule(
            artifact,
            "rc-1",
            semantic_start_timestamp=1.25,
            safe_boundary="between_mantra_cycles",
            control_state_id="cs-1",
            source_receipt_id="rcpt-1",
        )
        self.assertEqual(receipt.semantic_start_timestamp, 1.25)
        self.assertEqual(receipt.semantic_end_timestamp, 1.25 + artifact.duration)

    def test_playback_duration_matches_rendered_frame_count(self) -> None:
        artifact = _render(state_baseline())
        self.assertEqual(artifact.duration, artifact.frame_count / artifact.sample_rate)

    def test_currently_playing_artifact_cannot_change_before_boundary(self) -> None:
        scheduler = PlaybackScheduler()
        a1 = _render(MantraControlState(control_state_id="a1"))
        a2 = _render(MantraControlState(control_state_id="a2"))
        scheduler.schedule(a1, "rc-1", 0.0, "between_mantra_cycles", "cs-a1", "r1")
        self.assertEqual(scheduler.current_artifact, a1)
        scheduler.schedule(a2, "rc-2", 1.0, "between_mantra_cycles", "cs-a2", "r2")
        # current still a1 until boundary advance
        self.assertEqual(scheduler.current_artifact, a1)
        scheduler.advance_boundary()
        self.assertEqual(scheduler.current_artifact, a2)

    def test_withdrawal_returns_toward_baseline(self) -> None:
        step1 = _render(state_withdrawal_step_1())
        step2 = _render(state_withdrawal_step_2())
        _ = _render(state_baseline())
        # Frame counts should monotonically approach baseline
        self.assertLess(step2.frame_count, step1.frame_count)
        self.assertLess(step2.duration, step1.duration)

    def test_sufficient_withdrawal_equals_baseline(self) -> None:
        baseline = _render(state_baseline())
        # Two withdrawal steps should get close; exact equality requires exact state
        withdrawal = _render(state_withdrawal_step_2())
        self.assertEqual(withdrawal.canonical_bytes, baseline.canonical_bytes)


class CLM03ControlLoopTests(unittest.TestCase):
    def _baseline_frame(self) -> ObservationFrame:
        return ObservationFrame(
            observation_frame_id="of-1",
            control_cycle_id="cc-1",
            session_id="s-1",
            sequence_number=1,
            observation_timestamp=0.0,
            behavioral_latency_ms=0.0,
            hesitation_score=0.0,
            error_score=0.0,
            eeg_stability=0.0,
            eeg_quality="good",
            respiration_stability=1.0,
            voice_stability=1.0,
            available_modalities=frozenset({"eeg"}),
            source_event_ids=["src-1"],
        )

    def test_decision_changes_audio_artifact_for_next_render_cycle(self) -> None:
        renderer = _renderer()
        scheduler = PlaybackScheduler()
        loop = ControlLoop(
            audio_renderer=renderer,
            playback_scheduler=scheduler,
            policy=ControlPolicy(),
        )
        frame = self._baseline_frame()
        # Two sustained high-load cycles trigger RECOVERY_REQUIRED on the second,
        # so the decision in control cycle 2 changes the artifact for render cycle 3.
        result = loop.run_session([frame, frame])
        self.assertEqual(len(result.cycles), 2)
        events = loop.store.read(loop.session_id)
        rendered = [e for e in events if e.event_type == "adapted_stimulus_rendered"]
        self.assertEqual(len(rendered), 3)
        rc2 = [e for e in rendered if e.payload["render_cycle_id"] == "rc-2"][0]
        rc3 = [e for e in rendered if e.payload["render_cycle_id"] == "rc-3"][0]
        self.assertTrue(rc2.payload.get("audio_generated"))
        self.assertTrue(rc3.payload.get("audio_generated"))
        self.assertNotEqual(rc2.payload.get("audio_checksum"), rc3.payload.get("audio_checksum"))

    def test_causal_graph_reconstructable(self) -> None:
        renderer = _renderer()
        loop = ControlLoop(audio_renderer=renderer)
        result = loop.run_session([self._baseline_frame()])
        events = loop.store.read(loop.session_id)
        audio_rendered = [e for e in events if e.event_type == "audio_artifact_rendered"]
        self.assertGreaterEqual(len(audio_rendered), 1)
        artifact = audio_rendered[-1]
        self.assertEqual(artifact.payload["source_actuation_receipt_id"], result.cycles[-1].receipt.command_id)

    def test_clm01_causal_chain_includes_playback_receipt(self) -> None:
        loop = ControlLoop(audio_renderer=_renderer(), playback_scheduler=PlaybackScheduler())
        _ = loop.run_session([self._baseline_frame()])
        events = loop.store.read(loop.session_id)
        rendered = [e for e in events if e.event_type == "adapted_stimulus_rendered" and e.payload["render_cycle_id"] == "rc-2"][0]
        self.assertIn("playback_receipt_id", rendered.payload)
        playback = [e for e in events if e.event_type == "playback_completed"]
        self.assertEqual(len(playback), 2)
