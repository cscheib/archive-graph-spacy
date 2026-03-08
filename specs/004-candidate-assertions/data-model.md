# Data Model: Candidate Assertions

## Candidate Assertion

**Purpose**: Represent a reviewable proposed fact emitted from derived
enrichment before any human review begins.

**Fields**
- `candidate_assertion_id`: Stable run-scoped identifier for the candidate
- `run_id`: Pipeline run that emitted the candidate
- `assertion_type`: `relay_sender_identity` or `person_link_disambiguation`
- `subject_canonical_id`: Immutable canonical subject ID
- `proposed_claim`: Structured or human-readable proposed fact
- `evidence_refs`: References to source message or link evidence
- `provenance_summary`: Derived-flow summary explaining how the candidate was produced
- `confidence_level`: Confidence signal used for prioritization
- `generation_scope`: Bundle or run scope used to derive the candidate
- `generated_at`: Candidate creation timestamp
- `review_class`: `reviewable`
- `promotion_class`: `promotion_eligible` or `derived_only`

**Validation Rules**
- Must not exist without an assertion type, subject canonical ID, evidence,
  provenance, confidence, and generation scope
- Must remain non-canonical and pre-review
- Must have deterministic identity within a generation scope

## Relay Sender Identity Candidate

**Purpose**: Capture a review-worthy inferred mapping between a relay-address
sender and a canonical person.

**Fields**
- `candidate_assertion_id`
- `subject_canonical_id`
- `relay_address`: Relay sender address or sender token under review
- `proposed_person_id`: Canonical person proposed by the inference
- `evidence_refs`
- `provenance_summary`
- `confidence_level`

**Validation Rules**
- Must only be emitted when relay sender evidence satisfies review-worthiness
  minimums
- Must include an unresolved relay-like sender address plus at least one
  supporting link signal beyond the raw sender value
- Must preserve provenance that identifies the source message and derivation
  path
- Must map to `promotion_eligible` in v1

## Person Link Disambiguation Candidate

**Purpose**: Capture a review-worthy ambiguous mention-link case where multiple
plausible canonical people exist and no clear winner can be selected.

**Fields**
- `candidate_assertion_id`
- `subject_canonical_id`
- `mention_text`: Ambiguous mention under review
- `plausible_person_ids`: Candidate canonical people considered plausible
- `leading_person_ids`: Optional top-ranked people before suppression
- `evidence_refs`
- `provenance_summary`
- `confidence_level`

**Validation Rules**
- Must only be emitted when more than one plausible canonical person exists
- Must not be emitted when the derived evidence selects a clear winner
- Must map to `derived_only` in v1

## Candidate Diagnostics Summary

**Purpose**: Provide a human-readable summary of candidate-generation results
for local validation and downstream planning.

**Fields**
- `run_id`
- `generation_scope`
- `emitted_candidate_count`
- `candidate_counts_by_type`
- `suppressed_counts`
- `example_candidate_ids`
- `generated_at`

**Validation Rules**
- Must summarize the same candidate set written to the persisted output surface
- Must distinguish emitted candidates from suppressed cases
- In v1, is published as `candidate_assertions_summary.json`

## Relationships

- One pipeline `run_id` may emit zero or more `Candidate Assertion` records.
- One `Candidate Diagnostics Summary` describes one run-scoped candidate set.
- One `Candidate Assertion` belongs to exactly one first-wave subtype:
  `Relay Sender Identity Candidate` or `Person Link Disambiguation Candidate`.
- Each `Candidate Assertion` must remain compatible with the reviewed-assertions
  lifecycle contract defined in `specs/003-reviewed-assertions-pipeline/`.

## Identity And Rerun Rules

- Candidate identity in v1 is stable per
  `(assertion_type, subject_canonical_id, proposed_claim, generation_scope)`.
- Reruns of the same generation scope regenerate the same logical candidate
  records deterministically.
- Broader cross-run historical deduplication is explicitly out of scope for
  this feature.

## Output Artifacts

- Persisted candidate output artifact: `candidate_assertions.jsonl`
- Diagnostics summary artifact: `candidate_assertions_summary.json`
