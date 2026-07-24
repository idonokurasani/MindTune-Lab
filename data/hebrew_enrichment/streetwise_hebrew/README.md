# Streetwise Hebrew Enrichment

Status: populated enrichment layer; every imported record remains `draft_unverified`.

Streetwise contributes evidence about living usage, register, roots, idioms, audio and
context. It does not overwrite Citizen Cafe cards and it does not enter MLF Core.

## Real Sources

- Public RSS: `https://streetwisehebrew.libsyn.com/swh.rss`
- Official TLV1 index: `https://tlv1.fm/podcasts/streetwise-hebrew-show/`
- Immutable RSS archive: `raw/STREETWISE_HEBREW_RSS_2026-07-15.xml`
- Verified offline seed: `STREETWISE_VERIFIED_EPISODE_SEED_v0.2.json`

Archive SHA-256: `5a3f7a9698fbbb06695fa13fb0b2319a2e8a0a25c0f31f3833e5e9e5c672354e`.

The RSS parser creates one source record per episode. The verified seed preserves a
small, traceable subset of public episode metadata and lexical examples so the layer
can be rebuilt even when local network access is unavailable.

## Rebuild From The Public Feed

```bash
python3 mindtune_console/scripts/import_streetwise_enrichment.py \
  --source-list mindtune_console/data/hebrew_enrichment/streetwise_hebrew/STREETWISE_SOURCE_SEED_v0.1.csv \
  --include-status selected \
  --max-pages 1
```

## Rebuild From The Verified Snapshot

```bash
python3 mindtune_console/scripts/import_streetwise_enrichment.py \
  --file mindtune_console/data/hebrew_enrichment/streetwise_hebrew/STREETWISE_VERIFIED_EPISODE_SEED_v0.2.json \
  --max-pages 1
```

## Outputs

- `STREETWISE_HEBREW_RAW_SOURCES_v0.1.json`: source and episode provenance.
- `STREETWISE_HEBREW_LEXICAL_EVIDENCE_v0.2.jsonl`: Hebrew usage evidence independent of Citizen Cafe.
- `STREETWISE_HEBREW_MATCHES_v0.1.jsonl`: conservative links to canonical cards.
- `STREETWISE_HEBREW_ENRICHMENT_CANDIDATES_v0.1.json`: candidate context records.
- `STREETWISE_HEBREW_REVIEW_QUEUE_v0.1.csv`: human review queue.
- `STREETWISE_IMPORT_REPORT_v0.2.md`: latest import statistics.

No item may be shown as verified linguistic truth until reviewed. Single-word links
require an exact lexical match; phrase links use controlled phrase matching.
