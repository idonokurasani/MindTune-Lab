from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESOURCE_ROOT = ROOT / "mindtune_console" / "data" / "hebrew_resources"


class HebrewVendorResourceTests(unittest.TestCase):
    def test_wordnet_compact_index_is_hebrew_and_semantic(self) -> None:
        payload = json.loads((RESOURCE_ROOT / "derived" / "hebrew_wordnet_compact.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["source"]["commit"], "55a814bad768206ca2679f10337fe63a7f8540f9")
        self.assertGreater(len(payload["lemmas"]), 5_000)
        self.assertGreater(len(payload["synsets"]), 5_000)
        self.assertGreater(len(payload["relations"]), 20_000)
        self.assertIn("בית", payload["lemmas"])
        self.assertIn("automatic translation truth", payload["policy"])

    def test_nnlp_verb_resource_is_validated_but_not_prompt_truth(self) -> None:
        payload = json.loads((RESOURCE_ROOT / "derived" / "nnlp_verb_index.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["source"]["commit"], "84d5db034fba56c27786b7c645d77370223263c3")
        self.assertGreater(payload["summary"]["verb_index_rows"], 4_000)
        self.assertGreater(payload["summary"]["inflected_form_rows"], 240_000)
        self.assertIn("Pealim remains", payload["policy"])

    def test_validation_report_preserves_scope_limits(self) -> None:
        report = json.loads((RESOURCE_ROOT / "validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["overall_status"], "validated_with_declared_scope_limits")
        self.assertEqual(report["hebrew_wordnet"]["status"], "validated_with_scope_limits")
        self.assertEqual(report["nnlp_hebrew_resources"]["invalid_hebrew_forms"], 0)


if __name__ == "__main__":
    unittest.main()
