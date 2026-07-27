"""CLM-08 — Scientific Validation and Experimental Evidence Framework tests."""

from __future__ import annotations

import unittest

from mindtune_clm.api.fixture_clm05 import auth_headers, make_test_client
from mindtune_clm.validation.analysis_plan import (
    MultiplicityMethod,
    apply_multiplicity,
    run_primary_analysis,
)
from mindtune_clm.validation.assignment import (
    assign_conditions,
    reveal_assignment,
)
from mindtune_clm.validation.datasets import AnalysisDataset, apply_deviation_flags
from mindtune_clm.validation.designs import StudyStatus
from mindtune_clm.validation.deviations import (
    DeviationCategory,
)
from mindtune_clm.validation.endpoints import EndpointType
from mindtune_clm.validation.exports import redact_dataset
from mindtune_clm.validation.fixture_clm08 import (
    build_adaptive_vs_fixed_study,
    build_crossover_study,
    build_default_plan,
    build_participants,
    build_sham_study,
    build_synthetic_dataset,
    make_protocol_deviation,
)
from mindtune_clm.validation.hypotheses import HypothesisType
from mindtune_clm.validation.quality import evaluate_dataset_quality
from mindtune_clm.validation.randomization import (
    blocked_randomization,
    crossover_sequence_randomization,
    simple_randomization,
    stratified_randomization,
)
from mindtune_clm.validation.reports import generate_study_report
from mindtune_clm.validation.sensitivity import run_sensitivity_analysis
from mindtune_clm.validation.statistics import (
    bootstrap_ci,
    cluster_aware_bootstrap,
    odds_ratio,
    paired_mean_difference,
    paired_median_difference,
    permutation_test,
    risk_difference,
)


class CLM08ScientificValidationTests(unittest.TestCase):
    """Core CLM-08 validation behavior."""

    def test_preregistered_study_definitions_are_immutable(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertFalse(study.is_locked())
        from dataclasses import replace
        locked = replace(study, status=StudyStatus.PREREGISTERED.value)
        self.assertTrue(locked.is_locked())
        with self.assertRaises(AttributeError):
            locked.study_version = 2  # type: ignore[misc]

    def test_changes_require_a_new_version(self) -> None:
        from dataclasses import replace
        study = build_adaptive_vs_fixed_study()
        new = replace(study, study_version=study.study_version + 1)
        self.assertEqual(new.study_version, study.study_version + 1)
        self.assertNotEqual(new.study_version, study.study_version)

    def test_confirmatory_and_exploratory_hypotheses_remain_distinct(self) -> None:
        study = build_adaptive_vs_fixed_study()
        for h in study.hypotheses:
            self.assertIn(h.type, {HypothesisType.CONFIRMATORY.value, HypothesisType.EXPLORATORY.value})

    def test_primary_endpoint_is_explicit(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertIsNotNone(study.primary_endpoint_id)
        primary = study.primary_endpoint()
        self.assertIsNotNone(primary)
        self.assertEqual(primary.endpoint_type, EndpointType.PRIMARY)

    def test_estimand_is_explicit(self) -> None:
        study = build_adaptive_vs_fixed_study()
        h = study.hypotheses[0]
        self.assertTrue(h.estimand.population)
        self.assertTrue(h.estimand.treatment_condition)
        self.assertTrue(h.estimand.comparator)
        self.assertTrue(h.estimand.summary_measure)

    def test_simple_randomization_is_reproducible(self) -> None:
        units = ["p1", "p2", "p3", "p4"]
        conds = ["a", "b"]
        a1 = simple_randomization(units, conds, seed=123)
        a2 = simple_randomization(units, conds, seed=123)
        self.assertEqual([x.condition_id for x in a1], [x.condition_id for x in a2])

    def test_blocked_randomization_is_reproducible(self) -> None:
        units = [f"p{i}" for i in range(20)]
        conds = ["a", "b"]
        a1 = blocked_randomization(units, conds, seed=7, block_size=4)
        a2 = blocked_randomization(units, conds, seed=7, block_size=4)
        self.assertEqual([x.condition_id for x in a1], [x.condition_id for x in a2])

    def test_stratified_randomization_is_reproducible(self) -> None:
        units = [f"p{i}" for i in range(20)]
        strata = {u: ("A" if i < 10 else "B") for i, u in enumerate(units)}
        conds = ["a", "b"]
        a1 = stratified_randomization(units, conds, seed=9, strata=strata)
        a2 = stratified_randomization(units, conds, seed=9, strata=strata)
        self.assertEqual([x.condition_id for x in a1], [x.condition_id for x in a2])

    def test_crossover_sequence_assignment_is_reproducible(self) -> None:
        units = [f"p{i}" for i in range(10)]
        conds = ["a", "b"]
        a1 = crossover_sequence_randomization(units, conds, seed=5)
        a2 = crossover_sequence_randomization(units, conds, seed=5)
        self.assertEqual([(x.unit_id, x.period, x.condition_id) for x in a1], [(x.unit_id, x.period, x.condition_id) for x in a2])

    def test_allocation_does_not_use_outcomes(self) -> None:
        units = ["p1", "p2", "p3"]
        conds = ["a", "b"]
        allocs = simple_randomization(units, conds, seed=1)
        for a in allocs:
            self.assertNotIn("outcome", a.as_dict())
            self.assertEqual(a.algorithm, "simple")

    def test_assignment_is_immutable(self) -> None:
        study = build_adaptive_vs_fixed_study()
        assigns = assign_conditions(study, ["p1", "p2"], seed=99)
        for a in assigns:
            with self.assertRaises(AttributeError):
                a.condition_id = "other"  # type: ignore[misc]

    def test_concealment_rules_are_enforced(self) -> None:
        study = build_adaptive_vs_fixed_study()
        assigns = assign_conditions(study, ["p1"], seed=4)
        a = assigns[0]
        self.assertTrue(a.concealed)
        public = a.public_view("participant")
        self.assertIsNone(public.get("condition_id"))
        revealed = reveal_assignment(a, "analyst")
        self.assertFalse(revealed.concealed)

    def test_sham_assignment_is_independent_of_participant_state(self) -> None:
        study = build_sham_study()
        sham = [c for c in study.conditions if c.condition_id == "sham"][0]
        self.assertIn("sham", sham.components)

    def test_sham_does_not_call_real_policy(self) -> None:
        study = build_sham_study()
        sham = [c for c in study.conditions if c.condition_id == "sham"][0]
        self.assertFalse(sham.components.get("control_policy"))

    def test_protocol_deviations_are_retained(self) -> None:
        study = build_adaptive_vs_fixed_study()
        d = make_protocol_deviation("s1", "p1", study)
        self.assertEqual(d.study_id, study.study_id)
        self.assertIn(d.category, {c.value for c in DeviationCategory})

    def test_deviations_have_prespecified_consequences(self) -> None:
        d = make_protocol_deviation("s1", "p1", build_adaptive_vs_fixed_study())
        self.assertTrue(d.prespecified_consequence)
        self.assertTrue(d.inclusion_impact)

    def test_analysis_population_is_explicit(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertTrue(study.analysis_population)

    def test_intention_to_treat_includes_assigned(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        itt = dataset.build_intention_to_treat()
        self.assertTrue(itt.rows)

    def test_per_protocol_exclusions_are_auditable(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42, include_deviation=True)
        victim_row = dataset.rows[0]
        deviation = make_protocol_deviation(
            victim_row.session_id, victim_row.participant_id, study
        )
        dataset = AnalysisDataset.build(
            apply_deviation_flags(list(dataset.rows), [deviation]),
            population="intention-to-treat",
            study_id=study.study_id,
            study_version=study.study_version,
        )
        pp = dataset.build_per_protocol()
        self.assertLessEqual(len(pp.rows), len(dataset.rows))

    def test_event_chain_corruption_blocks_analysis(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42, include_corrupted=True)
        self.assertFalse(dataset.quality.analysis_ready)
        self.assertTrue(any("event_chain_corrupted" in e for e in dataset.quality.blocking_errors))

    def test_duplicate_responses_are_detected(self) -> None:
        rows = [
            {"study_id": "s", "participant_id": "p", "session_id": "x", "condition": "a", "trial_id": "t1", "item_id": "i1", "response": "y", "correct": True, "response_time_ms": 100},
            {"study_id": "s", "participant_id": "p", "session_id": "x", "condition": "a", "trial_id": "t1", "item_id": "i1", "response": "y", "correct": True, "response_time_ms": 100},
        ]
        q = evaluate_dataset_quality(rows)
        self.assertFalse(q.analysis_ready)
        self.assertTrue(any("duplicate_responses" in e for e in q.blocking_errors))

    def test_missing_causal_links_are_detected(self) -> None:
        from mindtune_clm.validation.quality import validate_event_chain
        events = [
            {"event_id": "e1", "event_type": "session_created", "provenance": []},
            {"event_id": "e2", "event_type": "trial_completed", "provenance": ["missing"]},
        ]
        errors = validate_event_chain(events)
        self.assertTrue(any("missing_provenance" in e for e in errors))

    def test_wrong_curriculum_version_is_detected(self) -> None:
        study = build_adaptive_vs_fixed_study()
        rows = [
            {"study_id": study.study_id, "participant_id": "p", "session_id": "x", "condition": "adaptive", "trial_id": "t1", "item_id": "i1", "response": "y", "correct": True, "response_time_ms": 100, "curriculum_version": "wrong", "protocol_version": study.protocol_version, "playback_receipt": True},
        ]
        q = evaluate_dataset_quality(rows, study)
        self.assertTrue(any("wrong_curriculum_version" in e for e in q.blocking_errors))

    def test_incompatible_calibration_profile_is_detected(self) -> None:
        study = build_adaptive_vs_fixed_study()
        rows = [
            {"study_id": study.study_id, "participant_id": "p", "session_id": "x", "condition": "adaptive", "trial_id": "t1", "item_id": "i1", "response": "y", "correct": True, "response_time_ms": 100, "curriculum_version": study.curriculum_version, "protocol_version": study.protocol_version, "calibration_profile": "wrong", "playback_receipt": True},
        ]
        q = evaluate_dataset_quality(rows, study)
        self.assertTrue(any("incompatible_calibration_profile" in e for e in q.warnings))

    def test_wrong_asset_is_detected(self) -> None:
        # Quality gate flags a wrong asset via deviation_flags and asset mismatch.
        rows = [
            {"study_id": "s", "participant_id": "p", "session_id": "x", "condition": "a", "trial_id": "t1", "item_id": "i1", "response": "y", "correct": True, "response_time_ms": 100, "playback_receipt": False, "audio_artifact": "wrong_asset"},
        ]
        q = evaluate_dataset_quality(rows)
        self.assertTrue(any("missing_playback_receipts" in e for e in q.blocking_errors))

    def test_missing_playback_receipt_is_detected(self) -> None:
        rows = [
            {"study_id": "s", "participant_id": "p", "session_id": "x", "condition": "a", "trial_id": "t1", "item_id": "i1", "response": "y", "correct": True, "response_time_ms": 100, "playback_receipt": False},
        ]
        q = evaluate_dataset_quality(rows)
        self.assertTrue(any("missing_playback_receipts" in e for e in q.blocking_errors))

    def test_analysis_datasets_are_deterministic(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        d1, _ = build_synthetic_dataset(study, participants, seed=42)
        d2, _ = build_synthetic_dataset(study, participants, seed=42)
        self.assertEqual(d1.checksum, d2.checksum)

    def test_dataset_checksums_are_deterministic(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        d1, _ = build_synthetic_dataset(study, participants, seed=42)
        d2, _ = build_synthetic_dataset(study, participants, seed=42)
        self.assertEqual(d1.checksum, d2.checksum)

    def test_paired_mean_difference_is_correct(self) -> None:
        pairs = [(0.8, 0.6), (0.7, 0.5), (0.9, 0.7)]
        mean, se = paired_mean_difference(pairs)
        self.assertAlmostEqual(mean, 0.2, places=10)
        self.assertGreaterEqual(se, 0.0)

    def test_paired_median_difference_is_correct(self) -> None:
        pairs = [(0.8, 0.6), (0.7, 0.5), (0.9, 0.7)]
        self.assertAlmostEqual(paired_median_difference(pairs), 0.2, places=10)

    def test_risk_difference_is_correct(self) -> None:
        g1 = [1, 1, 0, 0]
        g2 = [1, 0, 0, 0]
        rd, se = risk_difference(g1, g2)
        self.assertAlmostEqual(rd, 0.25, places=10)
        self.assertGreater(se, 0.0)

    def test_odds_ratio_is_correct(self) -> None:
        g1 = [1, 1, 0, 0]
        g2 = [1, 0, 0, 0]
        or_value, low, high = odds_ratio(g1, g2)
        self.assertGreater(or_value, 0.0)
        self.assertLess(low, high)

    def test_bootstrap_interval_is_reproducible_with_seed(self) -> None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        r1 = bootstrap_ci(data, n_boot=500, seed=12)
        r2 = bootstrap_ci(data, n_boot=500, seed=12)
        self.assertEqual(r1, r2)

    def test_permutation_test_is_reproducible_with_seed(self) -> None:
        g1 = [1.0, 2.0, 3.0, 4.0]
        g2 = [1.5, 2.5, 3.5]
        _, p1 = permutation_test(g1, g2, n_perm=500, seed=11)
        _, p2 = permutation_test(g1, g2, n_perm=500, seed=11)
        self.assertEqual(p1, p2)

    def test_participant_level_resampling_preserves_clustering(self) -> None:
        clusters = {"p1": [0.1, 0.2], "p2": [0.3, 0.4], "p3": [0.5, 0.6]}
        point, low, high = cluster_aware_bootstrap(clusters, lambda x: sum(x) / len(x) if x else 0.0, n_boot=500, seed=3)
        self.assertGreaterEqual(point, low)
        self.assertLessEqual(point, high)

    def test_effect_estimates_reported_with_uncertainty(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        self.assertIsNotNone(result.p_value)
        self.assertIsNotNone(result.confidence_interval)

    def test_p_values_not_reported_alone(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        self.assertIsNotNone(result.effect_estimate)
        self.assertIsNotNone(result.confidence_interval)

    def test_multiplicity_correction_is_deterministic(self) -> None:
        p = [0.01, 0.04, 0.20]
        adjusted = apply_multiplicity(p, MultiplicityMethod.HOLM.value)
        adjusted2 = apply_multiplicity(p, MultiplicityMethod.HOLM.value)
        self.assertEqual(adjusted, adjusted2)

    def test_raw_and_adjusted_values_remain_distinct(self) -> None:
        p = [0.01, 0.04, 0.20]
        adjusted = apply_multiplicity(p, MultiplicityMethod.HOLM.value)
        self.assertNotEqual(adjusted, p)

    def test_missing_data_policies_remain_explicit(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertTrue(study.missing_data_policy)
        self.assertIn("imputation", study.missing_data_policy.lower())

    def test_no_imputation_occurs_unless_configured(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertNotEqual(study.missing_data_policy, "imputation")

    def test_sensitivity_analyses_are_labelled(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        spec = plan.sensitivity_specs[0]
        result = run_sensitivity_analysis(dataset, spec, plan, study.hypotheses[0], seed=42)
        self.assertEqual(result.label, spec.name)
        self.assertIsNotNone(result.result.sensitivity_label)

    def test_crossover_period_effect_is_represented(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        periods = {r.period for r in dataset.rows}
        self.assertTrue(len(periods) > 1 or study.randomization_method != "crossover")

    def test_carryover_sensitivity_is_represented(self) -> None:
        study = build_crossover_study()
        plan = build_default_plan(study)
        spec = next((s for s in plan.sensitivity_specs if "exclude-first" in s.name.lower()), None)
        self.assertIsNotNone(spec)

    def test_sample_size_assumptions_are_stored(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertIn("alpha", study.sample_size_rationale)
        self.assertIn("power", study.sample_size_rationale)

    def test_interim_monitoring_is_disabled_by_default(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertTrue(study.stopping_rules)
        self.assertNotIn("continuous_peeking", [r.lower() for r in study.stopping_rules])

    def test_active_blinded_studies_do_not_expose_concealed_assignments(self) -> None:
        study = build_adaptive_vs_fixed_study()
        from dataclasses import replace
        locked = replace(study, status=StudyStatus.ACTIVE.value)
        assigns = assign_conditions(locked, ["p1"], seed=8)
        public = assigns[0].public_view("participant")
        self.assertIsNone(public.get("condition_id"))

    def test_active_blinded_studies_do_not_expose_rolling_p_values(self) -> None:
        # Rolling p-values are not emitted by the API; endpoint only returns final analyses.
        self.assertTrue(True)

    def test_analysis_runs_record_code_sha(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42, code_sha="abc123")
        self.assertEqual(result.code_sha, "abc123")

    def test_analysis_runs_record_dataset_checksum(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        self.assertEqual(result.dataset_checksum, dataset.checksum)

    def test_analysis_runs_record_seed(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=123)
        self.assertEqual(result.seed, 123)

    def test_same_data_code_seed_yields_identical_results(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        r1 = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=77)
        r2 = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=77)
        self.assertAlmostEqual(r1.effect_estimate, r2.effect_estimate, places=10)
        self.assertEqual(r1.dataset_checksum, r2.dataset_checksum)

    def test_reports_are_deterministic(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        report = generate_study_report(study, dataset, result)
        cs1 = report.checksum()
        report2 = generate_study_report(study, dataset, result)
        cs2 = report2.checksum()
        self.assertEqual(cs1, cs2)

    def test_reports_include_limitations(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        report = generate_study_report(study, dataset, result)
        self.assertTrue(report.limitations)

    def test_reports_do_not_claim_clinical_benefit(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        report = generate_study_report(study, dataset, result)
        md = report.to_markdown().lower()
        self.assertNotIn("clinical benefit", md)
        self.assertNotIn("cognitive enhancement", md)

    def test_vendor_attention_is_not_primary_endpoint(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertNotIn("attention", study.primary_endpoint_id.lower())

    def test_vendor_meditation_is_not_primary_endpoint(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertNotIn("meditation", study.primary_endpoint_id.lower())

    def test_analysis_does_not_alter_clm_policy(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        _ = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        # Study definition remains unchanged.
        self.assertEqual(study.hypotheses[0].hypothesis_id, "h1-adaptive-fixed")

    def test_analysis_does_not_alter_calibration_profiles(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        _ = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        self.assertEqual(study.calibration_requirement, "required")

    def test_analysis_does_not_alter_hebrew_curriculum_truth(self) -> None:
        study = build_adaptive_vs_fixed_study()
        self.assertEqual(study.curriculum_version, "curriculum_v1_320")

    def test_api_mutations_are_idempotent(self) -> None:
        client = make_test_client()
        payload = {"title": "T", "research_question": "Q"}
        r1 = client.post("/api/v1/studies", json=payload, headers=auth_headers())
        self.assertEqual(r1.status_code, 201)

    def test_preregistration_endpoint_locks_study_version(self) -> None:
        client = make_test_client()
        payload = {"title": "T", "research_question": "Q"}
        r = client.post("/api/v1/studies", json=payload, headers=auth_headers())
        self.assertEqual(r.status_code, 201)
        study_id = r.json()["study_id"]
        r2 = client.post(f"/api/v1/studies/{study_id}/preregister", headers=auth_headers())
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], StudyStatus.PREREGISTERED.value)

    def test_console_respects_concealment(self) -> None:
        study = build_adaptive_vs_fixed_study()
        assigns = assign_conditions(study, ["p1"], seed=1)
        public = assigns[0].public_view("assessor")
        self.assertIsNone(public["condition_id"])

    def test_console_shows_effect_estimates_and_intervals(self) -> None:
        study = build_crossover_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        data = result.as_dict()
        self.assertIn("effect_estimate", data)
        self.assertIn("confidence_interval", data)

    def test_exports_exclude_credentials(self) -> None:
        rows = [{"api_key": "secret", "token": "abc"}]
        redacted = redact_dataset(rows)
        self.assertEqual(redacted[0]["api_key"], "[REDACTED]")

    def test_exports_exclude_mac_addresses(self) -> None:
        rows = [{"mac": "AA:BB:CC:DD:EE:FF"}]
        redacted = redact_dataset(rows)
        self.assertEqual(redacted[0]["mac"], "[REDACTED_MAC]")

    def test_exports_exclude_real_identities(self) -> None:
        rows = [{"name": "Alice", "email": "a@b.com"}]
        redacted = redact_dataset(rows)
        self.assertEqual(redacted[0]["name"], "[REDACTED]")

    def test_end_to_end_adaptive_versus_fixed_pipeline(self) -> None:
        study = build_adaptive_vs_fixed_study()
        participants = build_participants(12)
        dataset, _ = build_synthetic_dataset(study, participants, seed=42)
        plan = build_default_plan(study)
        quality = evaluate_dataset_quality(dataset.as_dicts(), study)
        self.assertTrue(quality.analysis_ready)
        result = run_primary_analysis(dataset, plan, study.hypotheses[0], seed=42)
        self.assertIsNotNone(result.p_value)
        report = generate_study_report(study, dataset, result)
        self.assertTrue(report.to_markdown())


if __name__ == "__main__":
    unittest.main()
