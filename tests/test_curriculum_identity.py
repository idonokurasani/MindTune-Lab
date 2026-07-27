"""Canonical curriculum identity, provenance, and determinism tests."""

from __future__ import annotations

import json
import subprocess
import unicodedata
import unittest
from pathlib import Path

from mantra.phase1.curriculum import CURRICULUM_PATH, Curriculum


class CurriculumIdentityTests(unittest.TestCase):
    """Guard the stable identity contract for the 320-verb curriculum."""

    def _curriculum(self) -> Curriculum:
        return Curriculum.load(CURRICULUM_PATH)

    def test_320_unique_verb_ids(self) -> None:
        curriculum = self._curriculum()
        ids = [v.verb_id for v in curriculum.verbs]
        self.assertEqual(len(ids), 320)
        self.assertEqual(len(set(ids)), 320)

    def test_verb_id_equals_asset_id_prefix(self) -> None:
        curriculum = self._curriculum()
        for v in curriculum.verbs:
            self.assertEqual(v.verb_id, v.asset_id_prefix)

    def test_asset_id_prefixes_are_ascii_and_lowercase(self) -> None:
        curriculum = self._curriculum()
        for v in curriculum.verbs:
            self.assertTrue(v.asset_id_prefix.isascii())
            self.assertTrue(v.asset_id_prefix.islower())

    def test_infinitive_pointed_is_nfc(self) -> None:
        curriculum = self._curriculum()
        for v in curriculum.verbs:
            self.assertTrue(
                unicodedata.is_normalized("NFC", v.infinitive_pointed),
                f"{v.verb_id} infinitive_pointed is not NFC: {v.infinitive_pointed!r}",
            )

    def test_source_group_key_set_for_all_verbs(self) -> None:
        curriculum = self._curriculum()
        for v in curriculum.verbs:
            self.assertTrue(v.source_group_key)
            self.assertIn("_", v.source_group_key)

    def test_italian_infinitive_explicitly_absent(self) -> None:
        curriculum = self._curriculum()
        for v in curriculum.verbs:
            self.assertIsNone(v.italian_infinitive)

    def test_no_generated_at_timestamp(self) -> None:
        data = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("generated_at", data)

    def test_json_has_320_verbs(self) -> None:
        data = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(data["verbs"]), 320)


class CurriculumDeterminismTests(unittest.TestCase):
    """Generation and audit must be byte-for-byte deterministic."""

    def test_regeneration_is_byte_identical(self) -> None:
        repo_root = CURRICULUM_PATH.resolve().parents[2]
        env = {"PYTHONPATH": str(repo_root)}
        # Use the venv python symlink without resolving it, so the venv path is active.
        python = str(repo_root / ".venv" / "bin" / "python")

        before_curriculum = CURRICULUM_PATH.read_bytes()
        before_audit = Path("data/hebrew/curriculum_v1_320_audit.json").read_bytes()
        before_md = Path("docs/audits/curriculum_v1_320_audit.md").read_bytes()

        result = subprocess.run(
            [python, "scripts/generate_curriculum_320.py"],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr.decode("utf-8", errors="ignore"))
        result = subprocess.run(
            [python, "scripts/audit_curriculum_320.py"],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr.decode("utf-8", errors="ignore"))

        self.assertEqual(CURRICULUM_PATH.read_bytes(), before_curriculum)
        self.assertEqual(
            Path("data/hebrew/curriculum_v1_320_audit.json").read_bytes(), before_audit
        )
        self.assertEqual(Path("docs/audits/curriculum_v1_320_audit.md").read_bytes(), before_md)


class CurriculumMigrationMapTests(unittest.TestCase):
    """The legacy-verb-id migration map is complete and deterministic."""

    def _curriculum(self) -> Curriculum:
        return Curriculum.load(CURRICULUM_PATH)

    def test_migration_map_covers_all_old_and_new_ids(self) -> None:
        migration_path = Path("data/hebrew/curriculum_v1_320_id_migration.json")
        self.assertTrue(migration_path.exists())
        migration = json.loads(migration_path.read_text(encoding="utf-8"))

        curriculum = self._curriculum()
        new_ids = {v.verb_id for v in curriculum.verbs}
        mapped_new: set[str] = set()
        for old_id, new_list in migration.items():
            self.assertIsInstance(old_id, str)
            self.assertIsInstance(new_list, list)
            for nid in new_list:
                self.assertIn(nid, new_ids)
                mapped_new.add(nid)
        self.assertEqual(mapped_new, new_ids)


class CurriculumAuditTests(unittest.TestCase):
    """Audit output must report a clean canonical artifact."""

    def test_audit_reports_zero_blocking_issues(self) -> None:
        audit_path = Path("data/hebrew/curriculum_v1_320_audit.json")
        self.assertTrue(audit_path.exists())
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["summary"]["blocking_issues"], 0)

    def test_audit_reports_zero_duplicate_verb_ids(self) -> None:
        audit = json.loads(
            Path("data/hebrew/curriculum_v1_320_audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(audit["summary"]["duplicate_verb_ids"], 0)

    def test_audit_reports_zero_duplicate_asset_prefixes(self) -> None:
        audit = json.loads(
            Path("data/hebrew/curriculum_v1_320_audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(audit["summary"]["duplicate_asset_id_prefixes"], 0)


if __name__ == "__main__":
    unittest.main()
