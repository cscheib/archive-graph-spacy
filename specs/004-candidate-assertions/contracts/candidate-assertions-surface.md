# Contract: Candidate Assertions Surface

## Purpose

Define the candidate-side output contract produced by `archive-graph-spacy`
for `archive-graph-spacy#2`. This contract extends the reviewed-assertions
model without redefining downstream reviewed storage or promotion ownership.

## Related Issues

- Intended to close `archive-graph-spacy#2`
- Extends `archive-graph-spacy#4`
- Unblocks downstream candidate review consumption in `archive-graph-data#71`

## In-Scope Assertion Types

- `relay_sender_identity`
- `person_link_disambiguation`

No other candidate assertion types are in scope for v1.

## Persisted Candidate Output

The persisted candidate output surface must expose one record per emitted
candidate assertion in `candidate_assertions.jsonl` with these required fields:

| Field | Purpose |
|-------|---------|
| `candidate_assertion_id` | Stable run-scoped candidate handle |
| `run_id` | Links the candidate to the derivation run |
| `assertion_type` | Distinguishes relay sender identity from disambiguation |
| `subject_canonical_id` | Immutable canonical join key |
| `proposed_claim` | Reviewable proposed fact |
| `evidence_refs` | Source evidence pointers for downstream review |
| `provenance_summary` | Summary of how the candidate was derived |
| `confidence_level` | Review prioritization signal |
| `generation_scope` | Bundle/run scope for deterministic rerun behavior |
| `generated_at` | Candidate creation timestamp |
| `review_class` | Current pre-review classification (`reviewable`) |
| `promotion_class` | `promotion_eligible` or `derived_only` |

## Diagnostics Summary

The human-readable diagnostics summary must make these details visible for the
same run-scoped candidate set in `candidate_assertions_summary.json`:

| Field | Purpose |
|-------|---------|
| `run_id` | Identifies the summarized run |
| `generation_scope` | Identifies the summarized bundle scope |
| `emitted_candidate_count` | Total emitted candidates |
| `candidate_counts_by_type` | Per-assertion-type counts |
| `suppressed_counts` | Counts for non-emitted candidate cases by reason |
| `example_candidate_ids` | Small sample for manual inspection |

## Assertion-Type Rules

| Assertion Type | Emission Rule | Promotion Class |
|----------------|---------------|-----------------|
| `relay_sender_identity` | Emit only when a subject canonical ID exists, an unresolved relay-like sender address is present, at least one supporting link signal beyond the raw sender value exists, and provenance identifies the source message plus derivation path | `promotion_eligible` |
| `person_link_disambiguation` | Emit only when multiple plausible canonical people exist and no clear winner can be selected | `derived_only` |

## Identity And Rerun Guarantees

- Candidate assertions are deterministic within a generation scope.
- Within a run, there is one logical candidate per
  `(assertion_type, subject_canonical_id, proposed_claim, generation_scope)`.
- Reruns of the same generation scope must regenerate the same logical
  candidate set rather than appending duplicate competing records.

## Ownership And Boundaries

- `archive-graph-spacy` owns candidate generation and the candidate-side output
  surface.
- The persisted output remains pre-review and non-canonical.
- `archive-graph-data` owns any later review decision, accepted reviewed
  storage, and promotion steps.

## Guardrails

- Candidate outputs must never be labeled or presented as accepted reviewed
  assertions or canonical overrides.
- Candidate outputs must preserve enough evidence and provenance for later
  human review.
- V1 must not emit disambiguation candidates for generic low-confidence cases
  unless they meet the explicit multi-candidate/no-clear-winner rule.
