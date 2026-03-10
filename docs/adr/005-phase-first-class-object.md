# ADR 005: Phase as a First-Class Derived Object

## Status

Accepted

## Context

The original roadmap treated `Person`, `Relationship`, `Interaction`, and
`Phase` as the core exploration objects for the archive. Phase 1 and Phase 2
work established person-centric discovery, relationship views, reviewed
assertion workflows, and diagnostics, but `Phase` still exists only as an idea
in roadmap planning rather than as an explicit cross-repo contract.

The next roadmap issues depend on resolving that gap:

- `archive-graph-spacy#10` Consume reviewed assertions and promoted overrides
  in `nlpdata` derivation
- `archive-graph-spacy#11` Publish relationship-edge outputs and pair
  diagnostics in `nlpdata`
- `archive-graph-spacy#13` Derive life-phase and temporal relationship outputs
  for archive exploration
- `archive-graph-data#78` Add social graph and life-phase exploration surfaces
  in the main UI
- `archive-graph-spacy#12` Add selective embeddings and LLM-assisted aggregate
  enrichment

Phase 3 now provides the prerequisite feedback and relationship surfaces this
ADR depends on:

- reviewed outcomes are consumed read-only during `build_nlpdata`
- `reviewed_effects` capture replay diagnostics for reruns
- `person_person_edges` publish one canonical summary row per pair
- `person_person_edge_evidence` publish bounded supporting pair evidence

Without an explicit `Phase` decision, the repo boundary remains blurry:

- `archive-graph-spacy` could under-publish and force the UI to invent graph
  and temporal semantics locally
- `archive-graph-data` could overfit phase and graph meaning to one UI flow
- later AI enrichment could start before deterministic temporal and graph
  outputs are stable

## Decision

Treat `Phase` as a first-class derived object owned by
`archive-graph-spacy` and consumed by `archive-graph-data`.

This means:

- `archive-graph-spacy` owns deterministic derivation of phase-oriented
  outputs, temporal relationship outputs, and their provenance-bearing
  contracts.
- `archive-graph-data` owns navigation, filtering, review actions,
  presentation, and lightweight composition of those published outputs.
- The UI must not invent new graph or phase semantics that are absent from the
  upstream `nlpdata` contract.

### Phase Model

The initial phase model is:

- inferred temporal segments first
- optional curated labels later
- owner-centric rather than person-specific in the initial rollout
- evidence-backed and provenance-bearing rather than narrative-only

The initial rollout does **not** require manually curated phase boundaries
before any phase surfaces exist.

### Cross-Repo Sequencing

The remaining roadmap order is:

1. `archive-graph-spacy#10`
2. `archive-graph-spacy#11`
3. `archive-graph-spacy#13`
4. `archive-graph-data#78`
5. `archive-graph-spacy#12`

This order is mandatory because:

- reviewed outcomes must affect derivation before later graph and phase outputs
  are trusted
- stable relationship-edge outputs must exist before temporal phase and graph
  exploration is defined
- the UI phase depends on published phase-oriented outputs
- AI enrichment remains optional and must not outrun the deterministic
  contract-bearing pipeline

### Required Upstream Outputs

Before `archive-graph-data#78` can be implemented as more than a thin shell,
`archive-graph-spacy#13` must publish phase-oriented outputs that support at
least:

- phase list/detail exploration
- central people by phase
- dominant themes by phase
- per-pair activity or strength by phase
- representative interaction references by phase
- provenance and diagnostics for how phase-level claims were derived

These outputs may be split across multiple `nlpdata` tables, but they must be
stable enough that the UI does not need to recompute phase boundaries,
relationship shifts, or centrality semantics ad hoc.

### Repo Cut Line

`archive-graph-spacy` is responsible for:

- deterministic scoring and derivation
- temporal segmentation
- graph and pair aggregation
- confidence and provenance propagation
- published Delta/JSONL contracts

`archive-graph-data` is responsible for:

- route structure and page composition
- user filtering and navigation
- rendering summaries from published fields
- drill-down from phase to person, relationship, and interaction views
- review and diagnostics entry points

`archive-graph-data` may format already-published summaries for presentation,
but it must not create hidden semantic layers that change what a phase, edge,
or centrality claim means.

### Phase 4 UI Scope

The first UI phase consuming `Phase` should be limited to:

- phase-oriented discovery
- central people and dominant themes per phase
- representative interactions
- evidence-backed navigation between phase, person, relationship, and
  interaction surfaces

Community exploration, bridge-contact exploration, and broader graph analytics
may follow later in the same epic, but they are not required for the initial
Phase 4 MVP.

### AI Gating

Selective embeddings and LLM-assisted aggregate enrichment remain blocked until
after:

- phase-oriented outputs are published by `archive-graph-spacy#13`
- the UI has consumed them through `archive-graph-data#78`
- deterministic evaluation baselines exist for the new graph and phase
  surfaces

## Consequences

### Positive

- The roadmap regains a clear phase boundary after the completed Phase 2 work.
- `archive-graph-spacy#13` and `archive-graph-data#78` can be designed against
  one shared object model instead of parallel interpretations.
- The UI stays explainable because published provenance-bearing outputs remain
  the source of truth for phase and graph claims.
- Phase 5 AI work stays optional and bounded.

### Negative

- `archive-graph-spacy` must publish additional temporal and graph-oriented
  derived contracts before the Phase 4 UI can advance meaningfully.
- The first phase model may feel conservative because it favors inferred
  segments and provenance over free-form narrative summaries.
- Future curated phase editing or richer community semantics will require
  contract updates after the initial Phase 4 rollout.

## Alternatives Considered

### Let `archive-graph-data` define phases in the UI

Rejected because it duplicates semantic ownership in the presentation layer and
would make phase exploration brittle across reruns and downstream views.

### Require curated phases before any phase exploration exists

Rejected because it delays Phase 4 unnecessarily and blocks evidence-backed
inferred exploration that can already be produced from derived outputs.

### Start AI enrichment before phase and graph outputs stabilize

Rejected because it would push optional, higher-cost enrichment ahead of the
deterministic contracts the rest of the roadmap depends on.

## Deferred Questions

- What exact table-level contracts should `archive-graph-spacy#13` publish for
  phase membership, central people, and temporal relationship shifts?
- Should curated phase labels or boundary overrides live in canonical
  `graph-data` memory tables, in `nlpdata`, or in a separate review surface?
- Which graph primitives become first-class in the initial Phase 4 UI:
  centrality only, centrality plus bridges, or community structure as well?
- What evidence threshold should suppress a weak phase or graph claim from the
  UI entirely?
- What evaluation bar should gate `archive-graph-spacy#12` once deterministic
  phase outputs are live?
