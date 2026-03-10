# Data Model: Feedback Consumption and Relationship Outputs

## Reviewed Input Record

**Purpose**: Represent one reviewed assertion or reviewed decision consumed
read-only from `graph-data` during `build_nlpdata`.

**Fields**
- `reviewed_assertion_id`
- `candidate_assertion_id`
- `assertion_type`
- `subject_ref`
- `claim_payload`
- `review_state`
- `decision_source`
- `source_catalog`
- `decision_recorded_at`
- `generation_scope`
- `evidence_window`

**Validation Rules**
- Must be read from `memory.reviewed_assertions` or
  `memory.review_assertion_decisions`
- Must remain read-only inside `archive-graph-spacy`
- Must carry enough normalized subject and claim data to support replay
  matching

## Replay Match Key

**Purpose**: Represent the stable semantic key used to apply reviewed outcomes
across reruns even when candidate IDs change.

**Fields**
- `assertion_type`
- `subject_key`
- `claim_key`
- `scope_key`
- `evidence_anchor`
- `tolerance_window`

**Validation Rules**
- Subject and claim semantics must match exactly
- Tolerance applies only to bounded evidence-window drift
- Broad fuzzy matching is not allowed

## Reviewed Effect Result

**Purpose**: Record the outcome of attempting to consume a reviewed input
record during one derivation run.

**Fields**
- `run_id`
- `reviewed_assertion_id`
- `assertion_type`
- `result`
- `matched_candidate_key`
- `reason_code`
- `details`

**Allowed Results**
- `applied`
- `suppressed`
- `skipped`
- `conflicted`
- `ignored`

**Validation Rules**
- `conflicted` means the system did not auto-apply the reviewed outcome
- `suppressed` means a rejected or resolved case prevented re-emission for the
  same semantic case
- `ignored` must represent an explicit out-of-scope or unsupported condition,
  not an unknown failure

## Person-Person Edge

**Purpose**: Publish one deterministic canonical summary row per unordered
person pair for bounded-scope relationship consumption.

**Fields**
- `pair_id`
- `person_a_id`
- `person_b_id`
- `run_id`
- `generation_scope`
- `strength_score`
- `relationship_signal`
- `direct_evidence_count`
- `indirect_evidence_count`
- `strongest_evidence_ref`
- `is_current`

**Validation Rules**
- `pair_id` must be canonical and order-independent
- Exactly one current summary row exists per pair per run scope
- Summary rows must remain queryable without requiring downstream
  recomputation of pair semantics

## Person-Person Edge Evidence

**Purpose**: Publish the bounded supporting evidence for a canonical person
pair.

**Fields**
- `pair_evidence_id`
- `pair_id`
- `evidence_family`
- `source_ref`
- `contribution_score`
- `rank_within_pair`
- `message_ref`
- `theme_refs`
- `provenance`

**Validation Rules**
- Evidence rows must remain bounded and representative rather than exhaustive
- Selection must be deterministic for reruns of the same bounded scope
- Every evidence row must join back to a published `pair_id`

## Candidate Assertion Family

**Purpose**: Represent one supported reviewable candidate assertion family in
the shared reviewed lifecycle.

**Fields**
- `assertion_type`
- `promotion_mode`
- `subject_model`
- `claim_model`
- `replay_model`
- `diagnostics_group`

**Validation Rules**
- Every family must be either `promotion_eligible` or `derived_only`
- Every family must use the shared candidate schema and reviewed lifecycle
- Every family must define replay and diagnostics behavior explicitly

## Relationship Evidence Review Candidate

**Purpose**: Represent a derived-only candidate assertion for a pairwise
relationship claim that is uncertain, conflicting, or operationally important
enough to review.

**Fields**
- `candidate_assertion_id`
- `assertion_type` = `relationship_evidence_review`
- `pair_id`
- `claim_payload`
- `evidence_refs`
- `confidence`
- `generation_scope`
- `replay_key`

**Validation Rules**
- Must be `derived_only`, not promotion-eligible
- Must use pair-scoped replay matching
- Must reference bounded relationship evidence rows rather than full raw
  message history

## Relationships

- One `Reviewed Input Record` may produce one `Reviewed Effect Result` in a run.
- One `Replay Match Key` belongs to one supported `Candidate Assertion Family`.
- One `Person-Person Edge` may have many `Person-Person Edge Evidence` rows.
- One `Relationship Evidence Review Candidate` must reference one canonical
  `Person-Person Edge` and one or more bounded evidence rows.
- One derivation run aggregates reviewed-effect diagnostics across many
  candidate families and pair outputs.
