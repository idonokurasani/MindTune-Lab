# Citizen Cafe All Courses - Source Audit v1.1

Generated: `2026-07-15T05:13:16+00:00`

This audit promotes only the current MindTune runtime seed candidates, then preserves source lineage into source_map_ref.

## Gate Rule

- Empty Hebrew or empty translation: quarantine.
- Hebrew detected in Italian back side: quarantine.
- Mojibake/extraction symbols and suspicious translation payloads: quarantine.
- Duplicate exact `(deck, Hebrew, Italian)` in promoted seed: quarantine duplicate.
- Any existing audit/source flag remains visible in canonical quality_flags.

## Not A Linguistic Approval

These artifacts are normalized and structured, not frozen. Human linguistic review remains required before declaring the corpus approved.
