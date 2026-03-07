# Phase 0 Research: NLP Search Workspace

## Decision: Keep `nlpdata` as a derived Delta workspace in the dev catalog

- **Rationale**: The source archive already owns canonical people, interactions,
  and overrides. A separate derived workspace preserves that ownership boundary
  while allowing repeatable NLP refreshes and search-specific denormalization.
- **Alternatives considered**:
  - Write NLP outputs back into existing `gold` tables: rejected because it
    mixes canonical and derived concerns.
  - Keep all outputs as local files only: rejected because the feature goal is a
    searchable dev-catalog workspace.

## Decision: Reuse the existing managed Databricks contract pattern from `graph-data`

- **Rationale**: `graph-data` already centralizes table contracts as logical
  schemas and deploys them through generated DDL backed by registry tests. Using
  the same pattern keeps `nlpdata` consistent with the existing catalog
  governance model.
- **Alternatives considered**:
  - Hand-written table DDL outside the registry model: rejected because it would
    create a parallel contract system.
  - File-only contracts with no registry mapping: rejected because deploy-time
    validation is already schema-registry driven upstream.

## Decision: Use message-level search documents in v1

- **Rationale**: Message-level documents align with the current experimental
  model, keep validation straightforward, and satisfy the search use cases in
  the spec without prematurely introducing thread rollups.
- **Alternatives considered**:
  - Thread-level only documents: rejected because they blur explicit
    interaction-level provenance and make validation harder.
  - Both message-level and thread-level in v1: rejected as unnecessary
    complexity for the first rollout.

## Decision: Store derived search fields plus source references, not duplicated full text

- **Rationale**: Search needs person links, theme tags, time facets, and enough
  derived fields to retrieve relevant interactions, but duplicating full text
  creates unnecessary privacy, storage, and drift risk.
- **Alternatives considered**:
  - Full-text duplication in `nlpdata`: rejected due to duplication and
    governance overhead.
  - No message-level search surface: rejected because the feature requires a
    queryable search-ready dataset.

## Decision: Separate normalized derivation tables from denormalized search documents

- **Rationale**: Normalized tables preserve provenance and make quality review
  possible; a denormalized search document table keeps downstream retrieval
  simple.
- **Alternatives considered**:
  - A single wide search table only: rejected because it obscures evidence and
    weakens debugging.
  - Normalized tables only: rejected because search consumers would need manual
    joins for common retrieval tasks.

## Decision: Make refreshes idempotent by scope and record every run

- **Rationale**: The spec requires repeatable reruns and traceable refreshes.
  Scope-aware reruns with run metadata avoid conflicting current-state records
  and support backfills over bounded slices or the full corpus. The current
  Databricks pattern to mirror is overwrite-based rebuilds for derived tables,
  with truncate or atomic swap behavior when stale current-state rows would
  otherwise survive.
- **Alternatives considered**:
  - Append-only current-state tables: rejected because reruns would leave
    conflicting search records.
  - Full-table rebuild only for every change: rejected because bounded reruns
    are needed for validation and incremental correction.

## Decision: Theme tagging starts with deterministic rules and provenance

- **Rationale**: The project constitution favors minimal complexity, and current
  experiments already rely on explicit extraction/linking logic. Rule-based or
  hybrid theme tagging is enough to validate search usefulness before adopting
  heavier semantic approaches.
- **Alternatives considered**:
  - LLM-only theme tagging: rejected as premature for v1.
  - No themes in v1: rejected because searchable themes are a primary user
    story in the spec.
