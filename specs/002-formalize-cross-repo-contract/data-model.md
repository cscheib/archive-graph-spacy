# Data Model: Cross-Repo Contract

## Overview

The cross-repo contract defines how canonical records, derived enrichment,
candidate assertions, reviewed assertions, and promoted overrides relate across
`archive-graph-data` and `archive-graph-spacy`. The model is semantic rather
than implementation-specific: it describes ownership, identifiers, provenance,
and state transitions that downstream work must honor.

## Entities

### Canonical Record

- **Purpose**: Represents a source-of-truth person, interaction, override, or
  other durable fact that downstream workflows may read.
- **Primary fields**:
  - `canonical_id`
  - `record_type`
  - `source_repository`
  - `effective_state`
  - `last_reviewed_at`
- **Validation rules**:
  - `canonical_id` is immutable.
  - `source_repository` is `archive-graph-data`.
  - Canonical records may be referenced by derived or reviewed records but are
    not re-owned by them.

### Canonical Identifier

- **Purpose**: Provides the authoritative join key used across repositories.
- **Primary fields**:
  - `canonical_id`
  - `entity_type`
  - `issued_by`
  - `status`
- **Validation rules**:
  - The identifier is stable for the life of the canonical record.
  - Natural identifiers such as names, emails, aliases, and handles are not
    authoritative cross-repo join keys.

### Derived Enrichment

- **Purpose**: Captures replaceable NLP or analysis outputs generated from
  canonical inputs for search, explanation, ranking, or review support.
- **Primary fields**:
  - `derived_id`
  - `canonical_id_refs`
  - `derivation_type`
  - `provenance`
  - `confidence`
  - `run_id`
- **Validation rules**:
  - `derived_id` is unique within its derivation surface.
  - Every row includes provenance back to source evidence and the generating
    run or process.
  - `source_repository` is `archive-graph-spacy`.

### Candidate Assertion

- **Purpose**: Represents a proposed fact or identity outcome produced from
  derived evidence before human review begins.
- **Primary fields**:
  - `candidate_assertion_id`
  - `assertion_type`
  - `subject_canonical_id`
  - `object_canonical_id` or `proposed_value`
  - `supporting_evidence_refs`
  - `confidence`
  - `generation_context`
  - `handoff_status`
- **Validation rules**:
  - Candidate assertions originate in `archive-graph-spacy`.
  - Every candidate assertion references supporting evidence.
  - Candidate assertions are not canonical facts and cannot directly change
    canonical state.
- **State transitions**:
  - `generated` -> `handed_off`
  - `generated` -> `withdrawn`

### Reviewed Assertion

- **Purpose**: Represents a candidate assertion once it has entered human
  review and curation.
- **Primary fields**:
  - `reviewed_assertion_id`
  - `candidate_assertion_id`
  - `review_state`
  - `reviewer_identity`
  - `decision_reason`
  - `supporting_evidence_refs`
  - `promotion_eligibility`
  - `promotion_status`
- **Validation rules**:
  - Reviewed assertions live in `archive-graph-data`.
  - Every reviewed assertion preserves the evidence chain from the originating
    candidate assertion.
  - `review_state` is one of `queued`, `accepted`, `rejected`, `superseded`, or
    `promoted`.
- **State transitions**:
  - `queued` -> `accepted`
  - `queued` -> `rejected`
  - `accepted` -> `promoted`
  - `accepted` -> `superseded`
  - `rejected` -> `superseded`

### Promotion Rule

- **Purpose**: Defines whether and how a reviewed assertion may become a
  durable upstream fact.
- **Primary fields**:
  - `assertion_type`
  - `eligibility_class`
  - `required_review_state`
  - `required_provenance_minimum`
  - `promotion_target`
- **Validation rules**:
  - Every assertion type is classified as `derived_only`, `reviewable`, or
    `promotion_eligible`.
  - Promotion requires both the required review state and the minimum evidence
    conditions defined by the contract.

### Interface Map

- **Purpose**: Documents the owned surfaces and allowed transitions between the
  two repositories.
- **Primary fields**:
  - `surface_name`
  - `owning_repository`
  - `consuming_repository`
  - `authoritative_join_key`
  - `allowed_transitions`
  - `notes`
- **Validation rules**:
  - Each surface has one owning repository.
  - Cross-repo transitions must identify the sending surface, receiving
    surface, and authoritative join key.

## Relationships

- A `Canonical Record` is identified by one `Canonical Identifier`.
- Many `Derived Enrichment` rows may reference the same `Canonical Record`.
- Many `Candidate Assertion` rows may be generated from one or more `Derived
  Enrichment` rows.
- A `Candidate Assertion` may become one `Reviewed Assertion` after handoff into
  the curation system.
- A `Reviewed Assertion` is governed by one `Promotion Rule`.
- The `Interface Map` describes which repository owns each entity lifecycle
  stage and how records move between them.

## Identity And Uniqueness

- `canonical_id` is the only authoritative cross-repo join key for canonical
  entities and promoted facts.
- `candidate_assertion_id` uniquely identifies a pre-review proposal.
- `reviewed_assertion_id` uniquely identifies one reviewed lifecycle record in
  the curation system.
- Natural identifiers may aid lookup and evidence display, but they do not
  replace canonical IDs for cross-repo joins.

## Lifecycle Notes

- Derived enrichment remains replaceable and non-canonical.
- Candidate assertions remain pre-review proposals until handed off to
  `archive-graph-data`.
- Human review begins in `archive-graph-data`, where review history and
  promotion decisions remain durable and auditable.
- Promotion changes canonical state only when a reviewed assertion satisfies
  its promotion rule; otherwise the reviewed assertion remains part of review
  history without becoming a canonical override.
