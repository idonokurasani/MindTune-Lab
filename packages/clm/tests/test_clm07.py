"""CLM-07 — Personal Calibration and Individual Baselines tests."""

from __future__ import annotations

import inspect
import unittest

from mindtune_clm import ControlPolicy, StateEstimator
from mindtune_clm.api.fixture_clm05 import auth_headers, make_test_client
from mindtune_clm.calibration import (
    CalibrationProtocol,
    FeatureBaseline,
    InMemoryCalibrationProfileRepository,
    ProfileCompatibility,
    ProfileSelector,
    ProfileStatus,
)
from mindtune_clm.calibration.application import (
    apply_profile_to_observation_frame,
    calibrate_value,
)
from mindtune_clm.calibration.fixture_clm07 import (
    build_incompatible_config_profile,
    build_insufficient_data_profile,
    build_movement_contamination_profile,
    build_two_participant_profiles,
    build_unstable_profile,
    build_valid_profile,
    make_observation_frame,
)
from mindtune_clm.calibration.profiles import recalibration_recommendation
from mindtune_clm.calibration.robust_stats import mad, median, quantile, quantiles
from mindtune_clm.state import CognitiveStateEstimate, MantraControlState
from mpe.enums import CognitiveState


class CLM07ModelAndStatsTests(unittest.TestCase):
    """Core calibration model and robust-statistics properties."""

    def test_valid_profile_can_be_built(self) -> None:
        profile = build_valid_profile("p1")
        self.assertEqual(profile.validity_status, ProfileStatus.VALID)

    def test_profile_is_immutable(self) -> None:
        profile = build_valid_profile("p1")
        with self.assertRaises(AttributeError):
            profile.validity_status = ProfileStatus.INVALID  # type: ignore[misc]

    def test_recalibration_creates_new_profile(self) -> None:
        p1 = build_valid_profile("p1")
        p2 = build_valid_profile("p1")
        self.assertNotEqual(p1.profile_id, p2.profile_id)

    def test_pseudonymous_id_is_sufficient_no_pii(self) -> None:
        profile = build_valid_profile("anon-42")
        data = profile.as_dict()
        self.assertEqual(data["participant_id"], "anon-42")
        for pii in ("real_name", "email", "phone", "dob", "address", "employer"):
            self.assertNotIn(pii, data)

    def test_raw_observations_remain_unchanged(self) -> None:
        profile = build_valid_profile("p1")
        frame = make_observation_frame(eeg_stability=0.65)
        apply_profile_to_observation_frame(frame, profile, "p1")
        self.assertEqual(frame.eeg_stability, 0.65)

    def test_calibrated_values_reference_raw_and_profile(self) -> None:
        profile = build_valid_profile("p1")
        frame = make_observation_frame()
        calibrated, _ = apply_profile_to_observation_frame(frame, profile, "p1")
        for obs in calibrated:
            self.assertEqual(obs.source_observation_id, frame.observation_frame_id)
            self.assertEqual(obs.profile_id, profile.profile_id)
            self.assertEqual(obs.profile_version, profile.profile_version)
            self.assertTrue(obs.algorithm_version)

    def test_rejected_observations_not_in_baseline_statistics(self) -> None:
        profile = build_movement_contamination_profile("p1")
        self.assertGreater(profile.quality_summary.rejected_count, 0)
        for baseline in profile.feature_baselines.values():
            self.assertEqual(baseline.rejected_count, 0)
            self.assertEqual(baseline.sample_count, baseline.accepted_count)

    def test_missing_data_is_counted(self) -> None:
        profile = build_valid_profile("p1")
        self.assertGreater(profile.quality_summary.missing_count, 0)

    def test_no_interpolation_by_default(self) -> None:
        profile = build_valid_profile("p1")
        frame = make_observation_frame(respiration_stability=None, voice_stability=None)
        calibrated, _ = apply_profile_to_observation_frame(frame, profile, "p1")
        names = {c.feature_name for c in calibrated}
        self.assertNotIn("respiration_stability", names)
        self.assertNotIn("voice_stability", names)

    def test_robust_median_is_deterministic(self) -> None:
        values = [3.0, 1.0, 2.0, 5.0, 4.0]
        self.assertEqual(median(values), 3.0)
        self.assertEqual(median(values), median(values))

    def test_mad_is_deterministic(self) -> None:
        values = [3.0, 1.0, 2.0, 5.0, 4.0]
        self.assertEqual(mad(values), mad(values))
        self.assertGreaterEqual(mad(values), 0.0)

    def test_quantiles_are_deterministic(self) -> None:
        values = list(range(1, 21))
        self.assertEqual(quantile(values, 0.5), quantile(values, 0.5))
        qs = quantiles(values, ["q1", "q2", "q3"], [0.25, 0.5, 0.75])
        self.assertEqual(qs, quantiles(values, ["q1", "q2", "q3"], [0.25, 0.5, 0.75]))

    def test_zero_dispersion_is_handled_explicitly(self) -> None:
        baseline = FeatureBaseline(
            feature_name="constant",
            modality="eeg",
            unit="",
            sample_count=10,
            accepted_count=10,
            rejected_count=0,
            missing_count=0,
            central_tendency=0.5,
            dispersion=0.0,
            robust_min=0.5,
            robust_max=0.5,
            transformation_recommendation="robust_z",
            algorithm_version="clm07.robust.v1",
        )
        value, reasons = calibrate_value(0.5, baseline, "robust_z")
        self.assertIn("calibration_zero_dispersion", reasons)


class CLM07StabilityAndValidationTests(unittest.TestCase):
    """Stability, compatibility, and selection rules."""

    def test_minimum_sample_count_alone_does_not_guarantee_validity(self) -> None:
        profile = build_insufficient_data_profile("p1")
        self.assertNotEqual(profile.validity_status, ProfileStatus.VALID)

    def test_stability_checks_are_required(self) -> None:
        profile = build_unstable_profile("p1")
        self.assertIn("excessive_within_block_drift", profile.stability_summary.reason_codes)

    def test_repeated_blocks_are_evaluated(self) -> None:
        profile = build_valid_profile("p1")
        for baseline in profile.feature_baselines.values():
            self.assertIn("block_agreement", baseline.stability_metrics)

    def test_compatibility_checks_sensor_family(self) -> None:
        profile = build_valid_profile("p1")
        compat = ProfileCompatibility(CalibrationProtocol.default())
        result = compat.check(
            profile,
            "p1",
            "other_device",
            profile.sensor_config_fingerprint,
            profile.parser_version,
            profile.feature_schema_version,
        )
        self.assertFalse(result.compatible)
        self.assertIn("sensor_family_mismatch", result.reasons)

    def test_compatibility_checks_feature_schema(self) -> None:
        profile = build_valid_profile("p1")
        compat = ProfileCompatibility(CalibrationProtocol.default())
        result = compat.check(
            profile,
            "p1",
            profile.sensor_family,
            profile.sensor_config_fingerprint,
            profile.parser_version,
            "other.schema",
        )
        self.assertFalse(result.compatible)
        self.assertIn("feature_schema_mismatch", result.reasons)

    def test_compatibility_checks_parser_version(self) -> None:
        profile = build_valid_profile("p1")
        compat = ProfileCompatibility(CalibrationProtocol.default())
        result = compat.check(
            profile,
            "p1",
            profile.sensor_family,
            profile.sensor_config_fingerprint,
            "other.parser",
            profile.feature_schema_version,
        )
        self.assertFalse(result.compatible)
        self.assertIn("parser_version_mismatch", result.reasons)

    def test_incompatible_profiles_are_rejected(self) -> None:
        repo = InMemoryCalibrationProfileRepository()
        profile = build_incompatible_config_profile("p1")
        repo.add(profile)
        selected = repo.latest_compatible(
            "p1",
            "fc11",
            "fc11.default",
            profile.parser_version,
            profile.feature_schema_version,
        )
        self.assertIsNone(selected)

    def test_expired_profiles_are_not_silently_selected(self) -> None:
        from dataclasses import replace

        profile = build_valid_profile("p1")
        expired = replace(profile, validity_status=ProfileStatus.EXPIRED)
        repo = InMemoryCalibrationProfileRepository()
        repo.add(expired)
        selector = ProfileSelector(CalibrationProtocol.default())
        result = selector.select(
            [expired],
            "p1",
            profile.sensor_family,
            profile.sensor_config_fingerprint,
            profile.parser_version,
            profile.feature_schema_version,
        )
        self.assertIsNone(result.profile_id)

    def test_superseded_profiles_are_not_silently_selected(self) -> None:
        from dataclasses import replace

        profile = build_valid_profile("p1")
        superseded = replace(profile, validity_status=ProfileStatus.SUPERSEDED)
        selector = ProfileSelector(CalibrationProtocol.default())
        result = selector.select(
            [superseded],
            "p1",
            profile.sensor_family,
            profile.sensor_config_fingerprint,
            profile.parser_version,
            profile.feature_schema_version,
        )
        self.assertIsNone(result.profile_id)

    def test_explicit_pinned_compatible_profile_is_selected(self) -> None:
        profile = build_valid_profile("p1")
        selector = ProfileSelector(CalibrationProtocol.default())
        result = selector.select(
            [profile],
            "p1",
            "fc11",
            "fc11.default",
            profile.parser_version,
            profile.feature_schema_version,
            pinned_profile_id=profile.profile_id,
        )
        self.assertEqual(result.profile_id, profile.profile_id)
        self.assertIn("pinned", result.reason)

    def test_latest_valid_compatible_profile_selected_otherwise(self) -> None:
        p1 = build_valid_profile("p1")
        p2 = build_valid_profile("p1")
        repo = InMemoryCalibrationProfileRepository()
        repo.add(p1)
        repo.add(p2)
        selector = ProfileSelector(CalibrationProtocol.default())
        result = selector.select(
            repo.list_for_participant("p1"),
            "p1",
            "fc11",
            "fc11.default",
            p1.parser_version,
            p1.feature_schema_version,
        )
        self.assertIsNotNone(result.profile_id)

    def test_no_cross_participant_profile_leakage(self) -> None:
        pa, pb, _ = build_two_participant_profiles()
        repo = InMemoryCalibrationProfileRepository()
        repo.add(pa)
        repo.add(pb)
        for_a = {p.profile_id for p in repo.list_for_participant("participant-a")}
        self.assertIn(pa.profile_id, for_a)
        self.assertNotIn(pb.profile_id, for_a)

    def test_drift_recommendation_does_not_mutate_profile(self) -> None:
        profile = build_valid_profile("p1")
        original = profile.validity_status
        rec = recalibration_recommendation(profile, [], 5, 3)
        self.assertEqual(profile.validity_status, original)
        self.assertIsNotNone(rec)


class CLM07BehavioralAndVendorTests(unittest.TestCase):
    """Behavioral calibration and vendor-metric handling."""

    def test_behavioral_response_time_baseline_is_trial_type_specific(self) -> None:
        features = CalibrationProtocol.default().features
        self.assertIn("response_time_correct", features)
        self.assertIn("response_time_incorrect", features)
        self.assertNotIn("universal_response_time", features)

    def test_vendor_attention_is_contextual(self) -> None:
        defaults = CalibrationProtocol.default().normalization_defaults
        self.assertIn("vendor_attention", defaults)
        self.assertEqual(defaults["vendor_attention"], "percentile")

    def test_vendor_meditation_is_contextual(self) -> None:
        defaults = CalibrationProtocol.default().normalization_defaults
        self.assertIn("vendor_meditation", defaults)
        self.assertEqual(defaults["vendor_meditation"], "percentile")


class CLM07EstimatorAndPolicyTests(unittest.TestCase):
    """Estimator adapter and control-policy separation."""

    def test_state_estimator_can_consume_calibrated_features(self) -> None:
        profile = build_valid_profile("est-p")
        frame = make_observation_frame(eeg_stability=0.65)
        _, calibrated_values = apply_profile_to_observation_frame(frame, profile, "est-p")
        estimator = StateEstimator()
        estimate = estimator.estimate(frame, calibrated_values=calibrated_values)
        self.assertIsInstance(estimate, CognitiveStateEstimate)

    def test_estimator_can_abstain_when_evidence_missing(self) -> None:
        frame = make_observation_frame(
            eeg_stability=None,
            behavioral_latency_ms=None,
            hesitation_score=None,
            error_score=None,
        )
        estimator = StateEstimator()
        estimate = estimator.estimate(frame)
        self.assertEqual(estimate.cognitive_load, 0.0)
        self.assertIn("no_usable_evidence", estimate.reason_codes)

    def test_same_state_estimate_produces_same_policy_decision(self) -> None:
        estimate = CognitiveStateEstimate(
            estimate_id="e1",
            source_observation_frame_id="f1",
            source_control_cycle_id="cc1",
            cognitive_state=CognitiveState.RECOVERY_REQUIRED,
            attention_stability=0.5,
            cognitive_load=0.8,
            fatigue_probability=0.8,
            recovery_probability=0.0,
            confidence=0.9,
            trend="deteriorating",
            validity_horizon=1.0,
        )
        policy = ControlPolicy()
        d1 = policy.decide(estimate, MantraControlState.baseline(), 1.0, "d1")
        d2 = policy.decide(estimate, MantraControlState.baseline(), 1.0, "d2")
        self.assertEqual(d1.decision_kind, d2.decision_kind)
        self.assertEqual(d1.proposed_control_state.as_dict(), d2.proposed_control_state.as_dict())

    def test_same_raw_observation_yields_different_calibrated_values_for_different_profiles(self) -> None:
        profile_a, profile_b, _ = build_two_participant_profiles()
        frame = make_observation_frame(eeg_stability=0.65)
        _, values_a = apply_profile_to_observation_frame(frame, profile_a, "participant-a")
        _, values_b = apply_profile_to_observation_frame(frame, profile_b, "participant-b")
        self.assertNotEqual(values_a, values_b)

    def test_control_policy_does_not_directly_inspect_participant_profile(self) -> None:
        sig = inspect.signature(ControlPolicy.decide)
        params = set(sig.parameters.keys())
        self.assertNotIn("profile_id", params)
        self.assertNotIn("participant_id", params)


class CLM07APIAndSmokeTests(unittest.TestCase):
    """API endpoints and smoke scenarios."""

    def setUp(self) -> None:
        self.client = make_test_client()
        self.headers = auth_headers()

    def tearDown(self) -> None:
        self.client.close()

    def _create_calibration(self, participant_id: str = "anon-smoke") -> dict:
        payload = {
            "participant_id": participant_id,
            "sensor_family": "fc11",
            "sensor_config_fingerprint": "fc11.default",
            "parser_version": "fc11.parser.v1",
            "feature_schema_version": "clm07.schema.v1",
        }
        r = self.client.post("/api/v1/calibrations", json=payload, headers=self.headers)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_api_create_and_get_calibration(self) -> None:
        s = self._create_calibration()
        get = self.client.get(f"/api/v1/calibrations/{s['session_id']}", headers=self.headers)
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["session_id"], s["session_id"])

    def test_api_readiness_blocks_without_sensor_config(self) -> None:
        r = self.client.post(
            "/api/v1/calibrations",
            json={"participant_id": "readiness-p"},
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 201)
        sid = r.json()["session_id"]
        readiness = self.client.get(f"/api/v1/calibrations/{sid}/readiness", headers=self.headers)
        self.assertEqual(readiness.status_code, 200)
        body = readiness.json()
        self.assertFalse(body["ready"])
        self.assertTrue(body["blocking_reasons"])

    def test_api_lifecycle_creates_profile(self) -> None:
        s = self._create_calibration("api-p1")
        sid = s["session_id"]
        self.client.post(f"/api/v1/calibrations/{sid}/prepare", headers=self.headers)
        self.client.post(f"/api/v1/calibrations/{sid}/start", headers=self.headers)
        stop = self.client.post(f"/api/v1/calibrations/{sid}/stop", headers=self.headers)
        self.assertEqual(stop.status_code, 200)
        body = stop.json()
        self.assertIn("profile_id", body)

    def test_api_invalidates_profile_requires_reason(self) -> None:
        s = self._create_calibration("api-p2")
        sid = s["session_id"]
        self.client.post(f"/api/v1/calibrations/{sid}/prepare", headers=self.headers)
        self.client.post(f"/api/v1/calibrations/{sid}/start", headers=self.headers)
        stop = self.client.post(f"/api/v1/calibrations/{sid}/stop", headers=self.headers)
        profile_id = stop.json()["profile_id"]
        r = self.client.post(
            f"/api/v1/participants/api-p2/calibration-profiles/{profile_id}/invalidate",
            json={},
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 400)

    def test_api_mutation_is_idempotent(self) -> None:
        payload = {
            "participant_id": "idemp-p",
            "idempotency_key": "key-1",
        }
        r1 = self.client.post("/api/v1/calibrations", json=payload, headers=self.headers)
        r2 = self.client.post("/api/v1/calibrations", json=payload, headers=self.headers)
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r1.json()["session_id"], r2.json()["session_id"])

    def test_session_pins_profile_at_creation(self) -> None:
        s = self._create_calibration("pin-p")
        sid = s["session_id"]
        self.client.post(f"/api/v1/calibrations/{sid}/prepare", headers=self.headers)
        self.client.post(f"/api/v1/calibrations/{sid}/start", headers=self.headers)
        stop = self.client.post(f"/api/v1/calibrations/{sid}/stop", headers=self.headers)
        profile_id = stop.json()["profile_id"]

        r = self.client.post(
            "/api/v1/sessions",
            json={
                "learner_id": "pin-p",
                "mode": "synthetic",
                "parameters": {
                    "participant_id": "pin-p",
                    "sensor_family": "fc11",
                    "sensor_config_fingerprint": "fc11.default",
                    "parser_version": "fc11.parser.v1",
                    "feature_schema_version": "clm07.schema.v1",
                },
            },
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["calibration_profile_id"], profile_id)

    def test_calibrated_observations_reconstruct_raw_and_profile(self) -> None:
        profile = build_valid_profile("p-ev")
        frame = make_observation_frame()
        calibrated, _ = apply_profile_to_observation_frame(frame, profile, "p-ev")
        for obs in calibrated:
            self.assertIn(frame.observation_frame_id, obs.provenance)
            self.assertIn(profile.profile_id, obs.provenance)

    def test_profile_events_reconstruct_source_sessions(self) -> None:
        profile = build_valid_profile("p-ev2")
        self.assertIn(profile.source_session_ids[0], profile.provenance)


if __name__ == "__main__":
    unittest.main()
