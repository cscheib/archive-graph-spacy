# Feature Specification: Phase and Temporal Outputs

**Feature Branch**: `007-phase-temporal-outputs`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "Begin planning the next phase and get a spec started."

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-10

- Q: What Phase 4 contract shape should the initial upstream output use? → A: One `phases` table plus separate child tables for central people, dominant themes, temporal pairs, and representative interactions.
- Q: What rule should create inferred phase boundaries in the first implementation? → A: Time-gap segmentation with deterministic merge rules.
- Q: What shape should the initial temporal pair contract use within each phase? → A: Publish phase-bounded pair summary rows plus bounded pair-evidence rows.
- Q: How should the first implementation handle weak or low-evidence temporal segments? → A: Suppress them from published phase outputs and record them in diagnostics.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish First-Class Phase Outputs (Priority: P1)

A downstream Phase 4 consumer needs explicit phase-oriented `nlpdata` outputs so
life-phase exploration is backed by deterministic contracts instead of UI-side
reconstruction.

**Why this priority**: This is the minimum upstream slice required before the
main UI can offer phase-oriented discovery without inventing local phase
semantics.

**Independent Test**: Run `build_nlpdata` on a bounded fixture bundle spanning
multiple time periods and verify that the emitted phase tables support phase
list/detail exploration with provenance-bearing metrics and representative
interaction references.

**Acceptance Scenarios**:

1. **Given** a bounded bundle with interactions spanning multiple time periods,
   **When** `build_nlpdata` completes, **Then** it publishes one stable phase
   surface that identifies inferred temporal segments for the owner-centric
   archive.
2. **Given** a published phase row, **When** a downstream consumer reads only
   `nlpdata`, **Then** it can recover the phase label surrogate, time bounds,
   representative interaction refs, and provenance fields without recomputing
   segmentation logic.
3. **Given** the same bounded scope is rerun, **When** phase derivation
   completes again, **Then** stable phase identifiers and phase ordering remain
   deterministic for unchanged inputs.

---

### User Story 2 - Publish Temporal Relationship and Centrality Outputs (Priority: P2)

A downstream Phase 4 consumer needs per-phase people, themes, and pair activity
outputs so it can explain who and what defined each phase without ad hoc joins
over raw messages.

**Why this priority**: Phase rows alone are not sufficient for the intended UI;
the upstream contract also has to expose central people, dominant themes, and
per-pair activity per phase.

**Independent Test**: Build `nlpdata` for a bounded fixture bundle and verify
that each phase can be joined to central people, dominant themes, and temporal
pair outputs using only published Phase 4 artifacts.

**Acceptance Scenarios**:

1. **Given** a phase with multiple people and themes, **When** the temporal
   aggregation flow completes, **Then** the published outputs identify the most
   central people and dominant themes for that phase with provenance-bearing
   scores.
2. **Given** a canonical pair that appears across multiple inferred phases,
   **When** temporal relationship outputs are published, **Then** downstream
   consumers can see phase-bounded pair strength or activity without
   recomputing pair semantics from raw message rows.
3. **Given** a downstream consumer rendering one phase detail view, **When** it
   joins the phase-oriented outputs, **Then** it can support the Phase 4 MVP
   flow for central people, dominant themes, representative interactions, and
   per-pair activity using upstream contracts only.

---

### User Story 3 - Publish Phase Diagnostics and Boundary Explanations (Priority: P3)

An operator needs diagnostics that explain how a phase boundary or temporal
claim was derived so Phase 4 remains explainable and safe to iterate on.

**Why this priority**: Phase outputs are only trustworthy if they remain
provenance-backed and diagnosable rather than opaque segmentation artifacts.

**Independent Test**: Run the phase derivation flow on a bounded fixture and
verify that diagnostics expose segmentation inputs, representative evidence, and
suppression or fallback behavior for weak phases.

**Acceptance Scenarios**:

1. **Given** a weak or borderline temporal segment, **When** phase diagnostics
   are produced, **Then** the output clearly shows whether the phase was
   retained, merged, or suppressed and why.
2. **Given** a published phase-level claim about a person, theme, or pair,
   **When** an operator inspects the diagnostics surface, **Then** the claim
   remains explainable through bounded representative evidence rather than
   opaque aggregate scores alone.
3. **Given** a bounded rerun with unchanged inputs, **When** diagnostics are
   emitted, **Then** their counts and representative evidence ordering remain
   deterministic.

### Edge Cases

- What happens when the bounded run has too little temporal spread to justify
  more than one inferred phase?
- What happens when multiple temporal segments have weak separation and the
  derivation cannot justify a stable boundary?
- How does the system behave when a person or pair spans several adjacent
  periods with no clear dominant phase?
- What happens when a phase has no strong theme signal but does have clear
  relationship activity?
- How does the system represent a phase that has representative interactions
  but no strongly central people?
- What happens when the current run contains partial or sparse relationship
  outputs because earlier Phase 3 data is missing or suppressed?
- How does the system behave when a previously inferred phase disappears after a
  bounded rerun due to changed upstream scope or reviewed replay effects?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST derive first-class phase-oriented outputs in
  `nlpdata` for owner-centric archive exploration.
- **FR-002**: The initial phase model MUST use inferred temporal segments first
  and MUST defer curated phase labels or manual boundary overrides.
- **FR-002a**: The first implementation MUST infer phase boundaries from
  time-gap segmentation with deterministic merge rules rather than from
  narrative labeling or broad clustering heuristics.
- **FR-003**: The system MUST publish stable phase identifiers, time bounds,
  ordering, and representative interaction references for each inferred phase.
- **FR-003a**: The initial Phase 4 contract MUST use one canonical `phases`
  table plus separate child tables for central people, dominant themes,
  temporal pairs, and representative interactions.
- **FR-004**: The system MUST publish enough phase metadata for downstream
  consumers to support phase list and phase detail exploration without
  recomputing segmentation logic locally.
- **FR-005**: The system MUST publish central-people outputs per phase with
  deterministic ranking and provenance-bearing scores.
- **FR-006**: The system MUST publish dominant-theme outputs per phase with
  deterministic ranking and provenance-bearing scores.
- **FR-007**: The system MUST publish temporal relationship outputs that expose
  per-phase pair activity or strength using canonical pair identifiers from the
  Phase 3 relationship contract.
- **FR-007a**: The initial temporal pair contract MUST publish both
  phase-bounded pair summary rows and bounded pair-evidence rows.
- **FR-008**: The system MUST keep phase-oriented outputs clearly separate from
  canonical truth and MUST NOT imply that inferred phases are manually curated.
- **FR-009**: The system MUST publish diagnostics that explain how phase
  boundaries, central-people rankings, dominant themes, and temporal pair
  claims were derived.
- **FR-010**: The system MUST preserve deterministic rerun semantics for phase
  identifiers, ordering, and representative evidence when the bounded input
  scope is unchanged.
- **FR-011**: The system MUST support the Phase 4 MVP UI flow described in ADR
  005 using upstream contracts only:
  phase list/detail, central people, dominant themes, representative
  interactions, and phase-bounded pair activity.
- **FR-012**: The system MUST define explicit suppression or merge behavior for
  weak or low-evidence temporal segments instead of emitting ambiguous phases as
  if they were equally trustworthy.
- **FR-012a**: Phase merge or suppression behavior MUST be driven by the same
  deterministic time-gap and merge rules used to form initial temporal
  segments.
- **FR-012b**: The initial implementation MUST suppress weak or low-evidence
  temporal segments from the published phase contract and MUST record the
  suppression reason in diagnostics.
- **FR-013**: The system MUST document how the published Phase 4 outputs are
  intended to be consumed by `archive-graph-data#78`.
- **FR-014**: The system MUST keep representative interactions, temporal pair
  evidence, and diagnostics bounded by deterministic selection rules rather
  than emitting exhaustive phase-level history.

### Key Entities *(include if feature involves data)*

- **Phase**: An inferred owner-centric temporal segment with a stable phase id,
  ordering metadata, time bounds, representative interaction refs, and
  provenance-bearing diagnostics.
- **Phase Boundary Rule**: The deterministic time-gap and merge logic that
  decides where one inferred phase ends and the next begins.
- **Phase Aggregate Table**: A child-table output keyed by `phase_id` for one
  aggregate family such as central people, dominant themes, temporal pairs, or
  representative interactions.
- **Phase Membership**: A derived relation connecting messages, people, themes,
  or pairs to one inferred phase.
- **Phase Central Person**: A ranked person-level aggregate within a phase,
  representing who most defines that segment by bounded evidence-backed scores.
- **Phase Theme Summary**: A ranked theme-level aggregate within a phase,
  representing the dominant topics or subject matter of that segment.
- **Temporal Pair Output**: A phase-bounded aggregate for a canonical person
  pair that captures pair activity or strength within an inferred phase.
- **Temporal Pair Evidence**: A bounded evidence surface for one temporal pair
  within one phase, sufficient to explain why that pair is active or strong in
  the segment.
- **Phase Diagnostics Record**: A provenance-bearing explanation artifact for
  boundaries, retained or suppressed phases, representative evidence, and
  aggregation rationale.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `README.md`, `docs/adr/005-phase-first-class-object.md`,
  new quickstart/contract artifacts under
  `specs/007-phase-temporal-outputs/`
- **Behavior Change Summary**: Document the first explicit Phase 4 upstream
  contract, the initial owner-centric inferred phase model, and the handoff
  boundary to `archive-graph-data#78`
- **Local Test Plan**: Add fixture-driven tests for phase derivation, temporal
  pair outputs, diagnostics behavior, deploy/view contracts, and rerun
  determinism; run focused phase tests plus the full local regression suite

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/006-phase-output-contract.md`
- **Architectural Scope**: Introduces the first concrete table-level Phase 4
  contract for inferred phases, temporal relationship outputs, and their
  diagnostics

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A bounded fixture derivation emits deterministic phase-oriented
  outputs that support at least one complete phase detail exploration scenario
  using only published `nlpdata` artifacts.
- **SC-002**: Re-running the same bounded fixture without input changes
  preserves phase identifiers, ordering, and representative evidence ordering.
- **SC-003**: Every published phase, central-person, dominant-theme, and
  temporal-pair claim can be traced to bounded representative evidence or
  diagnostics outputs.
- **SC-004**: The resulting contract is sufficient for `archive-graph-data#78`
  to plan against without requiring local recomputation of phase boundaries or
  temporal pair semantics.
- **SC-005**: A bounded fixture derivation emits capped representative
  interactions, capped temporal pair evidence, and bounded diagnostics using
  deterministic selection rules rather than exhaustive output.
