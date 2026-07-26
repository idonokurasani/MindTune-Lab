"""Deterministic unit and integration tests for CLM-01."""

from __future__ import annotations

import unittest

from mpe.control import (
    ControlDecisionKind,
    ControlLoop,
    MantraActuator,
    MantraControlState,
    ObservationFrame,
    StateEstimator,
    make_clm01_fixture,
)
from mpe.control.events import CLM01EventType
from mpe.enums import CognitiveState


class CLM01IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frames = make_clm01_fixture()
        self.result = ControlLoop().run_session(self.frames)

    def test_every_observation_creates_state_estimate(self) -> None:
        obs_events = [e for e in self.result.events if e.event_type == CLM01EventType.OBSERVATION_FRAME_CREATED]
        est_events = [e for e in self.result.events if e.event_type == CLM01EventType.COGNITIVE_STATE_ESTIMATED]
        self.assertEqual(len(obs_events), len(self.frames))
        self.assertEqual(len(est_events), len(self.frames))
        for obs, est in zip(obs_events, est_events, strict=True):
            self.assertIn(str(obs.event_id), [str(p) for p in est.provenance])

    def test_every_estimate_creates_decision(self) -> None:
        est_events = [e for e in self.result.events if e.event_type == CLM01EventType.COGNITIVE_STATE_ESTIMATED]
        dec_events = [e for e in self.result.events if e.event_type == CLM01EventType.CONTROL_DECISION_MADE]
        self.assertEqual(len(est_events), len(dec_events))
        for est, dec in zip(est_events, dec_events, strict=True):
            self.assertIn(str(est.event_id), [str(p) for p in dec.provenance])

    def test_sustained_deterioration_creates_apply_decision(self) -> None:
        # Cycle 3 is the sustained-deterioration cycle.
        cycle = self.result.cycles[2]
        self.assertEqual(cycle.estimate.cognitive_state, CognitiveState.RECOVERY_REQUIRED)
        self.assertEqual(cycle.decision.decision_kind, ControlDecisionKind.APPLY)

    def test_apply_decision_creates_successful_actuation_receipt(self) -> None:
        cycle = self.result.cycles[2]
        self.assertTrue(cycle.receipt.success)
        self.assertEqual(cycle.receipt.applied_state.assistance_level, 3)

    def test_next_rendered_stimulus_uses_applied_parameters(self) -> None:
        # The rendered control state following cycle 3 (used for cycle 4) must be
        # the applied assistance state, not the baseline.
        cycle = self.result.cycles[2]
        rendered = cycle.rendered_control_state
        baseline = MantraControlState.baseline()
        self.assertNotEqual(rendered.assistance_level, baseline.assistance_level)
        self.assertEqual(rendered.assistance_level, 3)
        self.assertEqual(rendered.post_stimulus_pause_ms, 1200)
        self.assertEqual(rendered.tempo_ratio, 0.7)

    def test_one_noisy_eeg_sample_does_not_trigger_intervention(self) -> None:
        frame = ObservationFrame(
            observation_frame_id="noise-test-1",
            session_id="noise-session",
            sequence_number=1,
            observation_timestamp=1.0,
            behavioral_latency_ms=400.0,
            hesitation_score=0.1,
            error_score=0.0,
            eeg_stability=0.2,
            eeg_quality="artifact",
            available_modalities=["behavioral", "eeg"],
        )
        estimator = StateEstimator()
        estimate = estimator.estimate(frame)
        self.assertEqual(estimate.cognitive_state, CognitiveState.STABLE)
        self.assertIn("eeg_rejected_low_quality", estimate.reason_codes)

    def test_loop_continues_when_eeg_is_absent(self) -> None:
        frame = ObservationFrame(
            observation_frame_id="no-eeg-1",
            session_id="no-eeg-session",
            sequence_number=1,
            observation_timestamp=1.0,
            behavioral_latency_ms=500.0,
            hesitation_score=0.0,
            error_score=0.0,
            eeg_stability=None,
            eeg_quality=None,
            available_modalities=["behavioral"],
        )
        loop = ControlLoop()
        result = loop.run_session([frame])
        self.assertTrue(len(result.events) > 0)
        self.assertEqual(result.cycles[0].estimate.cognitive_state, CognitiveState.STABLE)

    def test_safety_bounds_cannot_be_exceeded(self) -> None:
        from mpe.control.decision import ControlDecision

        unsafe = MantraControlState(
            tempo_ratio=0.1,
            post_stimulus_pause_ms=10000,
            assistance_level=10,
            vocal_energy=2.0,
        )
        decision = ControlDecision(
            decision_id="unsafe-1",
            decision_kind=ControlDecisionKind.APPLY,
            previous_control_state=MantraControlState.baseline(),
            proposed_control_state=unsafe,
        )
        actuator = MantraActuator()
        receipt = actuator.apply(decision, timestamp=1.0)
        self.assertTrue(receipt.success)
        self.assertGreaterEqual(receipt.applied_state.tempo_ratio, 0.5)
        self.assertLessEqual(receipt.applied_state.post_stimulus_pause_ms, 3000)
        self.assertLessEqual(receipt.applied_state.assistance_level, 5)
        self.assertLessEqual(receipt.applied_state.vocal_energy, 1.0)

    def test_recovery_does_not_withdraw_after_one_low_load_sample(self) -> None:
        # Cycle 5 is the first recovery evidence; assistance must still be maintained.
        cycle = self.result.cycles[4]
        self.assertEqual(cycle.estimate.cognitive_state, CognitiveState.RECOVERING)
        self.assertEqual(cycle.decision.decision_kind, ControlDecisionKind.MAINTAIN)
        self.assertEqual(cycle.rendered_control_state.assistance_level, 3)

    def test_sustained_recovery_gradually_returns_actuator_toward_baseline(self) -> None:
        # Cycle 6 withdraws; the final actuator state must be closer to baseline
        # than the intervention state and not jump all the way back in one step.
        final = self.result.final_control_state
        baseline = MantraControlState.baseline()
        intervention = MantraControlState(
            tempo_ratio=0.7,
            post_stimulus_pause_ms=1200,
            prosodic_emphasis=0.6,
            vocal_energy=0.7,
            breathing_cue=True,
            assistance_level=3,
            repetition_count=2,
        )
        # Direction is toward baseline.
        self.assertGreater(final.tempo_ratio, intervention.tempo_ratio)
        self.assertLess(final.post_stimulus_pause_ms, intervention.post_stimulus_pause_ms)
        self.assertLess(final.prosodic_emphasis, intervention.prosodic_emphasis)
        self.assertLess(final.assistance_level, intervention.assistance_level)
        self.assertLess(final.repetition_count, intervention.repetition_count)
        # Not yet fully back to baseline after one withdrawal step.
        self.assertGreater(final.post_stimulus_pause_ms, baseline.post_stimulus_pause_ms)
        self.assertGreater(final.assistance_level, baseline.assistance_level)

    def test_all_events_contain_causal_source_ids(self) -> None:
        events = self.result.events
        ids = set()
        for event in events:
            for provenance in event.provenance:
                self.assertIn(str(provenance), ids)
            ids.add(str(event.event_id))
        # Every control event after session creation has provenance.
        control_events = [e for e in events if e.event_type in CLM01EventType.all()]
        for event in control_events:
            self.assertTrue(len(event.provenance) > 0)

    def test_fixture_is_deterministic_across_runs(self) -> None:
        result1 = ControlLoop().run_session(make_clm01_fixture())
        result2 = ControlLoop().run_session(make_clm01_fixture())

        self.assertEqual(len(result1.events), len(result2.events))
        self.assertEqual(
            [e.event_type for e in result1.events],
            [e.event_type for e in result2.events],
        )
        self.assertEqual(
            [e.session_sequence_number for e in result1.events],
            [e.session_sequence_number for e in result2.events],
        )
        self.assertEqual(
            result1.final_control_state.as_dict(),
            result2.final_control_state.as_dict(),
        )

    def test_acceptance_causal_chain_decision_to_actuation_to_renderer(self) -> None:
        """Principal acceptance test: a decision changes the next rendered stimulus."""
        events = self.result.events

        # Find the apply decision at cycle 3.
        decisions = [e for e in events if e.event_type == CLM01EventType.CONTROL_DECISION_MADE]
        apply_decision = decisions[2]  # cycle 3
        self.assertEqual(apply_decision.payload["decision_kind"], ControlDecisionKind.APPLY.value)

        # Find the actuation request and receipt that follow the decision.
        request_events = [e for e in events if e.event_type == CLM01EventType.ACTUATION_REQUESTED]
        applied_events = [e for e in events if e.event_type == CLM01EventType.ACTUATION_APPLIED]
        request = request_events[2]
        receipt = applied_events[2]
        self.assertIn(str(apply_decision.event_id), [str(p) for p in request.provenance])
        self.assertTrue(receipt.payload["success"])
        self.assertIn(str(request.event_id), [str(p) for p in receipt.provenance])

        # Find the adapted_stimulus_rendered event that follows the receipt.
        render_events = [e for e in events if e.event_type == CLM01EventType.ADAPTED_STIMULUS_RENDERED]
        # The rendered event for cycle 4 follows the actuation from cycle 3.
        render_for_cycle_4 = render_events[3]
        self.assertIn(str(receipt.event_id), [str(p) for p in render_for_cycle_4.provenance])

        applied_state = receipt.payload["applied_state"]
        rendered_state = render_for_cycle_4.payload["control_state"]
        self.assertEqual(applied_state["assistance_level"], 3)
        self.assertEqual(rendered_state["assistance_level"], applied_state["assistance_level"])
        self.assertEqual(rendered_state["tempo_ratio"], applied_state["tempo_ratio"])
        self.assertNotEqual(rendered_state, MantraControlState.baseline().as_dict())


if __name__ == "__main__":
    unittest.main()
