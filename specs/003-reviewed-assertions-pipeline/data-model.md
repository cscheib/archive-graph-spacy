# Data Model: Reviewed Assertions Pipeline

## Candidate Assertion

**Purpose**: Represent a proposed fact emitted by derived enrichment before any
human review.

**Fields**
- `candidate_assertion_id`: Durable identifier for the candidate record
- `assertion_type`: First-wave type such as `relay_sender_identity` or
  `person_link_disambiguation`
- `subject_canonical_id`: Immutable canonical ID for the entity or interaction
  the assertion concerns
- `proposed_claim`: Human-readable or structured statement of the proposed fact
- `evidence_refs`: References to source evidence supporting the candidate
- `provenance_summary`: Summary of where the candidate came from in the derived
  workflow
- `confidence_level`: Confidence signal attached to the candidate
- `generated_at`: Time the candidate was created
- `generation_scope`: Source bundle or enrichment scope that produced it

**Validation Rules**
- Must include immutable canonical subject reference
- Must include assertion type, evidence, provenance, and confidence
- Must not imply canonical truth

## Review Decision

**Purpose**: Record how a candidate assertion was evaluated during human review.

**Fields**
- `review_decision_id`: Durable identifier for the decision record
- `candidate_assertion_id`: Referenced candidate assertion
- `decision_state`: Review outcome such as `queued`, `accepted`, `rejected`,
  or `superseded`
- `reviewer_actor`: Human reviewer or review surface identity
- `decision_reason`: Required rationale or classification note
- `decision_timestamp`: Time the review decision was made
- `evidence_snapshot`: Evidence references preserved at review time
- `promotion_intent`: Whether the reviewer marked the accepted assertion as
  intended for promotion consideration

**Validation Rules**
- Must preserve a stable link to the originating candidate assertion
- Must preserve evidence lineage and reviewer intent
- Must not directly write canonical override state

## Accepted Assertion

**Purpose**: Represent a durable reviewed assertion that survived review and is
stored independently of canonical override state.

**Fields**
- `accepted_assertion_id`: Durable identifier for the accepted reviewed record
- `candidate_assertion_id`: Originating candidate assertion
- `accepted_claim`: Reviewed version of the proposed claim
- `accepted_at`: Acceptance timestamp
- `accepted_by`: Reviewer actor
- `promotion_eligibility`: `promotion_eligible` or `derived_only`
- `accepted_provenance`: Preserved provenance package for the reviewed result
- `review_decision_id`: Acceptance decision that produced the record

**Validation Rules**
- Must exist before promotion can occur
- May remain durable even if never promoted
- Must preserve provenance from candidate through review

## Promotion Rule

**Purpose**: Define whether an accepted assertion type may become an upstream
canonical override and under what conditions.

**Fields**
- `assertion_type`: Assertion type governed by the rule
- `eligibility_class`: `promotion_eligible` or `derived_only`
- `required_provenance`: Minimum provenance needed before promotion
- `required_review_state`: Required accepted state before promotion
- `human_action_required`: Explicit flag that promotion requires human action
- `rule_notes`: Explanatory notes and examples

**Validation Rules**
- Must be explicit by assertion type
- Must distinguish accepted reviewed storage from promoted canonical override
- Must require explicit human promotion in v1

## Assertion Type Classification

| Assertion Type | Review Class | Promotion Class | Notes |
|----------------|--------------|-----------------|-------|
| `relay_sender_identity` | `reviewable` | `promotion_eligible` | May become a canonical override only after accepted review, required provenance, and explicit human promotion |
| `person_link_disambiguation` | `reviewable` | `derived_only` | May be accepted into durable reviewed history but must not write canonical override state in v1 |

## Promotion Outcome

**Purpose**: Record the result of attempting or completing promotion from an
accepted reviewed assertion into canonical override storage.

**Fields**
- `promotion_outcome_id`: Durable identifier for the promotion event
- `accepted_assertion_id`: Source accepted reviewed assertion
- `outcome_state`: `promoted`, `not_promoted`, `superseded`, or
  `promotion_rejected`
- `outcome_timestamp`: Time the outcome was recorded
- `acted_by`: Human actor who performed or rejected promotion
- `override_target`: Upstream override surface targeted by the action
- `outcome_notes`: Explanation for the result

**Validation Rules**
- Must not exist without an accepted reviewed assertion
- Must preserve the human actor who initiated promotion or rejected it
- Must keep a durable link between reviewed history and canonical override write

## Relationships

- One `Candidate Assertion` may have many `Review Decision` records over time.
- One `Candidate Assertion` may produce zero or one current `Accepted
  Assertion`.
- One `Accepted Assertion` may produce zero or more `Promotion Outcome`
  records.
- `Promotion Rule` applies by `assertion_type` and constrains both `Accepted
  Assertion` and `Promotion Outcome`.

## Integration Field Sets

### Candidate Handoff Fields

- `candidate_assertion_id`
- `assertion_type`
- `subject_canonical_id`
- `proposed_claim`
- `evidence_refs`
- `provenance_summary`
- `confidence_level`

### Review Decision Capture Fields

- `candidate_assertion_id`
- `decision_state`
- `reviewer_actor`
- `decision_reason`
- `decision_timestamp`
- `evidence_snapshot`
- `promotion_intent`

### Promotion Handoff Fields

- `accepted_assertion_id`
- `assertion_type`
- `promotion_eligibility`
- `accepted_provenance`
- `review_decision_id`
- `override_target`
- `acted_by`

## Lifecycle Summary

1. A derived workflow emits a `Candidate Assertion`.
2. Human review creates one or more `Review Decision` records.
3. An accepted review creates a durable `Accepted Assertion`.
4. A separate explicit human promotion action may create a `Promotion Outcome`
   and write an upstream canonical override if the assertion type is eligible.
