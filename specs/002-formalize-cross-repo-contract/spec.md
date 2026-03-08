# Feature Specification: Cross-Repo Contract

**Feature Branch**: `002-formalize-cross-repo-contract`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Use the content from GitHub issue #1: Formalize the
cross-repo canonical, derived, and assertion contract between
archive-graph-data and archive-graph-spacy."

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-08

- Q: Which repository should own reviewed assertions once a candidate is ready for human review? → A: `archive-graph-spacy` owns candidate assertions; `archive-graph-data` owns reviewed assertions and promoted overrides.
- Q: What should be the required cross-repo join key policy? → A: Cross-repo joins must use immutable canonical IDs only; names, emails, and aliases are supporting evidence only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shared Ownership Boundary (Priority: P1)

As a roadmap owner, I want one agreed contract that defines what each
repository owns so future feature work can proceed without conflicting data
models or duplicated responsibility.

**Why this priority**: The roadmap is blocked until both repositories can rely
on one shared definition of canonical records, derived enrichment, and reviewed
assertions.

**Independent Test**: Can be fully tested by reviewing the contract and
confirming that a maintainer can identify, for each major data class, which
repository owns it, whether it is read-only or editable, and how downstream
features should reference it.

**Acceptance Scenarios**:

1. **Given** a planner is defining a new feature that spans both repositories,
   **When** they read the contract, **Then** they can determine which
   repository owns canonical records, which repository owns derived enrichment,
   and where reviewed assertions belong.
2. **Given** two maintainers are discussing a proposed data change, **When**
   they compare it against the contract, **Then** they reach the same ownership
   decision without needing an additional architecture clarification.

---

### User Story 2 - Stable Interface And Join Semantics (Priority: P2)

As a feature implementer, I want the contract to define the stable identifiers,
provenance expectations, and confidence semantics shared across repositories so
I can build new features against consistent interfaces.

**Why this priority**: Even with clear ownership, downstream work will still
drift if identifiers, assertion types, and provenance rules remain implicit.

**Independent Test**: Can be fully tested by checking whether a maintainer can
map a canonical person, a derived enrichment row, and a reviewed assertion back
to their governing identifiers, confidence meaning, and source evidence without
inventing missing rules.

**Acceptance Scenarios**:

1. **Given** a maintainer needs to join derived outputs back to canonical
   records, **When** they consult the contract, **Then** the required join keys
   and boundary conditions are explicitly defined.
2. **Given** a maintainer is adding a new assertion-producing workflow,
   **When** they consult the contract, **Then** they can determine what
   provenance and confidence fields are required for that assertion to be
   reviewable.

---

### User Story 3 - Promotion And Reference Rules (Priority: P3)

As a curator or reviewer, I want the contract to state what remains derived and
what may be promoted upstream after review so the feedback loop stays auditable
and controlled.

**Why this priority**: The roadmap assumes reviewed assertions will influence
future canonical data, and that transition must be bounded before review tools
or candidate generators expand.

**Independent Test**: Can be fully tested by evaluating sample assertion types
and confirming that a maintainer can classify each one as derived-only,
reviewable, or eligible for upstream promotion based on the contract alone.

**Acceptance Scenarios**:

1. **Given** a reviewed assertion has been accepted, **When** a maintainer
   checks the contract, **Then** they can tell whether that assertion is
   eligible for upstream promotion or must remain derived-only.
2. **Given** a future UI workflow references reviewed assertions, **When** the
   implementer consults the contract, **Then** they can identify the required
   review states, provenance expectations, and promotion boundaries.

### Edge Cases

- What happens when a data element appears to belong in both repositories unless
  the contract distinguishes source-of-truth ownership from derived
  convenience?
- How is a feature handled when it needs canonical identifiers but also creates
  reviewer decisions that must remain auditable before any upstream promotion?
- What happens when an assertion has enough evidence to be reviewed but not
  enough confidence to become a canonical override?
- How does the contract handle future assertion classes that do not fit the
  initial promotion rules?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one shared contract that defines the data
  boundary between `archive-graph-data` and `archive-graph-spacy`.
- **FR-002**: The contract MUST explicitly distinguish canonical records,
  derived enrichment, candidate assertions, reviewed assertions, and promoted
  upstream facts.
- **FR-003**: The contract MUST define which repository is the source of truth
  for each major data class covered by the roadmap.
- **FR-003a**: The contract MUST define `archive-graph-spacy` as the owner of
  candidate assertions before review and `archive-graph-data` as the owner of
  reviewed assertions and promoted upstream overrides after review begins.
- **FR-004**: The contract MUST define the stable identifiers or join keys
  required to connect canonical records, derived outputs, and reviewed
  assertions.
- **FR-004a**: The contract MUST require immutable canonical identifiers as the
  primary cross-repository join keys for people, interactions, and promoted
  facts.
- **FR-004b**: The contract MUST treat names, emails, aliases, handles, and
  other natural identifiers as evidence or lookup aids rather than authoritative
  cross-repository join keys.
- **FR-005**: The contract MUST define provenance expectations for derived and
  reviewed data, including the minimum evidence needed to trace a record back to
  its source inputs and review activity.
- **FR-006**: The contract MUST define confidence semantics for derived and
  reviewed data so confidence values are interpreted consistently across both
  repositories.
- **FR-007**: The contract MUST define which assertion types are always
  derived-only, which are reviewable, and which may be promoted upstream after
  review.
- **FR-008**: The contract MUST define the required review states for reviewed
  assertions, including how accepted, rejected, superseded, and promoted
  outcomes are represented.
- **FR-009**: The contract MUST define the boundary between reviewed assertion
  storage and canonical override storage so accepted-but-not-promoted decisions
  remain auditable.
- **FR-009a**: The contract MUST require candidate assertions to cross the
  repository boundary before human review so review history and canonical
  override decisions live in one durable curation system.
- **FR-010**: The contract MUST include an initial interface map covering the
  canonical, derived, and assertion surfaces needed by the currently blocked
  roadmap issues.
- **FR-011**: The shared contract MUST be published in one authoritative
  location so both repositories can reference the same boundary definition
  without restating the rules in separate conflicting documents.
- **FR-012**: The contract MUST identify any intentionally deferred questions
  that could affect future roadmap items, so later work can proceed with known
  boundaries rather than hidden assumptions.

### Key Entities *(include if feature involves data)*

- **Canonical Record**: A source-of-truth person, interaction, override, or
  other upstream fact that downstream features may read but do not redefine in
  derived workflows.
- **Canonical Identifier**: An immutable identifier assigned to a canonical
  record and used as the authoritative join key across repositories.
- **Derived Enrichment**: A non-canonical output created from canonical inputs
  for search, analysis, ranking, or evidence display, which remains replaceable
  and traceable to its sources.
- **Candidate Assertion**: A proposed fact or identity resolution outcome that
  is generated from evidence in `archive-graph-spacy` and is eligible for human
  review once handed off to the curation system.
- **Reviewed Assertion**: A candidate assertion with recorded review state,
  provenance, and reviewer decision history in `archive-graph-data`, whether or
  not it is later promoted upstream.
- **Promotion Rule**: The contract rule that determines whether a reviewed
  assertion may become a durable upstream fact or must remain in reviewed or
  derived form only.
- **Interface Map**: The documented mapping of key entities, identifiers,
  ownership, and allowed state transitions across the two repositories.

## Assumptions

- `archive-graph-data` remains the owner of canonical archive records and any
  durable upstream overrides that become part of the canonical source of truth.
- `archive-graph-spacy` remains the owner of derived NLP enrichment, candidate
  assertion generation, and experimentation around evidence-backed review flows.
- Reviewed assertions require their own auditable state boundary and are not the
  same thing as immediate canonical overrides.
- Human review, accepted decisions, and promoted overrides should live in the
  same durable curation boundary rather than being split across repositories.
- The first contract version only needs to cover the roadmap issues already
  identified as blocked by this work; it does not need to anticipate every
  future data surface.
- The contract should resolve ownership, interface, provenance, and promotion
  questions without prescribing implementation details for specific services or
  storage engines.
- Natural identifiers such as names, emails, and aliases may change over time,
  so they are insufficient as authoritative cross-repository join keys.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `docs/ROADMAP.md`, this feature spec at
  `specs/002-formalize-cross-repo-contract/spec.md`, references in both
  repositories that point roadmap work to the shared contract, and a new ADR for
  the cross-repo boundary decision.
- **Behavior Change Summary**: Document the ownership split between canonical
  data, derived enrichment, candidate assertions, reviewed assertions, and
  promoted upstream facts; document that candidate assertions originate in
  `archive-graph-spacy` while reviewed assertions and override decisions live in
  `archive-graph-data`; document that immutable canonical IDs are the required
  cross-repo join keys and that natural identifiers remain evidence only;
  document the stable join semantics, provenance expectations, and promotion
  rules that downstream roadmap items must follow.
- **Local Test Plan**: Validate the spec with the requirements checklist; when
  implementation begins, add or update automated tests for any schema, contract,
  or promotion-rule behavior that becomes executable in either repository before
  rollout.

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/002-cross-repo-contract.md`
- **Architectural Scope**: Establishes the cross-repository contract that
  governs ownership, join semantics, provenance, confidence meaning, review
  boundaries, and promotion paths for canonical, derived, and assertion data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of roadmap issues currently blocked by this feature can point
  to one shared contract without redefining ownership or join semantics in their
  own issue bodies.
- **SC-002**: In a review exercise using at least five representative data
  flows, maintainers reach the same ownership decision for each flow without
  requiring an additional architecture clarification.
- **SC-003**: In a review exercise using at least five representative assertion
  examples, maintainers correctly classify each example as derived-only,
  reviewable, or promotion-eligible using the contract alone.
- **SC-004**: The shared contract and ADR are published in this repository and
  ready to be referenced by dependent planning materials before blocked roadmap
  issues move into implementation.
- **SC-005**: No unresolved ambiguity remains around source-of-truth ownership,
  stable join identifiers, provenance minimums, or promotion eligibility for the
  initial roadmap scope.
