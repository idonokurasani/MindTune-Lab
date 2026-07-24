from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

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
                "ready_count": 5,
                "total_count": 8,
                "operational_ready_count": 5,
                "operational_total_count": 5,
                "source_summary_label": "5/5 fonti operative · 2/2 supporto locale · Azure non configurata",
            }),
        ):
            result = server.hebrew_recovery_plan_state(30)

        plan = result["plan"]
        self.assertEqual(sum(phase["minutes"] for phase in plan["phases"]), 30)
        self.assertEqual(plan["evidence"]["resources_ready"], 5)
        self.assertEqual(plan["evidence"]["resources_total"], 5)
        self.assertEqual(plan["evidence"]["resources_label"], "5/5 fonti operative · 2/2 supporto locale · Azure non configurata")
        self.assertEqual(plan["active_increment"], "morphological_production")
        self.assertEqual(plan["source_policy"]["citizen_cafe"], "legacy_personal_archive_only")

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

    def test_source_registry_separates_operational_support_and_runtime_sources(self) -> None:
        result = server.hebrew_source_registry_state()

        by_id = {source["source_id"]: source for source in result["sources"]}
        self.assertEqual(by_id["pealim"]["source_category"], "operational")
        self.assertTrue(by_id["pealim"]["active_for_recovery"])
        self.assertEqual(by_id["hebrew_wordnet_shuly"]["source_category"], "operational")
        self.assertEqual(by_id["citizen_cafe_archive"]["source_category"], "support")
        self.assertFalse(by_id["citizen_cafe_archive"]["active_for_recovery"])
        self.assertEqual(by_id["nnlp_hebrew_resources"]["source_category"], "support")
        self.assertFalse(by_id["nnlp_hebrew_resources"]["active_for_recovery"])
        self.assertEqual(by_id["azure_speech"]["source_category"], "optional_runtime")
        self.assertFalse(by_id["azure_speech"]["active_for_recovery"])
        self.assertEqual(result["operational_total_count"], 5)
        self.assertIn("fonti operative", result["source_summary_label"])


if __name__ == "__main__":
    unittest.main()
