# Feature Specification: Feedback Consumption and Relationship Outputs

**Feature Branch**: `006-feedback-relationship-outputs`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "Compose the next roadmap work into as few specifications as possible. For archive-graph-spacy, combine Phase 3 reviewed-feedback consumption, relationship-edge outputs, and the next-step candidate-taxonomy expansion into one specification where possible."

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-10

- Q: Which additional candidate assertion family should be the first non-v1 family in this Phase 3 spec? → A: `relationship_evidence_review`
- Q: How strict should replay matching be when candidate IDs change across reruns? → A: Strict semantic key plus bounded evidence-window tolerance for small rerun drift.
- Q: What relationship-output shape should the initial published contract use? → A: One canonical summary row per pair plus a bounded evidence table.
- Q: How should the system handle an accepted reviewed outcome that materially conflicts with newly derived evidence? → A: Mark the case as `conflicted`, do not auto-apply it, and surface it in diagnostics.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consume Reviewed Feedback During Derivation (Priority: P1)

An operator rerunning `build_nlpdata` needs accepted and rejected reviewed
outcomes from `archive-graph-data` to affect derived outputs deterministically
so resolved cases stop resurfacing as if nothing has been reviewed.

**Why this priority**: This closes the first missing part of the human-feedback
loop and is the dependency that makes later relationship and temporal outputs
trustworthy.

**Independent Test**: Run `build_nlpdata` on a fixture bundle with reviewed
assertions and reviewed decisions present, then rerun the same scope and verify
that accepted outcomes change derived outputs while rejected outcomes suppress
re-emission for the same evidence window.

**Acceptance Scenarios**:

1. **Given** a reviewed relay-sender or disambiguation outcome that is accepted
   for the bounded scope, **When** `build_nlpdata` reruns for that scope,
   **Then** the derived outputs apply the accepted downstream effect allowed by
   the reviewed-assertions contract without mutating canonical source tables.
2. **Given** a reviewed candidate case that has already been rejected or
   otherwise resolved, **When** `build_nlpdata` reruns for the same evidence
   window, **Then** the system suppresses re-emission of that case unless the
   underlying semantics changed enough to make it a materially different case.
3. **Given** reviewed records whose original candidate IDs no longer match the
   regenerated candidates, **When** `build_nlpdata` reruns, **Then** stable
   semantic replay matching still applies or suppresses the reviewed outcome
   deterministically and records the decision in diagnostics.

---

### User Story 2 - Publish Durable Relationship Outputs From nlpdata (Priority: P2)

A downstream consumer needs person-pair relationship outputs to come directly
from `nlpdata` contracts so relationship exploration and later phase work do
not depend on ad hoc UI assembly.

**Why this priority**: Relationship outputs are the next contract-bearing layer
after feedback consumption and are required before Phase 4 phase and temporal
work can be specified cleanly.

**Independent Test**: Build `nlpdata` for a fixture bundle with direct,
indirect, and mention-driven relationships and verify that deterministic
`person_person_edges` and bounded `person_person_edge_evidence` outputs are
published together with enough diagnostics to explain a canonical pair.

**Acceptance Scenarios**:

1. **Given** a bounded derivation run over messages involving multiple people,
   **When** the relationship-output flow completes, **Then** the system
   publishes deterministic aggregated rows for canonical person pairs and a
   bounded evidence surface that explains the strongest signals behind each
   pair.
2. **Given** a downstream consumer requesting a canonical pair from published
   outputs, **When** it reads only `nlpdata` relationship tables, **Then** it
   can recover the pair summary, strength signals, and evidence references
   without recomputing pair semantics from raw message rows.
3. **Given** a rerun of the same bounded scope, **When** relationship outputs
   are regenerated, **Then** publish semantics, identifiers, and diagnostics
   remain deterministic for the affected pair rows.

---

### User Story 3 - Expand the Candidate Assertion Framework for Additional Families (Priority: P3)

A maintainer needs the reviewed-assertion pipeline to grow beyond the initial
relay-sender and disambiguation slice without creating one-off review
mechanisms for each new derived claim family.

**Why this priority**: The roadmap calls for broader human-review inputs, but
the expansion should happen through the same contract and diagnostics model
rather than branching into separate review systems.

**Independent Test**: Add `relationship_evidence_review` as the first
additional non-v1 candidate assertion family in a fixture derivation flow and
verify that it uses the shared candidate schema, diagnostics surfaces, replay
behavior, and reviewed-feedback consumption rules.

**Acceptance Scenarios**:

1. **Given** a `relationship_evidence_review` candidate case beyond the
   initial v1 set, **When** the candidate-generation flow runs, **Then** the
   emitted records use the same reviewed-assertion lifecycle shape,
   diagnostics, and replay rules as the existing candidate families.
2. **Given** a candidate family that is reviewable but not promotion-eligible,
   **When** it is emitted and later reviewed, **Then** the system keeps its
   derived-only boundary explicit and avoids implying canonical promotion.
3. **Given** multiple supported candidate assertion families in the same run,
   **When** diagnostics are produced, **Then** operators can distinguish
   emitted counts, suppressed counts, and reviewed-impact counts per family.

### Edge Cases

- What happens when reviewed records exist for a bounded scope but the semantic
  replay key cannot be reconstructed from current derived evidence?
- What happens when a regenerated candidate matches the same semantic case but
  the supporting evidence window shifted slightly across reruns?
- What happens when an accepted reviewed outcome conflicts with newly derived
  evidence strongly enough that the system cannot apply it cleanly?
- How does the system behave when reviewed input tables are present but only
  partially populated for the current bounded scope?
- What happens when a canonical person pair has only weak or entirely indirect
  relationship evidence and no bounded representative interactions?
- How does the system represent pair outputs when one or both people were
  affected by reviewed disambiguation outcomes during the same run?
- What happens when a newly supported candidate assertion family emits zero
  review-worthy cases for a run?
- How does the system behave when an older reviewed decision exists for a
  candidate family that the current build no longer emits?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST consume reviewed-input tables during
  `build_nlpdata` derivation using `memory.reviewed_assertions` as the semantic
  source and `memory.review_assertion_decisions` as audit or supporting state.
- **FR-002**: The system MUST treat reviewed-input consumption as read-only with
  respect to canonical `graph-data` ownership and MUST NOT mutate canonical
  source tables while applying downstream reviewed effects.
- **FR-003**: The system MUST apply accepted reviewed outcomes only through
  explicit downstream override or enrichment effects allowed by the
  reviewed-assertions contract.
- **FR-004**: The system MUST suppress re-emission of rejected or otherwise
  resolved candidate cases for the same semantic evidence window unless the
  regenerated case is materially different.
- **FR-005**: The system MUST support stable semantic replay matching so
  reviewed outcomes can still be applied when regenerated candidate IDs differ
  across reruns.
- **FR-005a**: Replay matching MUST use a strict semantic key with bounded
  evidence-window tolerance for small rerun drift rather than broad fuzzy
  matching.
- **FR-006**: The system MUST record reviewed-feedback diagnostics that show
  which reviewed records were applied, suppressed, skipped, conflicted, or
  ignored in a run.
- **FR-006a**: When an accepted reviewed outcome materially conflicts with new
  derivation, the system MUST mark the case as `conflicted`, MUST NOT
  auto-apply the reviewed outcome, and MUST surface the conflict in run
  diagnostics.
- **FR-007**: The system MUST publish deterministic relationship outputs for
  canonical person pairs in `nlpdata`.
- **FR-008**: The first relationship-output implementation MUST publish both
  aggregated `person_person_edges` and bounded `person_person_edge_evidence`
  outputs.
- **FR-008a**: The initial published relationship contract MUST use one
  canonical summary row per pair in `person_person_edges` plus a bounded
  supporting evidence table in `person_person_edge_evidence`.
- **FR-009**: Relationship outputs MUST preserve a canonical pair identity,
  joinability back to canonical people, and bounded evidence references to
  source interactions or derived message-level evidence.
- **FR-010**: Relationship outputs MUST expose enough published fields and
  diagnostics for downstream consumers to explain a pair's strongest signals
  without recomputing pair semantics ad hoc.
- **FR-011**: Bounded publish and rerun semantics for relationship outputs MUST
  follow the hardened `nlpdata` publish rules already established by ADR 004.
- **FR-012**: The candidate-assertion pipeline MUST support additional
  reviewable assertion families through the same shared schema, diagnostics,
  reviewed-feedback consumption, and replay model rather than per-family review
  pipelines.
- **FR-013**: The combined Phase 3 implementation MUST add at least one
  additional supported candidate assertion family beyond
  `relay_sender_identity` and `person_link_disambiguation`.
- **FR-013a**: The first additional candidate assertion family in this Phase 3
  spec MUST be `relationship_evidence_review` for uncertain or conflict-prone
  pairwise relationship claims.
- **FR-014**: For each supported candidate assertion family, the system MUST
  define whether it is promotion-eligible or derived-only and expose that
  distinction clearly in emitted candidate outputs and reviewed-effect logic.
- **FR-015**: The system MUST preserve enough run-level diagnostics to show
  emitted, suppressed, reviewed-consumed, conflicted, and ignored counts for
  each supported candidate assertion family.
- **FR-016**: The system MUST document how the new Phase 3 outputs block or
  enable the later Phase 4 phase-oriented derivation work in
  `archive-graph-spacy#13`.

### Non-Functional Requirements

- **NFR-001**: Phase 3 relationship evidence and reviewed-effect diagnostics
  MUST remain bounded by deterministic selection rules and MUST NOT require
  exhaustive full-history evidence emission for a normal bounded rerun.
- **NFR-002**: The implementation MUST preserve the current bounded-run
  operational model by keeping reviewed replay and pair-output generation
  inside the existing `build_nlpdata` pipeline rather than introducing a second
  derivation or review subsystem.

### Key Entities *(include if feature involves data)*

- **Reviewed Input Record**: A durable reviewed assertion or reviewed decision
  loaded from `graph-data`-owned tables and interpreted as a downstream
  read-only input during derivation.
- **Replay Match Key**: A stable semantic key used to match a reviewed outcome
  to regenerated derived evidence when raw candidate IDs are not stable across
  reruns.
- **Replay Tolerance Window**: A bounded allowance for small evidence-window
  drift that still represents the same semantic reviewed case across reruns.
- **Reviewed Effect Result**: A diagnostics-bearing outcome describing whether a
  reviewed input record was applied, suppressed, skipped, conflicted, or
  ignored for the current run.
- **Person-Person Edge**: An aggregated canonical pair row representing
  relationship strength or type signals for two canonical people within the
  bounded derivation scope.
- **Person-Person Edge Evidence**: A bounded evidence surface for a canonical
  pair that references representative interactions, mention patterns, themes,
  and derived support signals without copying full raw interaction history.
- **Candidate Assertion Family**: A reviewable class of proposed derived claim
  sharing one schema and reviewed-lifecycle model but differing in semantics,
  evidence rules, and promotion eligibility.
- **Relationship Evidence Review Candidate**: A reviewable candidate assertion
  for a canonical person pair whose relationship claim remains uncertain,
  conflicting, or operationally important enough to justify human review.

## Assumptions

- This feature combines roadmap issues `archive-graph-spacy#10`,
  `archive-graph-spacy#11`, and the first implementation slice of
  `archive-graph-spacy#14`.
- The reviewed-assertions lifecycle defined in ADR 003 remains the governing
  model for candidate states, promotion boundaries, and reviewed-effect
  semantics.
- The bounded publish and rerun safety rules defined by ADR 004 remain the
  governing model for publishing new Phase 3 outputs.
- Phase-oriented derivation from ADR 005 remains out of scope for this spec and
  will be handled in a later feature after reviewed feedback and relationship
  outputs are stable.
- `archive-graph-data` remains the owner of durable review storage and user
  review workflows, while `archive-graph-spacy` remains the owner of
  deterministic derivation and published `nlpdata` contracts.
- The first additional candidate assertion family added by this feature does
  not need to cover the full future taxonomy, but it must prove that expansion
  works without creating a parallel review system.
- The first expansion step in this spec is `relationship_evidence_review`,
  chosen because it directly exercises the same pairwise outputs introduced by
  this feature.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `README.md`, `docs/adr/003-reviewed-assertions-promotion-model.md`, `docs/adr/005-phase-first-class-object.md`, and the new `specs/006-feedback-relationship-outputs/` planning artifacts
- **Behavior Change Summary**: Documentation must explain how reviewed inputs
  are consumed during derivation, what downstream effects accepted or rejected
  reviewed outcomes have, what relationship outputs are now published, and how
  the expanded candidate-family model stays within the same reviewed lifecycle.
- **Local Test Plan**: Add or update fixture-driven tests for reviewed feedback
  consumption, replay matching, relationship outputs, additional candidate
  assertion families, and publish-safe diagnostics; run `uv run pytest` before
  deployment.

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/003-reviewed-assertions-promotion-model.md` and `docs/adr/005-phase-first-class-object.md`
- **Architectural Scope**: Extends the reviewed-assertion feedback loop into
  active derivation, defines contract-bearing relationship outputs, and fixes
  the Phase 3 boundary that Phase 4 depends on.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a representative fixture bundle with previously reviewed
  relay-sender and disambiguation cases, rerunning `build_nlpdata` changes the
  affected derived outputs deterministically and prevents the same resolved
  cases from resurfacing as fresh unresolved candidates.
- **SC-002**: Maintainers can inspect published relationship outputs for at
  least five representative canonical pairs and identify the pair identity,
  strongest signals, and bounded evidence references without recomputing pair
  semantics from raw message rows.
- **SC-003**: At least one additional candidate assertion family beyond the
  original v1 set runs end to end through shared candidate generation,
  diagnostics, reviewed-state consumption, and replay behavior with no
  separate review pipeline.
- **SC-004**: Run diagnostics let maintainers distinguish applied, suppressed,
  conflicted, skipped, and ignored reviewed outcomes plus emitted and
  suppressed candidate counts per assertion family on a representative fixture
  run.
- **SC-005**: On the representative fixture bundle, bounded evidence and
  reviewed-effect diagnostics remain capped by deterministic selection rules so
  maintainers can inspect the output without requiring exhaustive per-message
  history dumps.
