"""Deterministic unit and integration tests for CLM-01."""

from __future__ import annotations

import unittest

from mindtune_clm import (
    ControlDecisionKind,
    ControlLoop,
    MantraActuator,
    MantraControlState,
    ObservationFrame,
    StateEstimator,
    make_clm01_fixture,
)
from mindtune_clm.events import CLM01EventType
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
            self.assertEqual(est.payload["source_observation_frame_id"], obs.payload["observation_frame_id"])
            self.assertEqual(est.payload["source_control_cycle_id"], obs.payload["control_cycle_id"])

    def test_every_estimate_creates_decision(self) -> None:
        est_events = [e for e in self.result.events if e.event_type == CLM01EventType.COGNITIVE_STATE_ESTIMATED]
        dec_events = [e for e in self.result.events if e.event_type == CLM01EventType.CONTROL_DECISION_MADE]
        self.assertEqual(len(est_events), len(dec_events))
        for est, dec in zip(est_events, dec_events, strict=True):
            self.assertIn(str(est.event_id), [str(p) for p in dec.provenance])
            self.assertEqual(dec.payload["estimate_id"], est.payload["estimate_id"])

    def test_sustained_deterioration_creates_apply_decision(self) -> None:
        # Control cycle 3 is the sustained-deterioration cycle.
        cycle = self.result.cycles[2]
        self.assertEqual(cycle.estimate.cognitive_state, CognitiveState.RECOVERY_REQUIRED)
        self.assertEqual(cycle.decision.decision_kind, ControlDecisionKind.APPLY)

    def test_apply_decision_creates_successful_actuation_receipt(self) -> None:
        cycle = self.result.cycles[2]
        self.assertTrue(cycle.receipt.success)
        # First intervention is bounded: assistance should be small, not max.
        self.assertAlmostEqual(cycle.receipt.applied_state.assistance_level, 0.2, places=3)

    def test_next_rendered_stimulus_uses_applied_parameters(self) -> None:
        # The rendered control state following control cycle 3 (render rc-4)
        # must be the applied first-intervention state, not the baseline.
        cycle = self.result.cycles[2]
        rendered = cycle.rendered_control_state
        baseline = MantraControlState.baseline()
        self.assertNotAlmostEqual(rendered.assistance_level, baseline.assistance_level, places=3)
        self.assertAlmostEqual(rendered.assistance_level, 0.2, places=3)
        self.assertEqual(rendered.post_stimulus_pause_ms, 300)
        self.assertAlmostEqual(rendered.tempo_ratio, 0.95, places=3)
        self.assertAlmostEqual(rendered.prosodic_emphasis, 0.1, places=3)

    def test_first_intervention_changes_only_allowed_dimensions(self) -> None:
        """First intervention must not touch repetition, breathing, or vocal energy."""
        cycle = self.result.cycles[2]
        baseline = MantraControlState.baseline()
        applied = cycle.receipt.applied_state
        # Changed dimensions from the bounded first-intervention set.
        self.assertLess(applied.tempo_ratio, baseline.tempo_ratio)
        self.assertGreater(applied.post_stimulus_pause_ms, baseline.post_stimulus_pause_ms)
        self.assertGreater(applied.prosodic_emphasis, baseline.prosodic_emphasis)
        self.assertGreater(applied.assistance_level, baseline.assistance_level)
        # Unchanged dimensions.
        self.assertEqual(applied.repetition_count, baseline.repetition_count)
        self.assertEqual(applied.vocal_energy, baseline.vocal_energy)
        self.assertEqual(applied.breathing_cue, baseline.breathing_cue)

    def test_one_intervention_cannot_jump_to_maximum_assistance(self) -> None:
        cycle = self.result.cycles[2]
        applied = cycle.receipt.applied_state
        self.assertLessEqual(applied.assistance_level, 0.2)
        self.assertLess(applied.assistance_level, 1.0)
        self.assertEqual(applied.repetition_count, 1)
        self.assertFalse(applied.breathing_cue)

    def test_one_noisy_eeg_sample_does_not_trigger_intervention(self) -> None:
        frame = ObservationFrame(
            observation_frame_id="noise-test-1",
            control_cycle_id="noise-cc-1",
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
            control_cycle_id="no-eeg-cc-1",
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
        from mindtune_clm.decision import ControlDecision

        unsafe = MantraControlState(
            tempo_ratio=0.1,
            post_stimulus_pause_ms=10000,
            assistance_level=10.0,
            vocal_energy=2.0,
        )
        decision = ControlDecision(
            decision_id="unsafe-1",
            estimate_id="est-1",
            source_observation_frame_id="obs-1",
            source_control_cycle_id="cc-1",
            decision_kind=ControlDecisionKind.APPLY,
            previous_control_state=MantraControlState.baseline(),
            proposed_control_state=unsafe,
        )
        actuator = MantraActuator()
        receipt = actuator.apply(decision, timestamp=1.0)
        self.assertTrue(receipt.success)
        self.assertGreaterEqual(receipt.applied_state.tempo_ratio, 0.5)
        self.assertLessEqual(receipt.applied_state.post_stimulus_pause_ms, 3000)
        self.assertLessEqual(receipt.applied_state.assistance_level, 1.0)
        self.assertLessEqual(receipt.applied_state.vocal_energy, 1.0)

    def test_recovery_does_not_withdraw_after_one_low_load_sample(self) -> None:
        # Control cycle 5 is the first recovery evidence; assistance must still be maintained.
        cycle = self.result.cycles[4]
        self.assertEqual(cycle.estimate.cognitive_state, CognitiveState.RECOVERING)
        self.assertEqual(cycle.decision.decision_kind, ControlDecisionKind.MAINTAIN)
        self.assertAlmostEqual(cycle.rendered_control_state.assistance_level, 0.2, places=3)

    def test_sustained_recovery_gradually_returns_actuator_toward_baseline(self) -> None:
        # Control cycle 6 withdraws; the final actuator state must be closer to baseline
        # than the first-intervention state and not jump all the way back in one step.
        final = self.result.final_control_state
        baseline = MantraControlState.baseline()
        first = MantraControlState(
            tempo_ratio=0.95,
            post_stimulus_pause_ms=300,
            prosodic_emphasis=0.1,
            assistance_level=0.2,
        )
        # Direction is toward baseline.
        self.assertGreater(final.tempo_ratio, first.tempo_ratio)
        self.assertLess(final.post_stimulus_pause_ms, first.post_stimulus_pause_ms)
        self.assertLess(final.prosodic_emphasis, first.prosodic_emphasis)
        self.assertLess(final.assistance_level, first.assistance_level)
        # Not yet fully back to baseline after one withdrawal step.
        self.assertGreater(final.post_stimulus_pause_ms, baseline.post_stimulus_pause_ms)
        self.assertGreater(final.assistance_level, baseline.assistance_level)

    def test_state_returns_to_baseline_after_sufficient_stable_cycles(self) -> None:
        """After enough low-load cycles, all control parameters return to baseline."""
        # Two high-load cycles trigger recovery_required and apply the first intervention,
        # then ten low-load cycles allow full withdrawal.
        session_id = "recovery-baseline"
        high_frames = [
            ObservationFrame(
                observation_frame_id=f"{session_id}-obs-{i}",
                control_cycle_id=f"{session_id}-cc-{i}",
                session_id=session_id,
                sequence_number=i,
                observation_timestamp=float(i),
                behavioral_latency_ms=2200.0,
                hesitation_score=0.8,
                error_score=0.0,
                eeg_stability=0.4,
                eeg_quality="good",
                available_modalities=["behavioral", "eeg"],
            )
            for i in range(1, 3)
        ]
        low_frames = [
            ObservationFrame(
                observation_frame_id=f"{session_id}-obs-{i}",
                control_cycle_id=f"{session_id}-cc-{i}",
                session_id=session_id,
                sequence_number=i,
                observation_timestamp=float(i),
                behavioral_latency_ms=400.0,
                hesitation_score=0.0,
                error_score=0.0,
                eeg_stability=0.9,
                eeg_quality="good",
                available_modalities=["behavioral", "eeg"],
            )
            for i in range(3, 13)
        ]
        result = ControlLoop().run_session(high_frames + low_frames)
        final = result.final_control_state
        baseline = MantraControlState.baseline()
        self.assertAlmostEqual(final.tempo_ratio, baseline.tempo_ratio, places=3)
        self.assertEqual(final.post_stimulus_pause_ms, baseline.post_stimulus_pause_ms)
        self.assertAlmostEqual(final.prosodic_emphasis, baseline.prosodic_emphasis, places=3)
        self.assertAlmostEqual(final.assistance_level, baseline.assistance_level, places=3)

    def test_all_events_contain_causal_source_ids(self) -> None:
        events = self.result.events
        ids: set[str] = set()
        for event in events:
            for provenance in event.provenance:
                self.assertIn(str(provenance), ids)
            ids.add(str(event.event_id))
        # Every control event after session creation has provenance.
        control_events = [e for e in events if e.event_type in CLM01EventType.all()]
        for event in control_events:
            self.assertTrue(len(event.provenance) > 0)

    def test_causal_graph_is_reconstructable_from_payloads(self) -> None:
        """Critical causal relationships are directly queryable, not only by sequence order."""
        estimate_by_id = {
            e.payload["estimate_id"]: e
            for e in self.result.events
            if e.event_type == CLM01EventType.COGNITIVE_STATE_ESTIMATED
        }
        decision_ids = {
            e.payload["decision_id"]
            for e in self.result.events
            if e.event_type == CLM01EventType.CONTROL_DECISION_MADE
        }
        renders = [e for e in self.result.events if e.event_type == CLM01EventType.ADAPTED_STIMULUS_RENDERED]

        for dec in [e for e in self.result.events if e.event_type == CLM01EventType.CONTROL_DECISION_MADE]:
            # Decision references its estimate.
            self.assertIn(dec.payload["estimate_id"], estimate_by_id)

        for receipt in [e for e in self.result.events if e.event_type == CLM01EventType.ACTUATION_APPLIED]:
            # Receipt references its decision.
            self.assertIn(receipt.payload["decision_id"], decision_ids)

        for render in renders:
            # Render references the actuation receipt and control-state id.
            receipt_id = render.payload.get("actuation_receipt_id")
            if receipt_id:
                matching = [e for e in self.result.events if e.event_type == CLM01EventType.ACTUATION_APPLIED and e.payload.get("command_id") == receipt_id]
                self.assertEqual(len(matching), 1)
                self.assertEqual(
                    render.payload["applied_control_state_id"],
                    matching[0].payload["applied_control_state_id"],
                )

        for outcome in [e for e in self.result.events if e.event_type == CLM01EventType.INTERVENTION_OUTCOME_EVALUATED]:
            # Outcome references the rendered stimulus and the decision.
            self.assertIn(outcome.payload["rendered_stimulus_id"], [r.payload["rendered_stimulus_id"] for r in renders])
            self.assertIn(outcome.payload["decision_id"], decision_ids)

    def test_rendered_stimulus_uses_exact_applied_control_state(self) -> None:
        """No renderer independently recomputes actuator parameters."""
        renders = [e for e in self.result.events if e.event_type == CLM01EventType.ADAPTED_STIMULUS_RENDERED]
        applied = [e for e in self.result.events if e.event_type == CLM01EventType.ACTUATION_APPLIED]
        # Skip the initial baseline render (no receipt).
        for render, receipt in zip(renders[1:], applied, strict=True):
            self.assertEqual(render.payload["control_state"], receipt.payload["applied_state"])
            self.assertEqual(render.payload["applied_control_state_id"], receipt.payload["applied_control_state_id"])

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

    def test_persistent_deterioration_produces_gradual_escalation(self) -> None:
        """After enough consecutive high-load cycles, additional dimensions intensify."""
        session_id = "escalation"
        frames = [
            ObservationFrame(
                observation_frame_id=f"{session_id}-obs-{i}",
                control_cycle_id=f"{session_id}-cc-{i}",
                session_id=session_id,
                sequence_number=i,
                observation_timestamp=float(i),
                behavioral_latency_ms=2200.0,
                hesitation_score=0.8,
                error_score=0.0,
                eeg_stability=0.4,
                eeg_quality="good",
                available_modalities=["behavioral", "eeg"],
            )
            for i in range(1, 6)
        ]
        result = ControlLoop().run_session(frames)
        # Control cycle 2 reaches recovery_required and applies the first intervention.
        # Control cycle 4 (third consecutive high cycle, min_cycles_before_escalation=3) escalates.
        cycle2 = result.cycles[1]
        cycle4 = result.cycles[3]
        self.assertEqual(cycle2.decision.decision_kind, ControlDecisionKind.APPLY)
        self.assertEqual(cycle4.decision.decision_kind, ControlDecisionKind.APPLY)
        # Escalation introduced additional dimensions beyond the first intervention.
        self.assertGreater(cycle4.receipt.applied_state.assistance_level, cycle2.receipt.applied_state.assistance_level)
        self.assertTrue(cycle4.receipt.applied_state.breathing_cue)
        self.assertGreater(cycle4.receipt.applied_state.repetition_count, cycle2.receipt.applied_state.repetition_count)

    def test_acceptance_causal_chain_decision_to_actuation_to_renderer(self) -> None:
        """Principal acceptance test: a decision changes the next rendered stimulus."""
        events = self.result.events

        # Find the apply decision at control cycle 3.
        decisions = [e for e in events if e.event_type == CLM01EventType.CONTROL_DECISION_MADE]
        apply_decision = decisions[2]
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
        # rc-4 is the render produced by control cycle 3 (index 3: rc-1 baseline, rc-2, rc-3, rc-4).
        render_for_rc4 = render_events[3]
        self.assertIn(str(receipt.event_id), [str(p) for p in render_for_rc4.provenance])

        applied_state = receipt.payload["applied_state"]
        rendered_state = render_for_rc4.payload["control_state"]
        self.assertAlmostEqual(applied_state["assistance_level"], 0.2, places=3)
        self.assertEqual(rendered_state["assistance_level"], applied_state["assistance_level"])
        self.assertEqual(rendered_state["tempo_ratio"], applied_state["tempo_ratio"])
        self.assertNotEqual(rendered_state, MantraControlState.baseline().as_dict())


if __name__ == "__main__":
    unittest.main()
