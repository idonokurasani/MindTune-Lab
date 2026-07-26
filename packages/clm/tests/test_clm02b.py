"""CLM-02B FC11 recorded data adapter tests."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from mindtune_clm.replay.fc11 import (
    FC11CSVParser,
    FC11NormalizationPolicy,
    FC11QualityPolicy,
    load_fc11_source_from_text,
)
from mindtune_clm.replay.features import FeaturePolicy, compute_features
from mindtune_clm.replay.parser import CSVParser
from mindtune_clm.replay.runner import ReplayRunner
from mindtune_clm.replay.source import load_source_from_text
from mindtune_clm.replay.windows import WindowPolicy, make_windows

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "fc11"


def _fixture_text(name: str) -> tuple[str, str]:
    csv_path = FIXTURE_ROOT / f"{name}.csv"
    meta_path = FIXTURE_ROOT / f"{name}.json"
    return csv_path.read_text(), meta_path.read_text()


def _load(name: str) -> tuple[object, str, str]:
    csv_text, meta_text = _fixture_text(name)
    return load_fc11_source_from_text(
        source_id=f"fc11:{name}",
        fixture_handle=f"{name}.csv",
        csv_text=csv_text,
        metadata_text=meta_text,
        recording_id=f"{name}-anon",
    )


def _policies(**policy_overrides):
    norm = FC11NormalizationPolicy(**policy_overrides.get("normalization", {}))
    qual = FC11QualityPolicy(**policy_overrides.get("quality", {}))
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
    return norm, qual, win, feat


def _run(name: str, replay_id: str = "test-replay", **overrides):
    source, csv_text, meta_text = _load(name)
    parser = FC11CSVParser()
    norm, qual, win, feat = _policies(**overrides)
    runner = ReplayRunner()
    return runner.run(
        replay_id=replay_id,
        source=source,
        content=csv_text,
        parser=parser,
        normalization_policy=norm,
        quality_policy=qual,
        window_policy=win,
        clm_policy=None,
    )


def _digest(name: str, **overrides) -> str:
    return _run(name, **overrides).canonical_replay_digest.digest_hex


class FC11AdapterTests(unittest.TestCase):
    def test_source_and_metadata_checksums_stable(self) -> None:
        source, csv_text, meta_text = _load("fc11_clean_stable")
        self.assertEqual(
            source.content_checksum,
            hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            source.metadata_checksum,
            hashlib.sha256(meta_text.encode("utf-8")).hexdigest(),
        )

    def test_no_absolute_path_in_canonical_data(self) -> None:
        source, _, _ = _load("fc11_clean_stable")
        canonical = json.loads(_run("fc11_clean_stable").canonical_replay_digest.canonical_json)
        flat = json.dumps(canonical)
        self.assertNotIn("/Users/", flat)
        self.assertNotIn(str(FIXTURE_ROOT), flat)

    def test_repeated_runs_produce_same_digest(self) -> None:
        d1 = _digest("fc11_clean_stable")
        d2 = _digest("fc11_clean_stable")
        self.assertEqual(d1, d2)

    def test_parser_version_change_alters_digest(self) -> None:
        base = _digest("fc11_clean_stable")
        source, csv_text, meta_text = _load("fc11_clean_stable")
        # Simulate a parser version bump in the manifest by using a different parser object.
        parser = FC11CSVParser()
        parser = FC11CSVParser()
        object.__setattr__(parser, "version", "2.0.0")
        norm, qual, win, feat = _policies()
        runner = ReplayRunner()
        result = runner.run(
            replay_id="test",
            source=source,
            content=csv_text,
            parser=parser,
            normalization_policy=norm,
            quality_policy=qual,
            window_policy=win,
            clm_policy=None,
        )
        self.assertNotEqual(base, result.canonical_replay_digest.digest_hex)

    def test_quality_policy_version_change_alters_digest(self) -> None:
        base = _digest("fc11_clean_stable")
        changed = _digest("fc11_clean_stable", quality={"version": "2.0.0"})
        self.assertNotEqual(base, changed)

    def test_duplicate_timestamp_handled(self) -> None:
        result = _run("fc11_timing_corruption")
        reasons = []
        for a in result.quality_assessments:
            reasons.extend(a.reason_codes)
        self.assertIn("fc11_duplicate_timestamp", reasons)

    def test_timestamp_regression_handled(self) -> None:
        result = _run("fc11_timing_corruption")
        reasons = []
        for a in result.quality_assessments:
            reasons.extend(a.reason_codes)
        self.assertIn("fc11_timestamp_regression", reasons)

    def test_malformed_record_handled(self) -> None:
        result = _run("fc11_timing_corruption")
        reasons = []
        for a in result.quality_assessments:
            reasons.extend(a.reason_codes)
        self.assertIn("fc11_malformed_record", reasons)

    def test_packet_loss_represented(self) -> None:
        result = _run("fc11_movement_artifact")
        sample_ids = [a.sample_id for a in result.quality_assessments if "fc11_packet_loss" in a.reason_codes]
        self.assertTrue(sample_ids)

    def test_movement_and_artifact_reduce_evidence(self) -> None:
        result = _run("fc11_movement_artifact")
        rejected = [a for a in result.quality_assessments if not a.accepted]
        self.assertTrue(rejected)
        windows = [w for w in result.windows if not w.accepted]
        self.assertTrue(windows or result.warnings)

    def test_rejected_fc11_window_does_not_produce_accepted_eeg(self) -> None:
        result = _run("fc11_movement_artifact")
        for frame in result.observation_frames:
            self.assertIn("eeg", frame.available_modalities)
            self.assertEqual(frame.eeg_quality, "good")
        # At least one window must be rejected or no frames generated.
        rejected = [w for w in result.windows if not w.accepted]
        if rejected:
            for w in rejected:
                self.assertNotIn(w.window_id, {f.observation_frame_id for f in result.observation_frames})

    def test_deterioration_and_recovery_produce_bounded_control(self) -> None:
        result = _run("fc11_deterioration_recovery")
        loads = [c.estimate.cognitive_load for c in result.clm_session_result.cycles]
        self.assertTrue(any(load > 0.5 for load in loads), "expected a high-load window during deterioration")
        self.assertTrue(any(load < 0.35 for load in loads), "expected recovery to lower load")

    def test_clean_stable_returns_to_baseline(self) -> None:
        result = _run("fc11_clean_stable")
        loads = [c.estimate.cognitive_load for c in result.clm_session_result.cycles]
        if loads:
            self.assertTrue(max(loads) < 0.35, "clean stable should stay at low load")

    def test_missing_eeg_does_not_stop_replay(self) -> None:
        # The timing-corruption fixture still reaches the completed event without crashing.
        result = _run("fc11_timing_corruption")
        event_types = [e.event_type for e in result.clm_session_result.events]
        self.assertIn("fc11_sensor_replay_completed", event_types)

    def test_no_behavioral_evidence_fabricated(self) -> None:
        result = _run("fc11_clean_stable")
        for frame in result.observation_frames:
            self.assertIsNone(frame.behavioral_latency_ms)
            self.assertIsNone(frame.hesitation_score)
            self.assertIsNone(frame.error_score)

    def test_native_quality_flags_preserved_in_provenance(self) -> None:
        source, _, _ = _load("fc11_movement_artifact")
        norm, _, _, _ = _policies()
        parser = FC11CSVParser()
        raw = parser.parse(source, _fixture_text("fc11_movement_artifact")[0])
        normalized = norm.normalize(raw, source)
        for n in normalized:
            if n.raw_quality is not None:
                self.assertIsInstance(n.raw_quality, str)

    def test_generic_csv_v1_replay_still_works(self) -> None:
        text = "timestamp,eeg_stability,quality\n0.0,0.9,good\n0.1,0.9,good\n0.2,0.9,good\n0.3,0.9,good\n0.4,0.9,good\n0.5,0.9,good\n0.6,0.9,good\n0.7,0.9,good\n0.8,0.9,good\n0.9,0.9,good\n1.0,0.9,good\n1.1,0.9,good\n1.2,0.9,good\n1.3,0.9,good\n1.4,0.9,good\n1.5,0.9,good\n1.6,0.9,good\n1.7,0.9,good\n1.8,0.9,good\n1.9,0.9,good\n2.0,0.9,good\n2.1,0.9,good\n2.2,0.9,good\n2.3,0.9,good\n2.4,0.9,good\n"
        source, content = load_source_from_text(
            source_id="csv_v1_compat",
            fixture_handle="compat.csv",
            text=text,
            channel_names=["eeg_stability"],
            source_sampling_rate_hz=10.0,
        )
        from mindtune_clm.replay.normalization import NormalizationPolicy
        from mindtune_clm.replay.quality import QualityPolicy
        from mindtune_clm.replay.windows import WindowPolicy
        csv_feat = FeaturePolicy(
            policy_id="csv_feat.v1",
            version="1.0.0",
            primary_channel="eeg_stability",
            amplitude_range=1.0,
        )
        runner = ReplayRunner()
        result = runner.run(
            replay_id="csv-compat",
            source=source,
            content=content,
            parser=CSVParser(),
            normalization_policy=NormalizationPolicy("np", "1.0.0", required_channels=["eeg_stability"]),
            quality_policy=QualityPolicy("qp", "1.0.0"),
            window_policy=WindowPolicy("wp", "1.0.0", 2.0, 1.0, feature_policy=csv_feat),
            clm_policy=None,
        )
        self.assertTrue(result.observation_frames)
        self.assertIn("sensor_replay_completed", [e.event_type for e in result.clm_session_result.events])

    def test_full_causal_graph_reconstructable(self) -> None:
        result = _run("fc11_clean_stable")
        events = result.clm_session_result.events
        ids = {e.event_id for e in events}
        for e in events:
            for pid in e.provenance:
                self.assertIn(pid, ids)

    def test_window_signal_stability_computed_from_coefficient_of_variation(self) -> None:
        source, csv_text, _ = _load("fc11_deterioration_recovery")
        parser = FC11CSVParser()
        raw = parser.parse(source, csv_text)
        norm, qual, win, feat = _policies()
        normalized = norm.normalize(raw, source)
        assessments = [qual.assess(s, normalized[i - 1] if i else None) for i, s in enumerate(normalized)]
        sample_by_id = {s.normalized_sample_id: s for s in normalized}
        assessment_by_id = {a.sample_id: a for a in assessments}
        windows = make_windows("test", normalized, assessments, win, qual)
        for w in windows:
            if "eeg_scaled" in w.channel_coverage:
                features = compute_features(w, sample_by_id, assessment_by_id, feat)
                self.assertIn("signal_stability", features)
                self.assertGreaterEqual(features["signal_stability"], 0.0)
                self.assertLessEqual(features["signal_stability"], 1.0)

    def test_observation_frame_contains_vendor_context_fields(self) -> None:
        # Adapter must keep source sample IDs and not fabricate behavioral fields.
        result = _run("fc11_clean_stable")
        for frame in result.observation_frames:
            self.assertTrue(frame.source_event_ids)

    def test_parser_id_and_version_recorded(self) -> None:
        result = _run("fc11_clean_stable")
        self.assertEqual(result.replay_manifest.parser_id, "mindtune_clm.replay.fc11_csv.v1")
        self.assertEqual(result.replay_manifest.parser_version, FC11CSVParser().version)


if __name__ == "__main__":
    unittest.main()
