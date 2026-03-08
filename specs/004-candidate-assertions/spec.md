# Feature Specification: Candidate Assertions

**Feature Branch**: `004-candidate-assertions`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Generate high-value candidate assertions from derived enrichment, beginning with relay sender identity inference and ambiguous person-link cases worth review. Emit candidate assertions for inferred relay sender identity and selected mention disambiguation cases, attach evidence, confidence, and provenance, and provide diagnostics or an export surface for downstream review without conflating candidates with canonical truth."

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-08

- Q: What output surface must the first implementation publish for generated candidate assertions? → A: A persisted candidate-assertions output surface plus a human-readable diagnostics summary.
- Q: Which disambiguation cases should emit `person_link_disambiguation` candidates in v1? → A: Only cases with multiple plausible canonical people and no clear winner.
- Q: How should v1 handle duplicate candidate generation across reruns? → A: Within a run, keep one candidate per assertion type, subject, claim, and scope, and regenerate deterministically on rerun.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit Relay Sender Identity Candidates (Priority: P1)

A maintainer needs the enrichment pipeline to emit candidate assertions for
relay sender identity so high-confidence inferred sender mappings can be
reviewed explicitly instead of being buried inside derived outputs.

**Why this priority**: Relay sender identity is the clearest first-wave
promotion-eligible assertion type and provides the fastest path to a usable
review queue.

**Independent Test**: Run the candidate-generation flow on a fixture bundle
with relay-address messages and verify that reviewable candidate assertions are
produced with evidence, provenance, confidence, and no canonical mutation.

**Acceptance Scenarios**:

1. **Given** a message whose sender identity is inferred through relay
   addressing evidence, **When** the candidate-generation flow runs, **Then** a
   `relay_sender_identity` candidate assertion is emitted with the required
   subject reference, claim, evidence, provenance, and confidence fields.
2. **Given** a relay sender inference that lacks the minimum evidence or
   provenance required for review, **When** the flow runs, **Then** no
   reviewable candidate assertion is emitted for that case.

---

### User Story 2 - Surface High-Value Disambiguation Candidates (Priority: P2)

A maintainer needs the enrichment pipeline to emit candidate assertions only
for ambiguous person-link cases worth human review so downstream curation can
see the most valuable disambiguation work without being flooded by low-value
noise.

**Why this priority**: Ambiguous person-link cases are a core downstream review
need, but they should only be emitted when the case is materially useful for
later curation.

**Independent Test**: Run the candidate-generation flow on a fixture bundle
with mixed mention-link outcomes and verify that only the selected
high-value ambiguous cases produce `person_link_disambiguation` candidates.

**Acceptance Scenarios**:

1. **Given** a mention-link case that matches the selected high-value
   ambiguity criteria, **When** the flow runs, **Then** a
   `person_link_disambiguation` candidate assertion is emitted with evidence,
   provenance, and confidence.
2. **Given** a low-value or already-clear person-link case, **When** the flow
   runs, **Then** the system does not emit a reviewable disambiguation
   candidate assertion for that case.

---

### User Story 3 - Publish Reviewable Candidate Outputs (Priority: P3)

A downstream maintainer needs a diagnostics or export surface for generated
candidate assertions so review systems can inspect, validate, and hand off the
candidate set without treating it as canonical truth.

**Why this priority**: Candidate generation is not useful unless downstream
consumers can inspect the outputs in a bounded, reviewable form.

**Independent Test**: Generate candidate assertions from a fixture bundle and
verify that the resulting diagnostics or export surface exposes the candidate
payloads, types, and counts clearly enough for downstream review planning.

**Acceptance Scenarios**:

1. **Given** generated candidate assertions, **When** a maintainer inspects the
   diagnostics or export surface, **Then** they can identify the assertion
   type, proposed claim, evidence, provenance, and confidence for each emitted
   candidate.
2. **Given** a downstream reviewer reading the exported candidates, **When**
   they inspect the output, **Then** it is clear that the records are
   candidate assertions for review and not accepted reviewed assertions or
   canonical overrides.

### Edge Cases

- What happens when multiple candidate relay sender identities compete for the
  same subject and none clearly exceeds the high-value threshold?
- How does the system handle ambiguous person-link cases whose evidence is
  partially present but provenance is incomplete?
- What happens when the same underlying evidence would produce duplicate
  candidate assertions across reruns of the same derived bundle?
- How does the system represent a review-worthy candidate whose confidence is
  intentionally low but whose ambiguity is still operationally important?
- What happens when downstream diagnostics are requested for a bundle that
  produces zero review-worthy candidates?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST emit candidate assertions only for the initial
  assertion types already defined by the reviewed-assertions model:
  `relay_sender_identity` and `person_link_disambiguation`.
- **FR-002**: The system MUST emit `relay_sender_identity` candidate assertions
  for review-worthy inferred sender identity cases that satisfy the defined
  evidence and provenance minimums.
- **FR-002a**: In the first implementation, a `relay_sender_identity`
  candidate MUST be emitted only when the case includes a subject canonical ID,
  an unresolved relay-like sender address under review, at least one
  additional supporting link signal beyond the raw sender value, and
  provenance that identifies the source message and derivation path.
- **FR-003**: The system MUST emit `person_link_disambiguation` candidate
  assertions only for selected high-value ambiguous person-link cases worth
  later human review.
- **FR-004**: Every emitted candidate assertion MUST include a durable
  candidate identifier, assertion type, immutable subject canonical ID,
  proposed claim, evidence references, provenance summary, confidence signal,
  generation timestamp, and generation scope.
- **FR-005**: The system MUST define explicit selection rules for which
  disambiguation cases are considered high-value enough to emit as candidate
  assertions.
- **FR-005a**: In the first implementation, `person_link_disambiguation`
  candidates MUST be emitted only when multiple plausible canonical people are
  present and no clear winner can be selected from the derived evidence.
- **FR-006**: The system MUST avoid emitting candidate assertions for cases
  that do not satisfy the minimum review-worthiness rules for evidence,
  provenance, or ambiguity value.
- **FR-007**: The system MUST keep emitted candidate assertions separate from
  accepted reviewed assertions and canonical overrides.
- **FR-008**: The system MUST preserve enough evidence and provenance in each
  candidate assertion for a downstream reviewer to understand why the candidate
  was emitted.
- **FR-009**: The system MUST attach a confidence signal to every emitted
  candidate assertion.
- **FR-010**: The system MUST provide a diagnostics or export surface that
  exposes emitted candidate assertions for downstream review workflows.
- **FR-010a**: The first implementation MUST publish both a persisted
  candidate-assertions output surface for downstream consumption and a
  human-readable diagnostics summary for local validation and inspection.
- **FR-010b**: In the first implementation, the persisted candidate output
  surface MUST be written as `candidate_assertions.jsonl`, and the diagnostics
  summary MUST be written as `candidate_assertions_summary.json` within the
  derived `nlpdata` output directory.
- **FR-011**: The diagnostics or export surface MUST distinguish candidate
  assertions from canonical truth and from later reviewed-assertion lifecycle
  states.
- **FR-012**: The system MUST support rerunning candidate generation on the
  same derived bundle without inventing conflicting candidate payload rules for
  duplicate or repeated evidence.
- **FR-012a**: In the first implementation, candidate identity within a run
  MUST be stable for each `(assertion type, subject canonical ID, proposed
  claim, generation scope)` combination, and reruns of the same scope MUST
  regenerate those candidates deterministically rather than emitting duplicate
  competing records.
- **FR-013**: The system MUST document how emitted candidate assertions map to
  the reviewed-assertions lifecycle contract and the downstream issue
  `archive-graph-data#71`.

### Key Entities *(include if feature involves data)*

- **Candidate Assertion**: A reviewable proposed fact emitted from derived
  enrichment, with a specific assertion type, subject canonical ID, proposed
  claim, evidence, provenance, confidence, and generation metadata.
- **Relay Sender Identity Candidate**: A candidate assertion proposing the
  canonical identity behind a relay-address sender when the evidence is strong
  enough to justify explicit review.
- **Person Link Disambiguation Candidate**: A candidate assertion proposing a
  review-worthy interpretation of an ambiguous mention-to-person link case in
  which multiple plausible canonical people exist and no clear winner can be
  selected.
- **Candidate Diagnostics Export**: A local output or inspection surface that
  exposes the emitted candidate assertions, their payloads, and summary counts
  for downstream review planning.
- **Persisted Candidate Output**: A durable candidate-assertions output surface
  that downstream review workflows can consume without relying on ad hoc local
  inspection.

## Assumptions

- The reviewed-assertions lifecycle defined in `archive-graph-spacy#4` remains
  the governing model for candidate assertion types, review states, and
  promotion boundaries.
- `relay_sender_identity` remains `promotion_eligible`, while
  `person_link_disambiguation` remains reviewable but `derived_only` in the
  initial workflow.
- This feature covers candidate generation and candidate-side export or
  diagnostics in `archive-graph-spacy`; durable human review storage remains in
  `archive-graph-data`.
- The first implementation will provide both a persisted candidate output
  surface and a human-readable diagnostics summary rather than choosing only one
  of those surfaces.
- In the first implementation, those two output artifacts are
  `candidate_assertions.jsonl` and `candidate_assertions_summary.json`.
- The first implementation may rely on fixture-driven local validation rather
  than a full downstream review UI.
- High-value ambiguous person-link cases can be bounded by explicit
  review-worthiness rules without requiring the full future ambiguity taxonomy
  up front.
- In the first implementation, high-value disambiguation means a multi-candidate
  ambiguity with no clear winner, not every low-confidence or heuristic-only
  link case.
- Candidate identity in v1 is stable only within a generation scope and rerun
  of the same scope; broader cross-run historical deduplication can be handled
  later if needed.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `README.md`, `docs/ROADMAP.md`,
  `docs/adr/003-reviewed-assertions-promotion-model.md`, and the new
  `specs/004-candidate-assertions/` planning artifacts
- **Behavior Change Summary**: Documentation must explain which candidate
  assertion types are generated, what minimum payload each candidate carries,
  what makes a case review-worthy, and how the diagnostics or export surface
  maps into the reviewed-assertions workflow.
- **Local Test Plan**: Add or update local automated tests for candidate
  generation behavior and run `uv run pytest` before deployment.

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/003-reviewed-assertions-promotion-model.md`
- **Architectural Scope**: Extends the accepted reviewed-assertions model with
  the first concrete candidate-generation behaviors and candidate-side review
  export boundary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a representative fixture bundle with relay-address sender
  cases, maintainers can identify emitted `relay_sender_identity` candidates
  and confirm each includes the required payload fields with zero ambiguity
  about whether the result is canonical truth.
- **SC-002**: On a representative fixture bundle with mixed person-link cases,
  maintainers can distinguish emitted high-value
  `person_link_disambiguation` candidates from suppressed low-value cases with
  no contradictory interpretation of the selection rules.
- **SC-003**: Maintainers can inspect `candidate_assertions.jsonl` and
  `candidate_assertions_summary.json` and
  identify the assertion type, proposed claim, evidence, provenance, and
  confidence for at least five emitted candidates.
- **SC-004**: Candidate-generation runs produce zero workflow steps where an
  emitted candidate assertion is mistaken for an accepted reviewed assertion or
  canonical override.
