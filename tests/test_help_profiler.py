from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import sys

CONSOLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSOLE_DIR))

import help_profiler


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class HeLPProfilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        lexical = self.root / "lexical.csv"
        ld = self.root / "ld.csv"
        naming = self.root / "naming.csv"
        write_csv(
            lexical,
            ["word", "lexicality", "frequency", "word_length", "orthographic_neighborhood_density", "phonological_entropy", "clitic_count", "semitic_structure"],
            [
                {"word": "שמע", "lexicality": "word", "frequency": 42, "word_length": 3},
                {"word": "כתב", "lexicality": "word", "frequency": 31, "word_length": 3},
            ],
        )
        write_csv(
            ld,
            ["word_key", "stimulus_type", "ld_trials", "ld_median_rt", "ld_mean_rt", "ld_sd_rt", "ld_accuracy"],
            [{"word_key": "שמע", "stimulus_type": "word", "ld_trials": 20, "ld_median_rt": 640, "ld_accuracy": 0.95}],
        )
        write_csv(
            naming,
            ["word_key", "naming_trials", "naming_valid_trials", "naming_median_rt", "naming_mean_rt", "naming_sd_rt", "naming_accuracy"],
            [{"word_key": "שמע", "naming_trials": 10, "naming_valid_trials": 9, "naming_median_rt": 510, "naming_accuracy": 0.9}],
        )
        self.norms = help_profiler.HeLPNorms(lexical, ld, naming)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exact_norm_match_is_not_personal_competence(self) -> None:
        item = self.norms.item("שָׁמַע")
        self.assertTrue(item["matched"])
        self.assertEqual(item["match_type"], "exact_normalized_form")
        self.assertIn("non sono una misura della competenza personale", item["interpretation"])

        missing = self.norms.item("לאקיים")
        self.assertFalse(missing["matched"])
        self.assertIn("non implica", missing["interpretation"])

    def test_root_normalization_discards_non_hebrew_source_notes(self) -> None:
        contaminated = "ל-מ-דThis verb is stative. It is conjugated with a patach."
        self.assertEqual(help_profiler.normalize_hebrew_root(contaminated), "למד")
        observation = help_profiler._observation(
            source="test",
            source_ref="event-1",
            session_ref="session-1",
            item_ref="verb-learn",
            word="ללמוד",
            outcome="correct",
            latency_ms=500,
            root=contaminated,
        )
        self.assertEqual(observation["root"], "למד")
        self.assertNotIn("This", observation["root"])

    def test_repeated_recall_events_remain_distinct_and_unlock_only_after_threshold(self) -> None:
        events = []
        items = [
            {"id": "a", "raw_front": "שמע", "events": [], "next_due_at": 0},
            {"id": "b", "raw_front": "כתב", "events": [], "next_due_at": 0},
        ]
        for index in range(8):
            item = items[index % 2]
            event = {
                "at": 1000 + index,
                "label": f"2026-07-{10 + index // 4:02d} 10:00",
                "item_id": item["id"],
                "front": item["raw_front"],
                "result": "miss" if index in {1, 5} else "correct",
                "latency_s": 1.0 + index / 10,
                "eeg_annotation": {"jsonl": f"session-{1 + index // 4}.jsonl"},
            }
            item["events"].append(event)
            events.append(event)
        memory = {"items": items, "events": events}
        profile = help_profiler.build_profile(
            norms=self.norms,
            memory=memory,
            eeg_sessions_dir=self.root / "eeg",
            shoresh_sessions_dir=self.root / "shoresh",
            mlf_db_path=self.root / "missing.sqlite",
            learner_id="andrea",
        )
        self.assertEqual(profile["evidence"]["eligible_observation_count"], 8)
        self.assertEqual(profile["evidence"]["distinct_session_count"], 2)
        self.assertEqual(profile["evidence"]["distinct_item_count"], 2)
        self.assertEqual(profile["evidence"]["status"], "preliminary")
        self.assertTrue(profile["adaptive_candidates"])
        self.assertIn("priority_components", profile["adaptive_candidates"][0])
        self.assertIn("personal_recall", profile["adaptive_candidates"][0]["priority_components"])
        self.assertEqual(len(profile["session_summaries"]), 2)

        short_profile = help_profiler.build_profile(
            norms=self.norms,
            memory={"items": items, "events": events[:7]},
            eeg_sessions_dir=self.root / "eeg",
            shoresh_sessions_dir=self.root / "shoresh",
            mlf_db_path=self.root / "missing.sqlite",
            learner_id="andrea",
        )
        self.assertEqual(short_profile["evidence"]["status"], "insufficient_data")
        self.assertEqual(short_profile["adaptive_candidates"], [])

    def test_mlf_projection_uses_terminal_valid_score_correction(self) -> None:
        db = self.root / "mlf.sqlite"
        connection = sqlite3.connect(db)
        connection.execute(
            "CREATE TABLE events (event_id TEXT, event_type TEXT, timestamp TEXT, monotonic_ns INTEGER, session_id TEXT, unit_id TEXT, payload_json TEXT)"
        )
        rows = [
            ("start", "trial.start", 1, {"trial_id": "t1"}),
            ("response", "trial.response", 2, {"trial_id": "t1", "response_raw": "שמע", "response_normalized": "שמע"}),
            ("score-0", "trial.score", 3, {"trial_id": "t1", "outcome": "incorrect", "correction_sequence": 0, "score_metadata": {"hebrew": {"root": "שמע", "binyan": "paal"}}}),
            ("score-1", "trial.score", 4, {"trial_id": "t1", "outcome": "correct", "correction_of_event_id": "score-0", "correction_sequence": 1, "score_metadata": {"hebrew": {"root": "שמע", "binyan": "paal"}}}),
            ("malformed", "trial.score", 5, {"trial_id": "t1", "outcome": "incorrect", "correction_of_event_id": "not-latest", "correction_sequence": 2}),
            ("start-2", "trial.start", 6, {"trial_id": "t2"}),
            ("response-2", "trial.response", 7, {"trial_id": "t2", "response_raw": "כתב"}),
            ("score-unknown", "trial.score", 8, {"trial_id": "t2", "outcome": "unknown", "correction_sequence": 0}),
        ]
        for event_id, event_type, order, payload in rows:
            connection.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event_id, event_type, f"2026-07-15T10:00:0{order}Z", order, "s1", "u1", json.dumps(payload)),
            )
        connection.commit()
        connection.close()

        observations = help_profiler.mlf_observations(db)
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["source_ref"], "score-1")
        self.assertEqual(observations[0]["outcome"], "correct")
        self.assertEqual(observations[0]["root"], "שמע")

    def test_conjugation_events_are_read_without_eeg_and_deduplicated_by_event_id(self) -> None:
        eeg = self.root / "eeg"
        local = self.root / "behavioral"
        eeg.mkdir()
        local.mkdir()
        event = {
            "event_id": "answer-1",
            "timestamp": "2026-07-19T10:00:00Z",
            "ok": True,
            "reaction_time_ms": 1250,
            "expected": "אכל",
            "expected_phrase": "הוא אכל",
            "verb_id": "verb-eat",
            "root": "אכל",
            "binyan": "paal",
            "input_mode": "speech_to_text",
            "speech_recognition": {
                "provider": "azure_speech",
                "recognition_confidence": 0.91,
                "duration_ms": 820,
            },
        }
        row = {
            "behavioral_event_id": "answer-1",
            "behavioral_session_id": "conjugation-local-1",
            "type": "conjugation_response",
            "event": event,
        }
        (local / "conjugation-local-1.events.jsonl").write_text(
            json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (eeg / "session_duplicate.events.jsonl").write_text(
            json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        observations = help_profiler.conjugation_observations(eeg, local)
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["source_ref"], "answer-1")
        self.assertEqual(observations[0]["session_ref"], "conjugation-local-1")
        self.assertEqual(observations[0]["outcome"], "correct")
        self.assertEqual(observations[0]["latency_ms"], 1250.0)
        self.assertEqual(observations[0]["input_mode"], "speech_to_text")
        self.assertEqual(observations[0]["transcription_provider"], "azure_speech")
        self.assertEqual(observations[0]["transcription_confidence"], 0.91)

        profile = help_profiler.build_profile(
            norms=self.norms,
            memory={"items": [], "events": []},
            eeg_sessions_dir=eeg,
            behavioral_events_dir=local,
            shoresh_sessions_dir=self.root / "shoresh",
            mlf_db_path=self.root / "missing.sqlite",
            learner_id="andrea",
        )
        speech_summary = profile["input_mode_summaries"][0]
        self.assertEqual(speech_summary["input_mode"], "speech_to_text")
        self.assertEqual(speech_summary["median_transcription_confidence"], 0.91)
        self.assertTrue(any("not Hebrew pronunciation quality" in note for note in profile["notes"]))

    def test_recovery_events_feed_help_without_counting_warmup_or_summaries(self) -> None:
        eeg = self.root / "eeg"
        local = self.root / "behavioral"
        eeg.mkdir()
        local.mkdir()
        rows = []
        for index in range(8):
            verb_id = "verb-eat" if index % 2 == 0 else "verb-write"
            event_type = (
                "hebrew_recovery_lexical_response"
                if index < 4
                else "hebrew_recovery_comprehension_response"
            )
            rows.append({
                "behavioral_event_id": f"recovery-{index}",
                "behavioral_session_id": f"recovery-session-{1 + index // 4}",
                "type": event_type,
                "event": {
                    "event_id": f"recovery-{index}",
                    "timestamp": f"2026-07-21T10:00:0{index}Z",
                    "correct": index not in {1, 5},
                    "reaction_time_ms": 800 + index * 100,
                    "verb_id": verb_id,
                    "infinitive": "לאכול" if verb_id == "verb-eat" else "לכתוב",
                    "phrase": "הוא אוכל" if verb_id == "verb-eat" else "היא כותבת",
                    "root": "אכל" if verb_id == "verb-eat" else "כתב",
                    "binyan": "paal",
                },
            })
        rows.extend([
            {
                "behavioral_event_id": "warmup-1",
                "behavioral_session_id": "recovery-session-1",
                "type": "hebrew_recovery_activation_response",
                "event": {"correct": False, "reaction_time_ms": 9999},
            },
            {
                "behavioral_event_id": "summary-1",
                "behavioral_session_id": "recovery-session-2",
                "type": "hebrew_recovery_session_completed",
                "event": {"before_accuracy": 0, "after_accuracy": 0},
            },
        ])
        payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        (local / "recovery.events.jsonl").write_text(payload, encoding="utf-8")
        (eeg / "duplicate.events.jsonl").write_text(payload, encoding="utf-8")

        observations = help_profiler.recovery_observations(eeg, local)
        self.assertEqual(len(observations), 8)
        self.assertEqual({row["session_ref"] for row in observations}, {"recovery-session-1", "recovery-session-2"})
        self.assertEqual({row["item_ref"] for row in observations}, {"verb-eat", "verb-write"})
        self.assertTrue(all(row["binyan"] == "paal" for row in observations))

        profile = help_profiler.build_profile(
            norms=self.norms,
            memory={"items": [], "events": []},
            eeg_sessions_dir=eeg,
            behavioral_events_dir=local,
            shoresh_sessions_dir=self.root / "shoresh",
            mlf_db_path=self.root / "missing.sqlite",
            learner_id="andrea",
        )
        self.assertEqual(profile["evidence"]["status"], "preliminary")
        self.assertEqual(profile["evidence"]["eligible_observation_count"], 8)
        priorities = {row["item_id"]: row["priority"] for row in profile["adaptive_candidates"]}
        self.assertGreater(priorities["verb-write"], 0)
        self.assertNotIn("warmup-1", {row["source_ref"] for row in observations})


if __name__ == "__main__":
    unittest.main()
