# ADR 001: NLP Search Workspace Boundary

## Status

Accepted

## Context

The project needs a dedicated derived workspace for person-centric and
theme-aware search over archive interactions. Canonical archive data,
classifications, and overrides already exist upstream and should remain the
system of record. This repository owns experimentation and the new `nlpdata`
derivation behavior.

## Decision

Implement the `nlpdata` pipeline in `archive-graph-spacy` and treat
`graph-data` as a read-only upstream source of canonical interactions, people,
classifications, and overrides.

The first rollout is intentionally narrow:

- message-level records only
- derived search fields plus source references, not duplicated full text
- normalized evidence tables plus one denormalized search surface
- deterministic theme tagging and confidence-based suppression
- run metadata for every refresh

For Databricks-managed refreshes, source reads and table writes run inside the
Databricks job with Spark SQL. The Databricks SDK remains limited to control
plane work such as lightweight validation, orchestration, and bundle-adjacent
queries.

## Consequences

Positive:

- keeps canonical and derived concerns separate
- supports local testing before any deployment
- preserves provenance and rerun traceability
- reuses existing extraction/linking code rather than introducing a second NLP
  stack
- avoids SQL Statements API inline result limits during large source reads by
  using Spark SQL in the job runtime

Negative:

- local JSONL derivation is only a validation surface, not the final deployment
  target
- thread-level retrieval remains out of scope in v1
- deterministic theme tags will need later review if broader semantic coverage
  becomes necessary
- Databricks refresh logic now has two execution surfaces to maintain:
  local Python validation and Spark-based bundle execution

## Alternatives Considered

- Implement the pipeline inside `graph-data`
  - rejected because `graph-data` remains read-only for this feature
- Duplicate full message text into the search workspace
  - rejected due to privacy, storage, and drift concerns
- Build thread-level search documents in v1
  - rejected as premature complexity
- Read large source slices through the Databricks SQL Statements API
  - rejected because inline result limits and client-side result shipping are a
    poor fit for full-refresh or yearly backfill workloads
- Require operators to launch each historical backfill window manually
  - rejected because the agreed date windows are deterministic and should be
    expressed as a bundle-managed sequential job
