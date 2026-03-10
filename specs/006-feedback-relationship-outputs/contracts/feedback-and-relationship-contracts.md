# Contract: Feedback Consumption and Relationship Outputs

## Purpose

Define the Phase 3 contract for consuming reviewed outcomes during derivation,
publishing pairwise relationship outputs, and extending the candidate
assertion system without creating parallel review paths.

## Related Issues

- Intended to close `archive-graph-spacy#10`
- Intended to close `archive-graph-spacy#11`
- Covers the first implementation slice of `archive-graph-spacy#14`
- Unblocks `archive-graph-spacy#13`

## Reviewed-Input Consumption Contract

- `archive-graph-spacy` reads reviewed inputs directly from:
  - `memory.reviewed_assertions`
  - `memory.review_assertion_decisions`
- `memory.reviewed_assertions` is the semantic source of reviewed outcomes.
- `memory.review_assertion_decisions` is supporting or audit state.
- Reviewed inputs remain read-only inside `archive-graph-spacy`.
- Each derivation run must record the reviewed-input read boundary it used in
  run diagnostics.

## Replay Matching Contract

- Replay is based on semantic identity, not prior candidate IDs.
- The replay key must include:
  - candidate assertion family
  - normalized subject identity
  - normalized claim payload
  - generation or scope discriminator
  - evidence-window anchor
- Replay tolerance is limited to bounded evidence-window drift.
- Broad fuzzy matching is out of scope.

## Reviewed-Effect Result Contract

Every reviewed input considered during derivation must resolve to one of:

| Result | Meaning |
|--------|---------|
| `applied` | Reviewed outcome changed derived behavior for this run |
| `suppressed` | Rejected or resolved prior review prevented re-emission for the same semantic case |
| `skipped` | Replay-safe application could not be established for this run |
| `conflicted` | A replay-matched accepted reviewed outcome materially disagreed with current derivation and was not auto-applied |
| `ignored` | The reviewed input was out of scope, unsupported, stale, or intentionally not considered |

## Relationship Output Contract

The initial published pairwise contract must contain exactly two primary
artifacts:

### `person_person_edges`

One canonical summary row per unordered person pair containing at least:

- `pair_id`
- `person_a_id`
- `person_b_id`
- `run_id`
- `generation_scope`
- `strength_score`
- `relationship_signal`
- direct and indirect evidence counts
- strongest evidence pointer
- `is_current`

### `person_person_edge_evidence`

Bounded supporting evidence rows containing at least:

- `pair_evidence_id`
- `pair_id`
- `evidence_family`
- `source_ref`
- `message_ref`
- `contribution_score`
- `rank_within_pair`
- provenance fields sufficient to trace back to message-level artifacts

## Bounded Evidence Rules

- Evidence must be representative, not exhaustive.
- Selection must be deterministic across reruns of the same bounded scope.
- Evidence should be capped by explicit rules per pair and evidence family.
- Summary rows must expose counts that make truncation or hidden additional
  evidence understandable.

## Candidate-Family Expansion Contract

- Additional candidate families must use the shared candidate schema and the
  same reviewed lifecycle as the original v1 families.
- The first additional family in this Phase 3 slice is
  `relationship_evidence_review`.
- `relationship_evidence_review` is:
  - `reviewable`
  - `derived_only`
  - pair-scoped
  - replayable through the same semantic replay model

## Diagnostics Requirements

Run diagnostics must expose, at minimum:

- reviewed-effect counts by result category
- emitted and suppressed counts by candidate family
- pair row and evidence row counts
- counts by relationship evidence family
- bounded-evidence truncation or suppression counts
- a small representative sample of candidate IDs and pair IDs

## Non-Goals

- no canonical mutation of `graph-data` source tables
- no second durable reviewed-state store inside `archive-graph-spacy`
- no separate relationship review queue outside candidate assertions
- no multi-facet or multi-row-per-pair relationship summary model in the first pass
