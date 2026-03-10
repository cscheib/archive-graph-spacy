# Data Model: Phase and Temporal Outputs

## Phase

**Purpose**: Represent one inferred owner-centric temporal segment published as
part of the Phase 4 contract.

**Fields**
- `phase_id`
- `run_id`
- `generation_scope`
- `phase_index`
- `start_at`
- `end_at`
- `interaction_count`
- `representative_interaction_ref`
- `boundary_reason`
- `is_current`

**Validation Rules**
- `phase_id` must be stable for unchanged bounded inputs
- One current row exists per `phase_id` within a run scope
- `phase_index` must be deterministic and sortable

## Phase Boundary Decision

**Purpose**: Represent the deterministic reasoning used to retain, merge, or
suppress a temporal segment boundary.

**Fields**
- `run_id`
- `candidate_boundary_id`
- `phase_id_before`
- `phase_id_after`
- `decision`
- `gap_days`
- `merge_rule`
- `reason_code`

**Allowed Decisions**
- `retained`
- `merged`
- `suppressed`

**Validation Rules**
- Decision must come from time-gap segmentation plus merge rules
- `suppressed` boundaries must not create published weak phases

## Phase Central Person

**Purpose**: Publish one ranked person aggregate that helps explain who
defines a phase.

**Fields**
- `phase_id`
- `person_id`
- `rank`
- `centrality_score`
- `interaction_count`
- `evidence_ref`

**Validation Rules**
- Ranking must be deterministic for unchanged bounded input
- Every row must join to a published `phase_id`

## Phase Theme Summary

**Purpose**: Publish one ranked theme aggregate that helps explain what defines
a phase.

**Fields**
- `phase_id`
- `theme_key`
- `rank`
- `theme_score`
- `message_count`
- `evidence_ref`

**Validation Rules**
- Ranking must be deterministic for unchanged bounded input
- Theme rows may be omitted when theme signal is weak, but the omission must be
  diagnosable

## Phase Pair Summary

**Purpose**: Publish one phase-bounded aggregate for a canonical person pair.

**Fields**
- `phase_pair_id`
- `phase_id`
- `pair_id`
- `pair_rank`
- `activity_score`
- `relationship_signal`
- `evidence_count`
- `strongest_evidence_ref`

**Validation Rules**
- `pair_id` must reuse the canonical Phase 3 pair identity
- One current summary row exists per `phase_id` + `pair_id`
- Summary rows must be queryable without downstream recomputation

## Phase Pair Evidence

**Purpose**: Publish the bounded supporting evidence for one pair within one
phase.

**Fields**
- `phase_pair_evidence_id`
- `phase_id`
- `pair_id`
- `source_ref`
- `message_ref`
- `evidence_family`
- `rank_within_phase_pair`
- `contribution_score`

**Validation Rules**
- Evidence rows must remain bounded and representative
- Selection must be deterministic for reruns of the same bounded scope
- Every evidence row must join back to a published phase pair summary

## Phase Representative Interaction

**Purpose**: Publish a bounded interaction reference that represents one phase
for list/detail exploration and diagnostics.

**Fields**
- `phase_id`
- `interaction_ref`
- `rank`
- `selection_reason`

**Validation Rules**
- At least one representative interaction should exist for every published
  phase when qualifying evidence exists
- Ordering must be deterministic

## Phase Diagnostics Record

**Purpose**: Publish bounded provenance-bearing diagnostics for phase
retention, merge, suppression, and aggregate explanation.

**Fields**
- `run_id`
- `phase_id`
- `diagnostic_type`
- `result`
- `reason_code`
- `sample_ref`
- `details`

**Allowed Diagnostic Types**
- `boundary`
- `suppression`
- `central_people`
- `themes`
- `temporal_pairs`

**Validation Rules**
- Diagnostics must remain bounded and operator-readable
- Suppressed phases must appear here even when absent from `phases`

## Relationships

- One `Phase` may have many `Phase Central Person` rows.
- One `Phase` may have many `Phase Theme Summary` rows.
- One `Phase` may have many `Phase Pair Summary` rows.
- One `Phase Pair Summary` may have many `Phase Pair Evidence` rows.
- One `Phase` may have many `Phase Representative Interaction` rows.
- One `Phase` may have many `Phase Diagnostics Record` rows.
- One `Phase Boundary Decision` may explain the transition between two adjacent
  published phases or the suppression of a weak segment.
