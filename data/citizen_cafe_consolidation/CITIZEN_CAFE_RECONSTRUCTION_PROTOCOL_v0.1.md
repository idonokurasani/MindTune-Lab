# Citizen Cafe Reconstruction Protocol v0.1

Citizen Cafe is treated as a fragmented personal re-entry corpus, not as a finished authority.

Its importance in MindTune does not come from being the best available Hebrew
methodology. It comes from Andrea's learning history: it is the main source from
which he previously studied, so it is the most relevant corpus for measuring
re-entry, dormant skills, partial recall and reconstruction of past competence.

The working metaphor is archaeological reconstruction:

- every card is a fragment;
- every source row is a findspot;
- every correction must preserve provenance;
- missing material is reconstructed only when enough evidence exists;
- nothing is frozen without human linguistic review.

## Product Role

Citizen Cafe is a personal-history corpus.

It should answer questions such as:

- Which words and patterns did Andrea once know?
- Which items are still active, partially dormant or lost?
- Which fragments can be recovered quickly with retrieval practice?
- Which gaps are due to bad source material rather than memory failure?
- How does old material reconnect when validated against stronger sources?

It should not answer, by itself:

- What is the canonical Modern Hebrew curriculum?
- What is the correct linguistic form?
- What is the best pedagogical sequence for a new learner?
- What should MLF Core know about Hebrew?

## Evidence Ladder

| Layer | Role | Can Correct | Cannot Do |
|---|---|---|---|
| Raw Citizen Cafe fragments | Personal re-entry skeleton from Andrea's prior study | Source order, deck/color attribution, raw card identity, historical exposure | Decide linguistic truth or general pedagogy alone |
| Source map and audit trail | Provenance | Explain where a card came from | Replace the raw source |
| Academy of the Hebrew Language | Normative authority | Orthography, grammar, terminology, verb/noun tables, transliteration/rulings | Define our pedagogy or Italian translations alone |
| Streetwise Hebrew | Living usage evidence | Register, idiom, real spoken context, phrase plausibility | Become canonical corpus by itself |
| Pealim / morphology cache | Practical verb/root lookup | Working conjugation/root hypotheses | Override Academy or human review |
| Ulpan / university curricula | Pedagogical benchmark | Level order, skill progression, recycling pattern | Supply card-level truth |
| HeLP / psycholinguistic data | Future difficulty and processing evidence | Frequency/difficulty/reaction-time priors | Approve lexical meaning |
| Human Hebrew reviewer | Final domain gate | Approve, reject, split, merge, rewrite | Bypass provenance |

## Field Ownership

| Field | Primary Authority | Secondary Evidence | Review Required |
|---|---|---|---|
| Hebrew spelling | Academy | Citizen Cafe raw, Streetwise usage | Yes if conflict |
| Niqqud removal | MindTune normalization | Academy orthography rules | No, if purely mechanical |
| Root | Academy / morphology source | Pealim cache | Yes |
| Binyan | Academy / morphology source | Pealim cache | Yes |
| Infinitive | Academy / morphology source | Pealim cache | Yes |
| Italian translation | Human review | Citizen Cafe, dictionaries, Streetwise context | Yes |
| Register | Streetwise / human review | Academy usage notes if present | Yes |
| Course color/level | Citizen Cafe | Ulpan/university benchmark | Yes before curriculum freeze |
| Estimated difficulty | Curriculum review | HeLP/frequency/performance data | Yes |
| LearningUnit projection | Hebrew domain adapter | MLF lineage contract | Yes before production |

## Reconstruction States

| State | Meaning | Allowed In Exercises |
|---|---|---|
| `fragment_raw` | Raw piece exists but not normalized | No |
| `candidate_structural` | Hebrew/Italian surfaces look structurally usable | Limited, with draft label |
| `candidate_with_external_evidence` | Supported by Streetwise, Academy, Pealim or similar | Limited |
| `reconstructed_pending_review` | Missing or broken piece repaired with evidence | No, until reviewed |
| `human_reviewed` | Human linguistic review passed | Yes |
| `curriculum_ready` | Linguistic and pedagogical review passed | Yes |
| `quarantine` | Broken, suspicious, duplicate or unsupported | No |

## Reconstruction Rules

1. Never silently overwrite a raw fragment.
2. Preserve `source_map_ref` for every canonical item.
3. Put every correction into an append-only ledger.
4. Do not merge two cards unless the duplicate evidence is explicit.
5. Do not split a card without creating new derived IDs and linking back to the fragment.
6. Do not use Streetwise as a bulk text corpus; use it as context/evidence.
7. Do not use Academy data as copied card content; use it as authority references and validation.
8. Do not let MLF Core know about Citizen Cafe, Streetwise, Academy, Pealim, Hebrew roots or binyanim.

## Missing-Piece Classes

| Class | Example | Required Evidence |
|---|---|---|
| Broken Hebrew surface | Mojibake, extraction symbol, Latin in Hebrew side | Raw source plus Academy/human correction |
| Broken Italian surface | English residue, nonsense payload, empty back | Human translation, context, source map |
| Morphology missing | Verb with no root/binyan/infinitive | Academy/Pealim lookup plus human review |
| Register missing | Slang/formal/colloquial unknown | Streetwise or human usage note |
| Level uncertainty | Color order not pedagogically justified | Ulpan/university comparison plus performance data |
| Duplicate ambiguity | Same front/back in multiple decks | Source proof and curriculum decision |

## External Source Roles

The Academy of the Hebrew Language is the top normative source for Hebrew form.
Streetwise Hebrew is the stronger living-usage source.
Citizen Cafe is the personal re-entry skeleton to reconstruct.
Ulpan and university methods are curriculum comparators.

This means a Citizen Cafe item becomes solid only when:

1. its raw fragment is traceable;
2. its Hebrew form is structurally clean;
3. its translation is reviewed or strongly supported;
4. morphology/register are marked when relevant;
5. curriculum placement is justified;
6. no blocking quality flags remain.

## Current Status

The current all-course corpus is structurally organized but not archaeologically complete.
It is ready for systematic reconstruction, not for curriculum freeze.
