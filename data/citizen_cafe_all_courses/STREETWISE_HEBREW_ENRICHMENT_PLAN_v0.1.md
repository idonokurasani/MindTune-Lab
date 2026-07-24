# Streetwise Hebrew Enrichment Plan v0.1

Status: planning only, no production import.

## Sources Verified

- StreetWise Hebrew official site: `https://www.streetwisehebrew.com/`
- StreetWise Hebrew podcast page on TLV1: `https://tlv1.fm/podcasts/streetwise-hebrew-show/`
- StreetWise Hebrew quiz/text page: `https://www.streetwisehebrew.com/quiz.html`
- StreetWise Hebrew snippets page: `https://www.streetwisehebrew.com/snippets1.html`

The source material includes episode pages, short episode descriptions, audio
links, quiz prompts, slang snippets, Hebrew examples, transliterations and
English explanations. Treat these as external learning/enrichment sources, not
as canonical Citizen Cafe translations.

## Role

Streetwise Hebrew must not replace the Citizen Cafe corpus and must not become a
primary source for canonical translations.

Use it as a secondary enrichment layer for:

- colloquial usage;
- register notes;
- example phrases;
- listening/pronunciation references;
- links to external episodes or snippets;
- semantic disambiguation hints when a Citizen Cafe item is ambiguous.

## Boundary

Streetwise material belongs to the Hebrew domain layer, not MLF Core.

Allowed future location:

- `mindtune_console/data/hebrew_enrichment/streetwise_hebrew/`
- later, a Hebrew-domain read model or asset repository.

Not allowed:

- no MLF Core fields for Streetwise;
- no scheduler dependency on Streetwise;
- no overwrite of canonical Citizen Cafe Hebrew or Italian;
- no unreviewed automatic promotion into study cards.

## Proposed Record Shape

```json
{
  "enrichment_id": "streetwise_<stable_hash>",
  "canonical_item_id": "cclex_...",
  "source": "streetwise_hebrew",
  "source_ref": {
    "title": "",
    "url": "",
    "episode_id": "",
    "retrieved_at": ""
  },
  "usage_examples": [
    {
      "hebrew": "",
      "italian_gloss": "",
      "register": "colloquial|neutral|formal|slang|unknown",
      "confidence": "low|medium|high"
    }
  ],
  "audio_refs": [],
  "notes": [],
  "review_status": "draft_unverified"
}
```

## Future Pipeline

1. Keep Citizen Cafe canonical lexical items stable.
2. Build a matching layer by normalized Hebrew form and optional root/binyan.
3. Crawl or import Streetwise pages into raw source records:
   - page URL;
   - title;
   - source type: episode, quiz, snippet, song/video reference;
   - raw Hebrew spans;
   - raw transliteration spans when present;
   - raw English explanation spans;
   - audio URL when present;
   - extraction confidence.
4. Store Streetwise references as enrichment records.
5. Require human review before showing enrichment inside exercises.
6. Use enrichment only in prompts that explicitly request context/listening,
   never in base flashcard recall unless approved.

## Candidate Uses

- Add a "contesto vivo" panel for selected flashcards.
- Build listening prompts using linked episode/audio references.
- Add slang/register warnings to cards whose meaning changes in colloquial use.
- Generate optional production prompts: "use this item in a Streetwise-style
  sentence", clearly marked as enrichment, not canonical corpus.

## Acceptance Criteria

- Removing all Streetwise records must not change Citizen Cafe cards.
- Streetwise records must not change MLF event schema.
- A trial may reference enrichment through optional domain metadata only.
- No Streetwise content is treated as linguistically canonical without review.
