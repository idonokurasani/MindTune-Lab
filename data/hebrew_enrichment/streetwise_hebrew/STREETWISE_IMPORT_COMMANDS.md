# Streetwise Hebrew Import Commands

Streetwise Hebrew is an enrichment layer, not a canonical corpus.

The importer must not modify:

- Citizen Cafe canonical cards;
- MLF Core;
- SQLite schemas;
- UI;
- Hebrew production LearningUnits.

## 1. Add Sources

Edit:

```text
mindtune_console/data/hebrew_enrichment/streetwise_hebrew/STREETWISE_SOURCE_SEED_v0.1.csv
```

Use `import_status=queued` or `import_status=selected` only for sources you want to process.

For saved pages, use `file_path`.
For online pages, use `url`.

## 2. Preview Sources

```bash
python3 mindtune_console/scripts/import_streetwise_enrichment.py \
  --source-list mindtune_console/data/hebrew_enrichment/streetwise_hebrew/STREETWISE_SOURCE_SEED_v0.1.csv \
  --dry-run
```

## 3. Import Selected Sources

```bash
python3 mindtune_console/scripts/import_streetwise_enrichment.py \
  --source-list mindtune_console/data/hebrew_enrichment/streetwise_hebrew/STREETWISE_SOURCE_SEED_v0.1.csv \
  --include-status queued \
  --include-status selected \
  --max-pages 5
```

## 4. Import One Saved HTML Page

```bash
python3 mindtune_console/scripts/import_streetwise_enrichment.py \
  --file /absolute/path/to/saved_streetwise_page.html
```

The same `--file` option accepts `.rss`, `.xml` and the verified Streetwise JSON
snapshot. RSS/XML inputs are split into one source record per episode.

## 5. Outputs

Default output directory:

```text
mindtune_console/data/hebrew_enrichment/streetwise_hebrew/
```

Generated files:

- `STREETWISE_HEBREW_IMPORT_MANIFEST_v0.1.json`
- `STREETWISE_HEBREW_RAW_SOURCES_v0.1.json`
- `STREETWISE_HEBREW_MATCHES_v0.1.jsonl`
- `STREETWISE_HEBREW_ENRICHMENT_CANDIDATES_v0.1.json`
- `STREETWISE_HEBREW_REVIEW_QUEUE_v0.1.csv`
- `STREETWISE_HEBREW_LEXICAL_EVIDENCE_v0.2.jsonl`
- `STREETWISE_IMPORT_REPORT_v0.2.md`

## 6. Review Gate

Anything imported from Streetwise remains `draft_unverified`.

No Streetwise enrichment may be used inside exercises until reviewed and explicitly promoted by a later Hebrew-domain step.
