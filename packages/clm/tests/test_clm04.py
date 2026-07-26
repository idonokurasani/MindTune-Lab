"""CLM-04 live FC11 sensor gateway tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from mindtune_clm.live import (
    FC11LiveSource,
    LiveClock,
    LiveEventType,
    LiveGateway,
    LiveGatewayResult,
    LiveHealthStatus,
    PacketBuffer,
    SyntheticLiveSource,
)
from mindtune_clm.live.models import LivePacket
from mindtune_clm.loop import ControlLoop
from mindtune_clm.replay.fc11 import (
    FC11CSVParser,
    FC11NormalizationPolicy,
    FC11QualityPolicy,
    load_fc11_source_from_text,
)
from mindtune_clm.replay.features import FeaturePolicy
from mindtune_clm.replay.runner import ReplayRunner
from mindtune_clm.replay.windows import WindowPolicy
from mpe.types import SessionID

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "fc11"
LIVE_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "live_fc11"


def _fc11_fixture(name: str) -> tuple[str, str]:
    csv_path = FIXTURE_ROOT / f"{name}.csv"
    meta_path = FIXTURE_ROOT / f"{name}.json"
    return csv_path.read_text(), meta_path.read_text()


def _replay_result(name: str, **overrides):
    csv_text, meta_text = _fc11_fixture(name)
    source, csv_text, meta_text = load_fc11_source_from_text(
        source_id=f"fc11:{name}",
        fixture_handle=f"{name}.csv",
        csv_text=csv_text,
        metadata_text=meta_text,
        recording_id=f"{name}-anon",
    )
    parser = FC11CSVParser()
    norm = FC11NormalizationPolicy()
    qual = FC11QualityPolicy()
    feat = FeaturePolicy(
        policy_id="fc11_features.v1",
        version="1.0.0",
        primary_channel="eeg_scaled",
        normalization_mode="coefficient_of_variation",
    )
    win = WindowPolicy(
        policy_id="fc11_window.v1",
        version="1.0.0",
        window_duration_s=2.0,
        step_duration_s=1.0,
        min_accepted_sample_count=12,
        partial_final_window=True,
        feature_policy=feat,
    )
    runner = ReplayRunner()
    return runner.run(
        replay_id=f"replay-{name}",
        source=source,
        content=csv_text,
        parser=parser,
        normalization_policy=norm,
        quality_policy=qual,
        window_policy=win,
        clm_policy=None,
    )


def _run_live(csv_text: str, **gateway_kwargs) -> LiveGatewayResult:
    source = FC11LiveSource(csv_text=csv_text, source_id="fc11_live_test")
    gateway = LiveGateway(source=source, **gateway_kwargs)
    return gateway.run()


class LiveSourceAbstractionTests(unittest.TestCase):
    def test_abstract_source_contract(self) -> None:
        src = SyntheticLiveSource(source_id="test", duration=0.5, packet_interval=0.1, seed=1)
        self.assertFalse(src.connected)
        self.assertTrue(src.connect())
        self.assertTrue(src.connected)
        self.assertEqual(src.epoch, 1)
        self.assertEqual(src.reconnect_attempts, 0)

    def test_reconnect_bounds(self) -> None:
        src = SyntheticLiveSource(
            source_id="test",
            duration=0.5,
            packet_interval=0.1,
            seed=1,
            max_reconnect_attempts=2,
        )
        self.assertTrue(src.connect())  # epoch 1, attempts 0
        src.disconnect()
        self.assertTrue(src.connect())  # epoch 2, attempt 1
        src.disconnect()
        self.assertTrue(src.connect())  # epoch 3, attempt 2
        src.disconnect()
        self.assertFalse(src.connect())  # exhausted
        self.assertEqual(src.reconnect_attempts, 2)

    def test_fc11_source_wraps_parser(self) -> None:
        csv_text, _ = _fc11_fixture("fc11_clean_stable")
        src = FC11LiveSource(csv_text=csv_text)
        self.assertTrue(src.connect())
        pkt = src.receive()
        self.assertIsNotNone(pkt)
        self.assertIn("eeg_scaled", src.channel_names)
        self.assertEqual(pkt.connection_epoch, 1)

    def test_fc11_reconnect_resets_epoch(self) -> None:
        csv_text, _ = _fc11_fixture("fc11_clean_stable")
        src = FC11LiveSource(csv_text=csv_text)
        src.connect()
        src.receive()
        first_epoch = src.epoch
        src.disconnect()
        src.connect()
        pkt = src.receive()
        self.assertEqual(src.epoch, first_epoch + 1)
        self.assertEqual(pkt.connection_epoch, src.epoch)


class PacketBufferTests(unittest.TestCase):
    def test_accepts_monotonic_packets(self) -> None:
        buf = PacketBuffer(max_size=10)
        buf.reset(1)
        p1 = LivePacket(packet_index=0, source_timestamp=0.0, channel_values={"x": 1.0})
        p2 = LivePacket(packet_index=1, source_timestamp=0.1, channel_values={"x": 2.0})
        self.assertTrue(buf.push(p1).accepted)
        self.assertTrue(buf.push(p2).accepted)
        self.assertEqual(len(buf), 2)

    def test_detects_late_packets(self) -> None:
        buf = PacketBuffer(max_size=10)
        buf.reset(1)
        p1 = LivePacket(packet_index=0, source_timestamp=0.2, channel_values={"x": 1.0})
        p2 = LivePacket(packet_index=1, source_timestamp=0.1, channel_values={"x": 2.0})
        self.assertTrue(buf.push(p1).accepted)
        self.assertFalse(buf.push(p2).accepted)
        self.assertEqual(buf.push(p2).reason, "late_packet")

    def test_detects_duplicate_timestamps(self) -> None:
        buf = PacketBuffer(max_size=10)
        buf.reset(1)
        p1 = LivePacket(packet_index=0, source_timestamp=0.1, channel_values={"x": 1.0})
        p2 = LivePacket(packet_index=1, source_timestamp=0.1, channel_values={"x": 2.0})
        self.assertTrue(buf.push(p1).accepted)
        self.assertFalse(buf.push(p2).accepted)
        self.assertEqual(buf.push(p2).reason, "duplicate_packet")

    def test_buffer_overflow(self) -> None:
        buf = PacketBuffer(max_size=2)
        buf.reset(1)
        p = LivePacket(packet_index=0, source_timestamp=0.0, channel_values={"x": 1.0})
        self.assertTrue(buf.push(p).accepted)
        p1 = LivePacket(packet_index=1, source_timestamp=0.1, channel_values={"x": 1.0})
        p2 = LivePacket(packet_index=2, source_timestamp=0.2, channel_values={"x": 1.0})
        self.assertTrue(buf.push(p1).accepted)
        self.assertFalse(buf.push(p2).accepted)
        self.assertEqual(buf.push(p2).reason, "buffer_overflow")

    def test_reset_clears_epoch_state(self) -> None:
        buf = PacketBuffer(max_size=10)
        buf.reset(1)
        p1 = LivePacket(packet_index=0, source_timestamp=0.1, channel_values={"x": 1.0})
        buf.push(p1)
        buf.reset(2)
        p2 = LivePacket(packet_index=2, source_timestamp=0.1, channel_values={"x": 2.0})
        self.assertTrue(buf.push(p2).accepted)


class LiveClockTests(unittest.TestCase):
    def test_semantic_time_independent_of_wall(self) -> None:
        clock = LiveClock()
        clock.reset(0.0)
        clock.start_wall()
        clock.advance(1.5)
        self.assertAlmostEqual(clock.semantic_time, 1.5)
        self.assertIsNotNone(clock.wall_elapsed)


class GatewayLifecycleTests(unittest.TestCase):
    def test_start_stop(self) -> None:
        source = SyntheticLiveSource(duration=0.5, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        self.assertTrue(gateway.start())
        self.assertEqual(gateway.health.status, LiveHealthStatus.RUNNING)
        gateway.stop()
        self.assertEqual(gateway.health.status, LiveHealthStatus.STOPPED)
        self.assertFalse(source.connected)

    def test_pause_resume(self) -> None:
        source = SyntheticLiveSource(duration=0.5, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        gateway.start()
        self.assertTrue(gateway.tick())
        gateway.pause()
        self.assertEqual(gateway.health.status, LiveHealthStatus.PAUSED)
        self.assertFalse(gateway.tick())
        gateway.resume()
        self.assertEqual(gateway.health.status, LiveHealthStatus.RUNNING)
        self.assertTrue(gateway.tick())
        gateway.stop()

    def test_health_transitions(self) -> None:
        source = SyntheticLiveSource(duration=0.3, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        self.assertEqual(gateway.health.status, LiveHealthStatus.DISCONNECTED)
        gateway.start()
        self.assertEqual(gateway.health.status, LiveHealthStatus.RUNNING)
        gateway.pause()
        self.assertEqual(gateway.health.status, LiveHealthStatus.PAUSED)
        gateway.resume()
        self.assertEqual(gateway.health.status, LiveHealthStatus.RUNNING)
        gateway.stop()
        self.assertEqual(gateway.health.status, LiveHealthStatus.STOPPED)

    def test_gateway_events_in_store(self) -> None:
        source = SyntheticLiveSource(duration=0.5, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        gateway.run()
        events = gateway.store.read(SessionID(gateway.session_id))
        types = {e.event_type for e in events}
        self.assertIn(LiveEventType.GATEWAY_STARTED.value, types)
        self.assertIn(LiveEventType.GATEWAY_STOPPED.value, types)


class LiveReplayEquivalenceTests(unittest.TestCase):
    def _assert_samples_equivalent(self, live, replay) -> None:
        self.assertEqual(len(live), len(replay))
        for a, b in zip(live, replay, strict=True):
            self.assertEqual(a.source_sample_index, b.source_sample_index)
            self.assertEqual(a.source_timestamp, b.source_timestamp)
            self.assertEqual(a.replay_relative_timestamp, b.replay_relative_timestamp)
            self.assertEqual(a.channel_values, b.channel_values)
            self.assertEqual(a.raw_quality, b.raw_quality)
            self.assertEqual(a.missing_channel_indicators, b.missing_channel_indicators)
            self.assertEqual(sorted(a.normalization_operations), sorted(b.normalization_operations))

    def _assert_assessments_equivalent(self, live, replay) -> None:
        self.assertEqual(len(live), len(replay))
        for a, b in zip(live, replay, strict=True):
            self.assertEqual(a.accepted, b.accepted)
            self.assertEqual(a.quality_score, b.quality_score)
            self.assertEqual(a.reason_codes, b.reason_codes)
            self.assertEqual(a.detected_artifacts, b.detected_artifacts)
            self.assertEqual(a.missingness, b.missingness)

    def test_normalization_quality_equivalence_to_replay(self) -> None:
        csv_text, meta_text = _fc11_fixture("fc11_clean_stable")
        replay = _replay_result("fc11_clean_stable")
        live = _run_live(csv_text)
        self._assert_samples_equivalent(
            live.normalized_samples,
            replay.normalized_samples,
        )
        self._assert_assessments_equivalent(
            live.quality_assessments,
            replay.quality_assessments,
        )

    def test_observation_frames_equivalent(self) -> None:
        csv_text, meta_text = _fc11_fixture("fc11_clean_stable")
        replay = _replay_result("fc11_clean_stable")
        live = _run_live(csv_text)
        self.assertEqual(len(replay.observation_frames), len(live.observation_frames))
        for replay_frame, live_frame in zip(replay.observation_frames, live.observation_frames, strict=True):
            self.assertAlmostEqual(replay_frame.eeg_stability, live_frame.eeg_stability, places=5)
            self.assertEqual(replay_frame.eeg_quality, live_frame.eeg_quality)
            self.assertEqual(replay_frame.available_modalities, live_frame.available_modalities)

    def test_replay_live_clm_states_and_decisions_equivalent(self) -> None:
        csv_text, meta_text = _fc11_fixture("fc11_clean_stable")
        replay = _replay_result("fc11_clean_stable")
        live = _run_live(csv_text)
        self.assertTrue(replay.observation_frames)
        self.assertEqual(len(replay.observation_frames), len(live.observation_frames))
        loop_replay = ControlLoop()
        loop_live = ControlLoop()
        result_replay = loop_replay.run_session(replay.observation_frames)
        result_live = loop_live.run_session(live.observation_frames)
        self.assertEqual(
            result_replay.final_control_state.as_dict(),
            result_live.final_control_state.as_dict(),
        )
        self.assertEqual(
            [c.estimate.cognitive_load for c in result_replay.cycles],
            [c.estimate.cognitive_load for c in result_live.cycles],
        )


class LiveWindowAndFrameTests(unittest.TestCase):
    def test_half_open_window_semantics(self) -> None:
        csv_text, _ = _fc11_fixture("fc11_clean_stable")
        result = _run_live(csv_text)
        self.assertTrue(result.windows)
        for w in result.windows[:-1]:
            for sid in w.ordered_sample_ids:
                sample = next(
                    s for s in result.normalized_samples if s.normalized_sample_id == sid
                )
                if sample.replay_relative_timestamp is not None:
                    self.assertGreaterEqual(sample.replay_relative_timestamp, w.start_replay_timestamp)
                    self.assertLess(sample.replay_relative_timestamp, w.end_replay_timestamp)

    def test_one_frame_per_accepted_window(self) -> None:
        csv_text, _ = _fc11_fixture("fc11_clean_stable")
        result = _run_live(csv_text)
        accepted_windows = [w for w in result.windows if w.accepted]
        self.assertEqual(len(result.observation_frames), len(accepted_windows))

    def test_frame_provenance(self) -> None:
        csv_text, _ = _fc11_fixture("fc11_clean_stable")
        result = _run_live(csv_text)
        for frame in result.observation_frames:
            self.assertTrue(frame.source_event_ids)
            self.assertIn("eeg", frame.available_modalities)

    def test_missing_eeg_handling(self) -> None:
        packets = [
            LivePacket(packet_index=0, source_timestamp=0.0, channel_values={"eeg_scaled": None}, raw_quality="5"),
            LivePacket(packet_index=1, source_timestamp=0.1, channel_values={"eeg_scaled": 78.5}, raw_quality="5"),
        ]
        source = SyntheticLiveSource(duration=0.0, packet_interval=0.1, seed=0)
        # Manually feed packets through the gateway to test missing EEG.
        gateway = LiveGateway(source=source)
        gateway.start()
        for pkt in packets:
            gateway.ingest(pkt)
        result = gateway.flush()
        missing = [s for s in result.normalized_samples if s.missing_channel_indicators.get("eeg_scaled")]
        self.assertTrue(missing)
        for s in result.normalized_samples:
            self.assertIsInstance(s.missing_channel_indicators, dict)


class LiveNegativeAndConstraintTests(unittest.TestCase):
    def test_no_audio_or_speechgen_in_clm04(self) -> None:
        source = SyntheticLiveSource(duration=0.5, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        result = gateway.run()
        all_event_types = {e.event_type for e in gateway.store.all_events()}
        forbidden = {
            "audio_render_started",
            "audio_render_failed",
            "playback_scheduled",
            "speechgen_synthesis_started",
            "adapted_stimulus_rendered",
        }
        self.assertTrue(forbidden.isdisjoint(all_event_types))
        self.assertEqual(result.observation_frames, gateway._frames)
        # Gateway must not import or use SpeechGen routing.
        import mindtune_clm.live.gateway as gateway_module
        self.assertNotIn("speechgen", gateway_module.__dict__)

    def test_no_hila_hannah_provider(self) -> None:
        source = SyntheticLiveSource(duration=0.5, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        gateway.run()
        self.assertNotEqual(source.source_id, "hila")
        self.assertNotEqual(source.source_id, "hannah")

    def test_duplicate_and_late_detection_produces_events(self) -> None:
        source = SyntheticLiveSource(duration=0.3, packet_interval=0.1, seed=0)
        gateway = LiveGateway(source=source)
        gateway.start()
        # Feed duplicate
        pkt = LivePacket(packet_index=0, source_timestamp=0.0, channel_values={"eeg_scaled": 1.0})
        self.assertTrue(gateway.ingest(pkt))
        self.assertFalse(gateway.ingest(pkt))
        # Feed late
        late = LivePacket(packet_index=1, source_timestamp=-1.0, channel_values={"eeg_scaled": 1.0})
        self.assertFalse(gateway.ingest(late))
        events = gateway.store.read(SessionID(gateway.session_id))
        types = {e.event_type for e in events}
        self.assertIn(LiveEventType.PACKET_DUPLICATE.value, types)
        self.assertIn(LiveEventType.PACKET_LATE.value, types)


class MPEEventTypeRegistrationTests(unittest.TestCase):
    def test_all_live_event_types_supported(self) -> None:
        from mpe.events import SUPPORTED_EVENT_TYPES
        self.assertTrue(LiveEventType.all().issubset(SUPPORTED_EVENT_TYPES))


if __name__ == "__main__":
    unittest.main()
