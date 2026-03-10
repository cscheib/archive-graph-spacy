# ADR 006: Phase Output Contract

## Status

Accepted

## Context

ADR 005 established `Phase` as a first-class derived object owned by
`archive-graph-spacy`, but it deferred the exact table-level contract for
Phase 4. Without a concrete contract, downstream UI planning in
`archive-graph-data#78` would still depend on implicit reconstruction of phase
boundaries, central people, theme summaries, and temporal pair activity.

Phase 3 already established the prerequisites this contract depends on:

- reviewed feedback is consumed read-only during `build_nlpdata`
- `person_person_edges` publish canonical pair identity
- `person_person_edge_evidence` publish bounded relationship evidence

Phase 4 needs to build on those outputs without introducing a separate
segmentation pipeline or a UI-owned temporal model.

## Decision

Publish Phase 4 through the existing `build_nlpdata` contract as:

- one canonical `phases` table
- child tables for:
  - `phase_central_people`
  - `phase_theme_summaries`
  - `phase_pair_summaries`
  - `phase_pair_evidence`
  - `phase_representative_interactions`
  - `phase_diagnostics`

### Boundary Formation

The initial boundary model is deterministic:

- sort timestamped interactions in bounded run order
- retain a phase boundary only when the time gap exceeds the retained-gap
  threshold
- record medium-size candidate gaps as merged boundary decisions
- suppress weak segments from the published phase contract instead of emitting
  placeholder low-confidence phases

### Pair Reuse

Phase-bounded relationship outputs reuse canonical Phase 3 `pair_id` identity
from `person_person_edges`. Phase 4 may re-aggregate pair activity within a
segment, but it must not invent a second pair-identity model.

### Boundedness

Representative interactions, temporal pair evidence, and diagnostics are
explicitly bounded and deterministic:

- representative interactions are capped per phase
- temporal pair evidence is capped per phase pair and per phase
- diagnostics remain explanation-oriented, not exhaustive

## Consequences

### Positive

- `archive-graph-data#78` can consume a stable upstream phase contract without
  recomputing temporal semantics.
- Phase rows and child aggregates remain explainable because every published
  claim points to representative interactions, pair evidence, or diagnostics.
- The implementation stays inside the current `build_nlpdata` and deploy path.

### Negative

- The first phase model is intentionally conservative and owner-centric.
- Weak segments are suppressed, so operators must inspect diagnostics to see
  what was omitted.
- Future curated labels or boundary overrides will require contract evolution.

## Alternatives Considered

### Publish only phase membership rows

Rejected because downstream consumers would have to rebuild centrality, themes,
pair activity, and representative interactions locally.

### Publish one wide `phases` row with embedded arrays

Rejected because it would make queryability and Spark/Delta contract management
more awkward than small explicit child tables.

### Emit weak phases with low-confidence markers

Rejected because that would put ambiguous temporal segments into the main
contract instead of keeping them diagnosable but suppressed.
