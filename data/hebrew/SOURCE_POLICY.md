# Source Policy for the Hebrew Linguistic Engine

## Purpose

Every record consumed or produced by the engine carries a `source_id` and an
explicit `production_eligibility` tier. The runtime must be able to reject any
record that is not eligible for the intended use.

## Eligibility values

- `production_approved` — may be used in production learning content.
- `private_research_only` — may be used inside MindTune Lab for research, but not in externally distributed content.
- `reference_only` — may be consulted for comparison or validation, but must not appear in production records.
- `blocked` — must not be loaded or used.
- `unknown` — not yet classified; treated as blocked until reviewed.

## Filtering rules

1. A record whose `source_id` is not in the registry is rejected.
2. A record whose `production_eligibility` is `blocked` or `unknown` is rejected.
3. A `reference_only` record can be used as `source_evidence` but cannot become a `curriculum_status: approved` record.
4. A `private_research_only` record can be used for internal tooling and experiments, but not for public or commercial distribution.
5. `manual_override` is `production_approved`, but only when the override does not contradict a `blocked` or `reference_only` underlying source in a way that would leak that source's data.
6. A `curriculum-approved` record may only cite `production_approved` sources as its authority.

## Runtime behavior

All loaders and services must accept an optional `source_filter` parameter.
By default, services run in `strict` mode and exclude `reference_only`,
`private_research_only`, `blocked`, and `unknown` sources. For research and
internal validation, `permissive` mode may be used to include all sources.
