"""Tests for HeLP (Hebrew Lexicon Project) domain integration."""

from __future__ import annotations

import unittest

from mpe.domains.hebrew.help import HeLPLoader, HeLPProfiler, HeLPRepository


class HeLPLoaderTests(unittest.TestCase):
    def test_loads_help_data_from_default_paths(self) -> None:
        loader = HeLPLoader()
        self.assertGreater(len(loader.forms), 0)
        self.assertGreater(len(loader.summaries), 0)
        self.assertEqual(loader.combined_report()["dataset_version"], "auto")

    def test_forms_report_counts_are_consistent(self) -> None:
        loader = HeLPLoader().load()
        report = loader.forms_report
        self.assertGreaterEqual(report.valid_rows, 0)
        self.assertEqual(report.input_rows, report.valid_rows + report.invalid_rows + report.duplicate_rows)


class HeLPRepositoryTests(unittest.TestCase):
    def test_lookup_by_form_returns_evidence(self) -> None:
        repo = HeLPRepository()
        matches = repo.by_form("אוכל")
        self.assertTrue(matches)
        for ev in matches:
            self.assertEqual(ev.form, "אוכל")
            self.assertTrue(ev.provenance.source_name == "HeLP")

    def test_enrich_entity_attaches_help_evidence(self) -> None:
        from mpe.domains.hebrew.canonical import HebrewLexicalEntity

        repo = HeLPRepository()
        entity = HebrewLexicalEntity(
            entity_id="hebverb_001_infinitive",
            surface_form="לאכול",
            lemma="mangiare",
            root="אכל",
            binyan="paal",
            morphology="infinitive",
            help_verb_summary=None,
        )
        enriched = repo.enrich_entity(entity)
        self.assertTrue(enriched.has_help_evidence)
        self.assertGreaterEqual(len(enriched.help_form_evidence), 1)


class HeLPProfilerTests(unittest.TestCase):
    def test_difficulty_for_unknown_form(self) -> None:
        profiler = HeLPProfiler()
        result = profiler.difficulty_for_form("xyz")
        self.assertFalse(result["known"])

    def test_difficulty_for_known_form(self) -> None:
        profiler = HeLPProfiler()
        result = profiler.difficulty_for_form("אוכל")
        self.assertTrue(result["known"])
        self.assertIn("evidence", result)

    def test_priority_queue_is_deterministic(self) -> None:
        profiler = HeLPProfiler()
        queue1 = profiler.priority_queue(require_help_match=True, top_n=10)
        queue2 = profiler.priority_queue(require_help_match=True, top_n=10)
        self.assertEqual([item.form for item in queue1], [item.form for item in queue2])


if __name__ == "__main__":
    unittest.main()
