# Feature Specification: Reviewed Assertions Pipeline

**Feature Branch**: `003-reviewed-assertions-pipeline`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Create the data and workflow model for candidate assertions, review decisions, accepted assertions, and upstream promotion into canonical overrides. Define candidate assertion types, review decision states, provenance requirements, accepted assertion storage, promotion rules, and integration points with archive-graph-data UI and override tables so the feedback loop is explicit, reviewable, and clear about which assertion types are eligible for upstream promotion."

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-08

- Q: Which assertion types are in scope for the initial reviewed-assertions model? → A: Relay sender identity and ambiguous person-link/disambiguation assertions only.
- Q: Does accepting an assertion immediately promote it upstream? → A: No. Accepted reviewed assertions become durable reviewed records first, and promotion is a separate explicit step.
- Q: What triggers promotion to a canonical override? → A: Only an explicit human review action on an accepted reviewed assertion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Reviewable Assertion Records (Priority: P1)

A maintainer needs one explicit model for candidate assertions, review decisions,
accepted assertions, and promotion eligibility so enrichment outputs can be
reviewed without being mistaken for canonical truth.

**Why this priority**: The rest of the review workflow depends on a shared data
model and lifecycle. Without that model, downstream curation and UI work cannot
reliably distinguish tentative enrichment from durable accepted facts.

**Independent Test**: Can be fully tested by reviewing the specification and
examples to classify candidate, reviewed, accepted, and promoted records for a
set of representative assertions without inventing extra rules.

**Acceptance Scenarios**:

1. **Given** a maintainer reviewing the model, **When** they inspect the
   defined assertion record types, **Then** they can distinguish candidate
   assertions, review decisions, accepted assertions, and promoted canonical
   overrides as separate states with separate responsibilities.
2. **Given** a candidate assertion produced by enrichment, **When** the
   maintainer checks the model, **Then** it is clear that the candidate does not
   become canonical truth unless it passes through the reviewed and
   promotion-eligible path defined by the workflow.

---

### User Story 2 - Define Review Decisions And Promotion Rules (Priority: P2)

A maintainer needs clear review decision states, provenance minimums, and
promotion rules so only eligible accepted assertions can become upstream
canonical overrides.

**Why this priority**: The review loop fails if accepted assertions and promoted
facts are treated as the same thing. Promotion rules must be explicit before the
system can safely hand reviewed facts back upstream.

**Independent Test**: Can be fully tested by taking representative assertion
examples and determining which are rejectable, accepted-but-derived-only, or
eligible for upstream promotion using the specification alone.

**Acceptance Scenarios**:

1. **Given** a reviewed assertion with attached evidence and provenance,
   **When** a maintainer evaluates it against the promotion rules, **Then** they
   can determine whether it stays as reviewed enrichment or is eligible for
   upstream canonical override.
2. **Given** an assertion type that should never rewrite canonical truth,
   **When** a maintainer checks the workflow, **Then** the specification states
   that it can be reviewed and accepted without becoming promotion-eligible.

---

### User Story 3 - Define Downstream Integration Boundaries (Priority: P3)

A maintainer needs clear integration points for the `archive-graph-data` UI and
override tables so downstream review surfaces know which records to show, which
decisions to persist, and which accepted assertions can be promoted upstream.

**Why this priority**: Once the review model exists, downstream systems need a
bounded contract for presenting assertions, capturing decisions, and writing
canonical overrides without coupling directly to enrichment internals.

**Independent Test**: Can be fully tested by mapping at least five review and
promotion interactions to the documented integration points and confirming which
repo or system owns each step.

**Acceptance Scenarios**:

1. **Given** a downstream UI team, **When** they inspect the specification,
   **Then** they can identify which assertion records must be displayed for
   review, which decision outputs must be captured, and which promotion results
   must be written upstream.
2. **Given** an accepted reviewed assertion, **When** a maintainer traces the
   documented handoff, **Then** it is clear whether the assertion remains local
   reviewed data or becomes an upstream canonical override.

### Edge Cases

- What happens when multiple candidate assertions for the same subject and claim
  disagree with each other but all remain individually review-worthy?
- How does the workflow handle a reviewed assertion whose evidence is
  sufficient for review display but insufficient for upstream promotion?
- What happens when a review decision is later reversed after an accepted
  assertion has already been stored?
- How does the model handle assertion types that are useful for downstream
  diagnostics but explicitly not eligible for promotion?
- What happens when a downstream UI attempts to promote an assertion type that
  the model marks as reviewable but not promotable?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define separate record concepts for candidate
  assertions, review decisions, accepted assertions, and promoted canonical
  overrides.
- **FR-002**: The system MUST define the minimum required fields for candidate
  assertions, including assertion type, subject reference, proposed claim,
  evidence, provenance, and confidence.
- **FR-003**: The system MUST define the initial candidate assertion types in
  scope for this workflow as relay sender identity assertions and ambiguous
  person-link/disambiguation assertions only.
- **FR-004**: The system MUST define the review decision states that can be
  applied to a candidate assertion as `queued`, `accepted`, `rejected`, and
  `superseded`.
- **FR-005**: The system MUST define what information a review decision must
  preserve, including reviewer intent, decision timestamp, and supporting
  rationale or evidence references.
- **FR-006**: The system MUST define when an assertion becomes an accepted
  reviewed assertion rather than a transient candidate.
- **FR-007**: The system MUST define which accepted assertion types are eligible
  for upstream canonical promotion and which are permanently derived-only.
- **FR-008**: The system MUST define promotion eligibility rules that can be
  evaluated without conflating accepted reviewed assertions with canonical
  truth.
- **FR-008a**: The system MUST define acceptance as creating a durable accepted
  reviewed assertion record, not an immediate upstream canonical override.
- **FR-008b**: The system MUST define promotion as a separate explicit step
  applied only after an assertion has been accepted into reviewed storage.
- **FR-008c**: The system MUST define promotion to an upstream canonical
  override as requiring an explicit human review action on an accepted reviewed
  assertion.
- **FR-009**: The system MUST define provenance requirements for both
  accepted-but-derived assertions and promotion-eligible assertions.
- **FR-010**: The system MUST define how conflicting or superseded review
  decisions are represented so the workflow remains auditable.
- **FR-010a**: The system MUST define durable review decisions, accepted
  reviewed assertions, and promotion outcomes as records owned by
  `archive-graph-data` once human review begins.
- **FR-011**: The system MUST define the integration points required by the
  `archive-graph-data` UI to display candidate assertions, capture review
  decisions, and surface promotion outcomes.
- **FR-012**: The system MUST define the integration points required for writing
  promotion-eligible accepted assertions into upstream override tables.
- **FR-012a**: The system MUST define the exact required fields for candidate
  handoff, review decision capture, and promotion handoff so downstream systems
  can implement the workflow without inventing local payload rules.
- **FR-013**: The system MUST define examples that show the difference between
  reviewable assertions, accepted reviewed assertions, and promoted canonical
  overrides.
- **FR-014**: The system MUST explicitly prevent the reviewed-assertions
  workflow from silently rewriting canonical truth without a documented
  promotion step.

### Key Entities *(include if feature involves data)*

- **Candidate Assertion**: A proposed fact produced by enrichment that includes
  an assertion type, a subject reference, a proposed claim, attached evidence,
  provenance, and a confidence signal, but is not canonical truth.
- **Review Decision**: A durable decision record that captures how a candidate
  assertion was evaluated, including its decision state, rationale, reviewer
  context, and decision time.
- **Accepted Assertion**: A reviewed assertion that remains durable and
  queryable after review, whether or not it is promotion-eligible, and before
  any separate promotion decision is applied.
- **Promotion Rule**: A rule set that determines whether an accepted assertion
  may become an upstream canonical override after an explicit human promotion
  action.
- **Canonical Override**: An upstream durable fact written into canonical
  override storage after a reviewed assertion satisfies the promotion rules.
- **Promotion Outcome**: A record of whether an accepted assertion was promoted,
  rejected from promotion, superseded, or remains eligible but unpromoted.

## Assumptions

- The cross-repo ownership contract from `archive-graph-spacy#1` remains the
  governing boundary for canonical data, derived enrichment, reviewed
  assertions, and overrides.
- Once candidate assertions are handed off for human review, durable reviewed
  storage and promotion state remain owned by `archive-graph-data`.
- This feature defines the reviewed-assertions model and workflow contract; it
  does not require building the full downstream UI in this repository.
- Promotion to upstream canonical override is always initiated by explicit human
  review action rather than automatic background rules in the initial workflow.
- Candidate assertion generation logic for specific assertion types may be
  implemented separately, but this spec must identify the initial assertion
  types the workflow is designed to support as relay sender identity assertions
  and ambiguous person-link/disambiguation assertions only.
- Upstream promotion targets remain canonical override tables managed outside
  this repository, but this feature must define the required handoff contract.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `README.md`, `docs/ROADMAP.md`,
  `docs/adr/003-reviewed-assertions-promotion-model.md`, and the new
  `specs/003-reviewed-assertions-pipeline/` planning artifacts
- **Behavior Change Summary**: Documentation must explain the reviewed
  assertions lifecycle, distinguish derived reviewed data from promoted
  canonical overrides, and identify the downstream UI and override-table
  integration boundaries.
- **Local Test Plan**: Validate the generated planning artifacts, run
  `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, and run `uv run pytest`
  for any implementation that introduces or updates model logic in this
  repository.

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/003-reviewed-assertions-promotion-model.md`
- **Architectural Scope**: Introduces the reviewed assertions feedback-loop
  model, including durable reviewed storage, decision states, and promotion
  boundaries between enrichment outputs and canonical overrides.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can classify at least five representative assertions
  as candidate-only, accepted-but-derived, or promotion-eligible using the
  specification alone with no contradictory interpretations.
- **SC-002**: Maintainers can apply the documented review decision states to at
  least five representative assertion examples and reach the same resulting
  lifecycle state.
- **SC-003**: Downstream teams can identify, from the specification alone, the
  required inputs and outputs for review display, decision capture, and
  promotion handoff for at least three integration interactions.
- **SC-004**: The documented workflow contains zero steps where a candidate or
  reviewed assertion becomes canonical truth without an explicit promotion
  decision.
