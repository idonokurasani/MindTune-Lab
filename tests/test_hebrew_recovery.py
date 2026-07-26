from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CONSOLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSOLE_DIR))

import server


class HebrewRecoveryTests(unittest.TestCase):
    def test_plan_uses_performance_evidence_and_source_readiness(self) -> None:
        profile = {
            "evidence": {
                "status": "preliminary",
                "eligible_observation_count": 18,
                "distinct_session_count": 3,
                "distinct_item_count": 9,
                "source_counts": {"conjugation": 18},
            },
            "performance": {"success_ratio": 0.72},
        }
        with (
            patch.object(server, "help_profile_state", return_value={"profile": profile}),
            patch.object(server, "hebrew_source_registry_state", return_value={
                "ready_count": 4,
                "total_count": 5,
                "operational_ready_count": 4,
                "operational_total_count": 4,
                "source_summary_label": "4/4 fonti operative · 1/1 supporto locale",
            }),
        ):
            result = server.hebrew_recovery_plan_state(30)

        plan = result["plan"]
        self.assertEqual(sum(phase["minutes"] for phase in plan["phases"]), 30)
        self.assertEqual(plan["evidence"]["resources_ready"], 4)
        self.assertEqual(plan["evidence"]["resources_total"], 4)
        self.assertEqual(plan["evidence"]["resources_label"], "4/4 fonti operative · 1/1 supporto locale")
        self.assertEqual(plan["active_increment"], "morphological_production")
        self.assertIn("help", plan["source_policy"])
        self.assertIn("pealim", plan["source_policy"])
        self.assertNotIn("citizen_cafe", plan["source_policy"])
        self.assertNotIn("streetwise", plan["source_policy"])

    def test_source_registry_reports_missing_wordnet_without_fabricating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps({
                    "schema_version": "test/1",
                    "policy": "test",
                    "sources": [{"source_id": "hebrew_wordnet_shuly", "local_status": "catalogued_not_installed"}],
                }),
                encoding="utf-8",
            )
            with (
                patch.object(server, "HEBREW_SOURCE_REGISTRY_FILE", registry),
                patch.object(server, "HEBREW_WORDNET_INDEX_FILE", root / "missing-wordnet.json"),
            ):
                result = server.hebrew_source_registry_state()

        self.assertTrue(result["ok"])
        self.assertFalse(result["sources"][0]["available"])
        self.assertFalse(result["sources"][0]["active_for_recovery"])

    def test_source_registry_drops_legacy_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps({
                    "schema_version": "test/1",
                    "policy": "test",
                    "sources": [
                        {"source_id": "citizen_cafe_archive"},
                        {"source_id": "streetwise_hebrew"},
                        {"source_id": "azure_speech"},
                        {"source_id": "help_lexicon"},
                    ],
                }),
                encoding="utf-8",
            )
            with patch.object(server, "HEBREW_SOURCE_REGISTRY_FILE", registry):
                result = server.hebrew_source_registry_state()

        source_ids = {source["source_id"] for source in result["sources"]}
        self.assertNotIn("citizen_cafe_archive", source_ids)
        self.assertNotIn("streetwise_hebrew", source_ids)
        self.assertNotIn("azure_speech", source_ids)
        self.assertIn("help_lexicon", source_ids)
        self.assertEqual(len(source_ids), 1)

    def test_source_registry_separates_operational_and_support_sources(self) -> None:
        result = server.hebrew_source_registry_state()

        by_id = {source["source_id"]: source for source in result["sources"]}
        self.assertEqual(by_id["pealim"]["source_category"], "operational")
        self.assertTrue(by_id["pealim"]["active_for_recovery"])
        self.assertEqual(by_id["hebrew_wordnet_shuly"]["source_category"], "operational")
        self.assertEqual(by_id["nnlp_hebrew_resources"]["source_category"], "support")
        self.assertFalse(by_id["nnlp_hebrew_resources"]["active_for_recovery"])
        self.assertNotIn("citizen_cafe_archive", by_id)
        self.assertNotIn("streetwise_hebrew", by_id)
        self.assertNotIn("azure_speech", by_id)
        self.assertEqual(result["operational_total_count"], 4)
        self.assertIn("fonti operative", result["source_summary_label"])


if __name__ == "__main__":
    unittest.main()
