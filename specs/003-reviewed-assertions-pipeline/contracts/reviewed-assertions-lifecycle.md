# Contract: Reviewed Assertions Lifecycle

## Purpose

Define the authoritative reviewed-assertions lifecycle needed to close
`archive-graph-spacy#4` and provide the workflow contract that downstream review
and promotion features can reference.

This contract extends the ownership guarantees from
`specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md`. It
does not define implementation-specific tables or APIs.

## Related Issues

- Intended to close `archive-graph-spacy#4`
- Required before `archive-graph-spacy#2`
- Referenced by downstream workflow issues `archive-graph-data#70` and
  `archive-graph-data#71`

## In-Scope Assertion Types

- `relay_sender_identity`
- `person_link_disambiguation`

No other assertion types are in scope for this initial lifecycle contract.

## Assertion Type Classification

| Assertion Type | Reviewable | Promotion Eligible | Initial Rule |
|----------------|------------|--------------------|--------------|
| `relay_sender_identity` | Yes | Yes | May be promoted only after accepted review, sufficient provenance, and explicit human promotion action |
| `person_link_disambiguation` | Yes | No | May be reviewed and accepted into durable reviewed storage, but remains derived-only in v1 |

## Lifecycle States

### Candidate Assertion

- Produced by `archive-graph-spacy`
- Pre-review only
- Includes assertion type, subject reference, evidence, provenance, and
  confidence
- Cannot mutate canonical truth

### Review Decision

- Captured during human review in `archive-graph-data`
- Records reviewer action, rationale, timestamp, and evidence lineage
- May end in `queued`, `accepted`, `rejected`, or `superseded`

### Accepted Reviewed Assertion

- Durable reviewed record created only after an acceptance decision
- Still distinct from canonical truth
- May be either `derived_only` or `promotion_eligible`
- Must preserve the originating candidate and review lineage

### Promotion Outcome

- Separate explicit step after acceptance
- Triggered only by explicit human action
- Produces `promoted`, `not_promoted`, `promotion_rejected`, or `superseded`
  outcomes
- Only `promotion_eligible` assertion types may become canonical overrides

## Ownership Rules

- `archive-graph-spacy` owns candidate assertion generation and candidate-side
  evidence packaging.
- `archive-graph-data` owns review decisions, accepted reviewed assertions, and
  canonical override promotion.
- Canonical override writes remain outside `archive-graph-spacy`.

## Promotion Rules

- Acceptance never implies automatic promotion.
- Promotion always requires:
  - a durable accepted reviewed assertion
  - an assertion type marked `promotion_eligible`
  - provenance that satisfies the promotion rule
  - explicit human promotion action
- Assertion types marked `derived_only` may be reviewed and accepted but must
  never write canonical overrides.

## Required Integration Points

### Candidate Review Display

Downstream review surfaces must be able to consume these required fields:

| Field | Purpose |
|-------|---------|
| `candidate_assertion_id` | Stable handle for review and later decisions |
| `assertion_type` | Determines lifecycle and promotion class |
| `subject_canonical_id` | Immutable canonical join key for the reviewed subject |
| `proposed_claim` | Candidate fact presented for review |
| `evidence_refs` | Source evidence pointers shown to reviewers |
| `provenance_summary` | Summary of where the candidate came from |
| `confidence_level` | Confidence signal used to prioritize review |

### Review Decision Capture

Downstream review surfaces must be able to persist these required fields:

| Field | Purpose |
|-------|---------|
| `candidate_assertion_id` | Links the decision to the reviewed candidate |
| `decision_state` | `queued`, `accepted`, `rejected`, or `superseded` |
| `reviewer_actor` | Human reviewer identity |
| `decision_reason` | Rationale for the decision |
| `decision_timestamp` | When the decision happened |
| `evidence_snapshot` | Evidence lineage preserved at review time |
| `promotion_intent` | Whether the reviewer marked the accepted record for promotion consideration |

### Promotion Handoff

Downstream override workflows must be able to determine and persist these
required fields:

| Field | Purpose |
|-------|---------|
| `accepted_assertion_id` | Stable reviewed record eligible for promotion |
| `assertion_type` | Determines whether promotion is allowed |
| `promotion_eligibility` | `promotion_eligible` or `derived_only` |
| `accepted_provenance` | Reviewed provenance package evaluated for promotion |
| `review_decision_id` | Accepted review decision that produced the reviewed record |
| `override_target` | Upstream override surface targeted by the action |
| `acted_by` | Human actor who attempted or completed promotion |

## Examples

### Example A: Relay Sender Identity

- Candidate assertion proposes that a relay-address sender maps to a canonical
  person ID.
- Human review may reject it, accept it as reviewed enrichment, or accept it
  and explicitly promote it if the assertion type is marked
  `promotion_eligible`.

### Example B: Person-Link Disambiguation

- Candidate assertion proposes which canonical person a mention likely refers
  to.
- Human review may accept it for durable reviewed history while still leaving it
  `derived_only` if the workflow should not rewrite canonical truth for that
  assertion type.

## Guardrails

- Candidate assertions must never be presented as canonical facts.
- Accepted reviewed assertions must remain distinguishable from promoted
  canonical overrides.
- No background rule may promote assertions automatically in this initial
  workflow.
- Future assertion types must update this contract before being treated as
  reviewable or promotion-eligible.
