# Contract: Phase and Temporal Outputs

## Purpose

Define the Phase 4 upstream contract for inferred owner-centric phases,
phase-level aggregate outputs, temporal pair activity, and bounded diagnostics.

## Related Issues

- Intended to close `archive-graph-spacy#13`
- Unblocks `archive-graph-data#78`
- Must remain consistent with [ADR 005](../../../docs/adr/005-phase-first-class-object.md)
- The bounded reference fixture for this contract lives in
  `data_samples/phase_temporal_outputs/`

## Core Contract Shape

The initial Phase 4 contract publishes one first-class `phases` table plus
child tables for each major aggregate family.

### `phases`

One canonical row per inferred owner-centric temporal segment containing at
least:

- `phase_id`
- `run_id`
- `generation_scope`
- deterministic phase ordering
- time bounds
- representative interaction pointer
- boundary reason
- `is_current`

### `phase_central_people`

Ranked people per phase containing at least:

- `phase_id`
- `person_id`
- `rank`
- centrality or activity score
- evidence pointer

### `phase_theme_summaries`

Ranked themes per phase containing at least:

- `phase_id`
- `theme_key`
- `rank`
- theme score
- evidence pointer

### `phase_pair_summaries`

Phase-bounded pair aggregates containing at least:

- `phase_id`
- `pair_id`
- pair rank
- activity or strength score
- relationship signal
- strongest evidence pointer

### `phase_pair_evidence`

Bounded evidence rows for one pair within one phase containing at least:

- `phase_id`
- `pair_id`
- `message_ref`
- `source_ref`
- `evidence_family`
- bounded rank
- contribution score

### `phase_representative_interactions`

Bounded interaction references used to explain or summarize a phase, including:

- `phase_id`
- `interaction_ref`
- rank
- selection reason

### `phase_diagnostics`

Bounded diagnostics used for operator explanation, including:

- boundary retention, merge, and suppression results
- representative samples
- reason codes
- aggregate-family diagnostics for central people, themes, and temporal pairs

## Boundary Formation Contract

- Boundary formation must use deterministic time-gap segmentation plus merge
  rules.
- Broad clustering, narrative segmentation, and manual labeling are out of
  scope for the initial contract.
- Weak segments must be suppressed from the published phase tables and recorded
  only in diagnostics.

## Temporal Pair Contract

- Pair identity must reuse the canonical Phase 3 `pair_id`.
- Temporal pair outputs must include both:
  - one phase-bounded summary row per `phase_id` + `pair_id`
  - bounded evidence rows that explain that summary row
- Downstream consumers must not need to recompute pair activity from raw
  messages.

## Determinism and Boundedness Requirements

- Phase ids, ordering, and representative evidence ordering must remain stable
  for unchanged bounded input scope.
- Child-table ranking and evidence selection must be deterministic.
- Representative interactions and pair evidence must be capped by explicit
  selection rules.
- Diagnostics must remain bounded and operator-readable.

## Consumption Boundary for `archive-graph-data#78`

`archive-graph-data` may:

- render phase list and phase detail views
- join phase rows to central people, themes, temporal pairs, and
  representative interactions
- format summaries for presentation

`archive-graph-data` must not:

- recompute phase boundaries locally
- invent alternate temporal pair semantics
- treat inferred phases as curated canonical truth

## Non-Goals

- no curated phase labels or boundary overrides in the initial Phase 4 contract
- no second temporal derivation pipeline outside `build_nlpdata`
- no exhaustive evidence ledger for every phase claim
- no UI-side reconstruction of phase semantics
