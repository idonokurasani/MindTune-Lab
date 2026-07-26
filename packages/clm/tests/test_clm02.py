"""Deterministic tests for CLM-02 sensor replay."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from typing import Any

from mindtune_clm import (
    ControlPolicy,
    MantraControlState,
)
from mindtune_clm.replay import (
    CSVParser,
    NormalizationPolicy,
    QualityPolicy,
    ReplayRunner,
    WindowPolicy,
    compare_policies,
    load_source_from_text,
)
from mindtune_clm.replay.events import CLM02EventType

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "replay"


def _fixture_text(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text(encoding="utf-8")


def _default_policies() -> tuple[CSVParser, NormalizationPolicy, QualityPolicy, WindowPolicy, ControlPolicy]:
    parser = CSVParser()
    normalization = NormalizationPolicy(
        policy_id="norm.v1",
        version="1.0.0",
        required_channels=["eeg_stability"],
        unit_scale=1.0,
    )
    quality = QualityPolicy(
        policy_id="quality.v1",
        version="1.0.0",
        amplitude_min=-10.0,
        amplitude_max=10.0,
        flatline_tolerance=0.0,
        discontinuity_threshold=10.0,
        min_accepted_sample_count=5,
        min_channel_coverage=1,
    )
    window = WindowPolicy(
        policy_id="window.v1",
        version="1.0.0",
        window_duration_s=1.0,
        step_duration_s=1.0,
        min_accepted_sample_count=5,
        min_channel_coverage=1,
        partial_final_window=True,
    )
    clm = ControlPolicy()
    return parser, normalization, quality, window, clm


def _run_fixture(name: str, replay_id: str = "test-replay"):
    text = _fixture_text(name)
    source, content = load_source_from_text(
        source_id=f"fixture_{name.replace('.', '_')}",
        fixture_handle=name,
        text=text,
        channel_names=["eeg_stability"],
        source_sampling_rate_hz=10.0,
        source_start_timestamp=0.0,
    )
    parser, normalization, quality, window, clm = _default_policies()
    runner = ReplayRunner()
    return runner.run(
        replay_id=replay_id,
        source=source,
        content=content,
        parser=parser,
        normalization_policy=normalization,
        quality_policy=quality,
        window_policy=window,
        clm_policy=clm,
    )


def _small_source(rows: list[list[float | str]]) -> tuple[Any, str]:
    lines = "timestamp,eeg_stability,quality\n"
    for row in rows:
        lines += ",".join(str(v) for v in row) + "\n"
    source, content = load_source_from_text(
        source_id="synthetic",
        fixture_handle="synthetic.csv",
        text=lines,
        channel_names=["eeg_stability"],
        source_sampling_rate_hz=10.0,
        source_start_timestamp=0.0,
    )
    return source, content


class CLM02ReplayTests(unittest.TestCase):
    def test_manifest_checksum_is_verifiable(self) -> None:
        from mindtune_clm.replay.manifest import make_manifest, verify_manifest

        source, content = load_source_from_text(
            source_id="s1", fixture_handle="f.csv", text="a\n", channel_names=["x"]
        )
        m = make_manifest(
            replay_id="r1",
            source=source,
            parser_id="p", parser_version="1",
            normalization_policy_id="n", normalization_policy_version="1",
            quality_policy_id="q", quality_policy_version="1",
            window_policy_id="w", window_policy_version="1",
            clm_policy_id="c", clm_policy_version="1",
            replay_clock_config={"scale": 1.0},
            deterministic_seed="seed",
            requested_time_interval=None,
            creation_timestamp=1.0,
        )
        self.assertTrue(verify_manifest(m))

    def test_same_source_and_manifest_produce_same_digest(self) -> None:
        result1 = _run_fixture("clean_stable.replay.csv", replay_id="r1")
        result2 = _run_fixture("clean_stable.replay.csv", replay_id="r1")
        self.assertEqual(
            result1.canonical_replay_digest.digest_hex,
            result2.canonical_replay_digest.digest_hex,
        )
        self.assertEqual(
            result1.canonical_replay_digest.canonical_json,
            result2.canonical_replay_digest.canonical_json,
        )

    def test_replaying_twice_produces_identical_payloads_and_trajectory(self) -> None:
        result1 = _run_fixture("deterioration_recovery.replay.csv")
        result2 = _run_fixture("deterioration_recovery.replay.csv")
        self.assertEqual(len(result1.observation_frames), len(result2.observation_frames))
        for f1, f2 in zip(result1.observation_frames, result2.observation_frames, strict=True):
            self.assertEqual(f1.observation_timestamp, f2.observation_timestamp)
            self.assertEqual(f1.eeg_stability, f2.eeg_stability)
            self.assertEqual(f1.available_modalities, f2.available_modalities)
        c1 = [_cycle_key(c) for c in result1.clm_session_result.cycles]
        c2 = [_cycle_key(c) for c in result2.clm_session_result.cycles]
        self.assertEqual(c1, c2)

    def test_wall_clock_time_does_not_affect_results(self) -> None:
        result = _run_fixture("clean_stable.replay.csv")
        for event in result.clm_session_result.events:
            self.assertIsNone(event.wallclock_at)
        # The replay clock must not pull from wall clock.
        from mindtune_clm.replay.clock import ReplayClock
        clock = ReplayClock(source_start_timestamp=123.0, sample_interval=0.1)
        self.assertEqual(clock.now(), 123.0)

    def test_absolute_file_location_does_not_affect_digest(self) -> None:
        text = _fixture_text("clean_stable.replay.csv")
        s1, c1 = load_source_from_text(
            source_id="same", fixture_handle="a/clean.csv", text=text, channel_names=["eeg_stability"]
        )
        s2, c2 = load_source_from_text(
            source_id="same", fixture_handle="b/clean.csv", text=text, channel_names=["eeg_stability"]
        )
        parser, norm, qual, win, clm = _default_policies()
        runner = ReplayRunner()
        r1 = runner.run("r", s1, c1, parser, norm, qual, win, clm)
        r2 = runner.run("r", s2, c2, parser, norm, qual, win, clm)
        self.assertEqual(r1.canonical_replay_digest.digest_hex, r2.canonical_replay_digest.digest_hex)

    def test_one_sample_source_change_changes_digest(self) -> None:
        text = _fixture_text("clean_stable.replay.csv")
        altered = text.replace(",0.95,good\n", ",0.10,good\n", 1)
        s1, c1 = load_source_from_text("orig", "f.csv", text, ["eeg_stability"])
        s2, c2 = load_source_from_text("changed", "f.csv", altered, ["eeg_stability"])
        parser, norm, qual, win, clm = _default_policies()
        runner = ReplayRunner()
        r1 = runner.run("r", s1, c1, parser, norm, qual, win, clm)
        r2 = runner.run("r", s2, c2, parser, norm, qual, win, clm)
        self.assertNotEqual(r1.canonical_replay_digest.digest_hex, r2.canonical_replay_digest.digest_hex)

    def test_policy_version_change_changes_digest(self) -> None:
        text = _fixture_text("clean_stable.replay.csv")
        s, c = load_source_from_text("same", "f.csv", text, ["eeg_stability"])
        parser, norm, qual, win, clm = _default_policies()
        r1 = ReplayRunner().run("r", s, c, parser, norm, qual, win, clm)
        norm2 = NormalizationPolicy(
            policy_id="norm.v1", version="1.0.1", required_channels=["eeg_stability"], unit_scale=1.0
        )
        r2 = ReplayRunner().run("r", s, c, parser, norm2, qual, win, clm)
        self.assertNotEqual(r1.canonical_replay_digest.digest_hex, r2.canonical_replay_digest.digest_hex)

    def test_window_size_change_changes_digest(self) -> None:
        text = _fixture_text("clean_stable.replay.csv")
        s, c = load_source_from_text("same", "f.csv", text, ["eeg_stability"])
        parser, norm, qual, win, clm = _default_policies()
        r1 = ReplayRunner().run("r", s, c, parser, norm, qual, win, clm)
        win2 = WindowPolicy(
            policy_id="window.v1", version="1.0.0",
            window_duration_s=0.5, step_duration_s=0.5,
            min_accepted_sample_count=3, min_channel_coverage=1, partial_final_window=True,
        )
        r2 = ReplayRunner().run("r", s, c, parser, norm, qual, win2, clm)
        self.assertNotEqual(r1.canonical_replay_digest.digest_hex, r2.canonical_replay_digest.digest_hex)

    def test_duplicate_timestamps_are_rejected_by_rule(self) -> None:
        result = _run_fixture("corrupted.replay.csv")
        ops = [op for s in result.normalized_samples for op in s.normalization_operations]
        self.assertIn("duplicate_rejected", ops)

    def test_timestamp_regressions_are_rejected_or_repaired(self) -> None:
        result = _run_fixture("corrupted.replay.csv")
        ops = [op for s in result.normalized_samples for op in s.normalization_operations]
        self.assertIn("timestamp_regression_rejected", ops)

    def test_low_quality_samples_are_rejected_with_reason_codes(self) -> None:
        result = _run_fixture("corrupted.replay.csv")
        rejected = [a for a in result.quality_assessments if not a.accepted]
        reason_codes = {code for a in rejected for code in a.reason_codes}
        self.assertIn("poor_signal", reason_codes)

    def test_missing_eeg_does_not_stop_replay(self) -> None:
        rows = [[t, "", "good"] for t in (round(i * 0.1, 2) for i in range(20))]
        source, content = _small_source(rows)
        parser, norm, qual, win, clm = _default_policies()
        qual = QualityPolicy(
            policy_id="quality.v1", version="1.0.1",
            amplitude_min=-10.0, amplitude_max=10.0,
            min_accepted_sample_count=5, min_channel_coverage=0,
        )
        runner = ReplayRunner()
        result = runner.run("missing-eeg", source, content, parser, norm, qual, win, clm)
        # The replay should complete even though no EEG evidence is usable.
        completed = any(e.event_type == CLM02EventType.SENSOR_REPLAY_COMPLETED for e in result.clm_session_result.events)
        self.assertTrue(completed)

    def test_rejected_window_cannot_silently_produce_accepted_eeg(self) -> None:
        result = _run_fixture("corrupted.replay.csv")
        accepted_window_count = sum(1 for w in result.windows if w.accepted)
        self.assertEqual(len(result.observation_frames), accepted_window_count)

    def test_window_boundaries_are_half_open_and_deterministic(self) -> None:
        result = _run_fixture("clean_stable.replay.csv")
        first = result.windows[0]
        self.assertEqual(first.start_replay_timestamp, 0.0)
        self.assertEqual(first.end_replay_timestamp, 1.0)
        for sample_id in first.ordered_sample_ids:
            sample = next(s for s in result.normalized_samples if s.normalized_sample_id == sample_id)
            if sample.replay_relative_timestamp is not None:
                self.assertTrue(0.0 <= sample.replay_relative_timestamp < 1.0)

    def test_adapter_generates_valid_observation_frames(self) -> None:
        result = _run_fixture("clean_stable.replay.csv")
        for frame in result.observation_frames:
            self.assertTrue(frame.observation_frame_id.startswith("obs-"))
            self.assertTrue(frame.control_cycle_id.startswith("cc-"))
            self.assertIsInstance(frame.session_id, str)
            self.assertIsNotNone(frame.observation_timestamp)

    def test_clm01_causal_test_passes_during_replay(self) -> None:
        result = _run_fixture("deterioration_recovery.replay.csv")
        apply_cycles = [c for c in result.clm_session_result.cycles if c.decision.decision_kind.value == "apply"]
        self.assertTrue(len(apply_cycles) > 0)
        for c in apply_cycles:
            self.assertGreater(c.rendered_control_state.assistance_level, 0.0)
            self.assertEqual(
                c.rendered_control_state.as_dict(),
                c.receipt.applied_state.as_dict(),
            )

    def test_deterioration_and_recovery_progressive_trace(self) -> None:
        result = _run_fixture("deterioration_recovery.replay.csv")
        states = [c.estimate.cognitive_state.value for c in result.clm_session_result.cycles]
        decisions = [c.decision.decision_kind.value for c in result.clm_session_result.cycles]
        # The high-load windows should produce at least one apply, then recovery.
        self.assertIn("recovery_required", states)
        self.assertIn("apply", decisions)
        # Assistance must eventually withdraw toward baseline.
        final = result.clm_session_result.final_control_state
        self.assertLessEqual(final.assistance_level, 0.2)

    def test_sufficient_stable_windows_return_actuator_to_baseline(self) -> None:
        rows: list[list[float | str]] = []
        for i in range(20):
            rows.append([round(i * 0.1, 2), 0.40, "good"])
        for i in range(20, 80):
            rows.append([round(i * 0.1, 2), 0.95, "good"])
        source, content = _small_source(rows)
        parser, norm, qual, win, clm = _default_policies()
        runner = ReplayRunner()
        result = runner.run("baseline-return", source, content, parser, norm, qual, win, clm)
        final = result.clm_session_result.final_control_state
        baseline = MantraControlState.baseline()
        self.assertAlmostEqual(final.assistance_level, baseline.assistance_level, places=3)
        self.assertAlmostEqual(final.tempo_ratio, baseline.tempo_ratio, places=3)

    def test_full_causal_graph_reconstructable(self) -> None:
        result = _run_fixture("deterioration_recovery.replay.csv")
        events = result.clm_session_result.events
        by_payload: dict[str, Any] = {}
        for e in events:
            for key in ("observation_frame_id", "window_id", "decision_id", "command_id"):
                if key in e.payload:
                    by_payload[f"{key}:{e.payload[key]}"] = e

        # A CLM observation_frame_created must be preceded by a replay-generated event.
        generated = [e for e in events if e.event_type == CLM02EventType.OBSERVATION_FRAME_GENERATED_FROM_REPLAY]
        for g in generated:
            obs = by_payload.get(f"observation_frame_id:{g.payload['observation_frame_id']}")
            self.assertIsNotNone(obs)
            self.assertIn(str(g.event_id), [str(p) for p in obs.provenance])

    def test_multiple_policies_can_run_over_same_windows(self) -> None:
        result = _run_fixture("deterioration_recovery.replay.csv")
        p1 = ControlPolicy()
        p1.policy_id = "default"  # type: ignore[attr-defined]
        p2 = ControlPolicy()
        p2.policy_id = "aggressive"  # type: ignore[attr-defined]
        p2.first_intervention = MantraControlState(
            tempo_ratio=0.95,
            post_stimulus_pause_ms=300,
            prosodic_emphasis=0.1,
            assistance_level=0.5,
            control_state_id="p2_first",
        )
        comparison = compare_policies(
            replay_id="compare",
            windows=result.windows,
            samples=result.normalized_samples,
            sample_assessments=result.quality_assessments,
            policies=[p1, p2],
            source_start_timestamp=0.0,
            sample_interval=0.1,
        )
        self.assertEqual(len(comparison.policy_trajectories), 2)

    def test_policy_comparison_identifies_first_divergence(self) -> None:
        result = _run_fixture("deterioration_recovery.replay.csv")
        p1 = ControlPolicy()
        p1.policy_id = "default"  # type: ignore[attr-defined]
        p2 = ControlPolicy()
        p2.policy_id = "aggressive"  # type: ignore[attr-defined]
        p2.max_assistance_delta = 1.0  # type: ignore[attr-defined]
        p2.first_intervention = MantraControlState(
            tempo_ratio=0.95,
            post_stimulus_pause_ms=300,
            prosodic_emphasis=0.1,
            assistance_level=0.5,
            control_state_id="p2_first",
        )
        comparison = compare_policies(
            replay_id="compare",
            windows=result.windows,
            samples=result.normalized_samples,
            sample_assessments=result.quality_assessments,
            policies=[p1, p2],
            source_start_timestamp=0.0,
            sample_interval=0.1,
        )
        self.assertIsNotNone(comparison.first_divergence_index)
        self.assertIsNotNone(comparison.divergence_field)
        # The first apply cycle is where the parameter trajectory diverges.
        self.assertIn("parameter", comparison.divergence_field)

    def test_source_fixtures_remain_unchanged(self) -> None:
        for name in ("clean_stable.replay.csv", "deterioration_recovery.replay.csv", "corrupted.replay.csv"):
            path = FIXTURE_ROOT / name
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            _run_fixture(name)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(before, after)

    def test_replay_failure_emits_typed_event(self) -> None:
        source, content = load_source_from_text(
            source_id="bad", fixture_handle="bad.csv", text="bad\n1\n", channel_names=["eeg_stability"]
        )
        parser, norm, qual, win, clm = _default_policies()
        runner = ReplayRunner()
        result = runner.run("failure", source, content, parser, norm, qual, win, clm)
        event_types = [e.event_type for e in result.clm_session_result.events]
        self.assertIn(CLM02EventType.SENSOR_REPLAY_FAILED.value, event_types)
        self.assertNotIn(CLM02EventType.SENSOR_REPLAY_COMPLETED.value, event_types)


def _cycle_key(c: Any) -> dict[str, Any]:
    return {
        "control_cycle_id": c.control_cycle_id,
        "state": c.estimate.cognitive_state.value,
        "decision": c.decision.decision_kind.value,
        "applied": c.receipt.applied_state.as_dict(),
        "rendered": c.rendered_control_state.as_dict(),
    }


if __name__ == "__main__":
    unittest.main()
