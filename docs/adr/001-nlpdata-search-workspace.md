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

## Consequences

Positive:

- keeps canonical and derived concerns separate
- supports local testing before any deployment
- preserves provenance and rerun traceability
- reuses existing extraction/linking code rather than introducing a second NLP
  stack

Negative:

- local JSONL derivation is only a validation surface, not the final deployment
  target
- thread-level retrieval remains out of scope in v1
- deterministic theme tags will need later review if broader semantic coverage
  becomes necessary

## Alternatives Considered

- Implement the pipeline inside `graph-data`
  - rejected because `graph-data` remains read-only for this feature
- Duplicate full message text into the search workspace
  - rejected due to privacy, storage, and drift concerns
- Build thread-level search documents in v1
  - rejected as premature complexity
