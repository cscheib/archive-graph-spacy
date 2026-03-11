# Phase 0 Research: Phase and Temporal Outputs

## Decision: Use deterministic time-gap segmentation plus merge rules for the initial phase model

**Rationale**: Time-gap segmentation is the most explainable first
implementation for owner-centric temporal segments. It fits the repo's
deterministic pipeline style, creates auditable boundary reasons, and avoids
bringing clustering or narrative inference into the first contract-bearing
Phase 4 slice.

**Alternatives considered**:
- Fixed calendar buckets
  - rejected because they ignore archive-specific cadence changes and create
    artificial boundaries
- Theme-shift or relationship-shift segmentation first
  - rejected because it adds semantic coupling before a stable temporal object
    exists
- Hybrid scored segmentation over gaps, themes, and relationships
  - rejected because it is harder to explain, test, and operate safely in the
    first pass

## Decision: Publish one `phases` table plus child tables for each major aggregate family

**Rationale**: A first-class `phases` table keeps the temporal object explicit,
while child tables keep central people, themes, temporal pairs, representative
interactions, and diagnostics queryable without turning the phase row into an
overloaded nested structure.

**Alternatives considered**:
- One wide `phases` table only
  - rejected because it overloads one row with several unrelated aggregates
- No first-class `phases` table
  - rejected because downstream consumers would have to reconstruct the object
    model from membership rows
- One generic metrics table for all aggregates
  - rejected because it weakens type clarity and contract readability

## Decision: Reuse Phase 3 pair semantics and publish temporal pair summaries plus bounded evidence

**Rationale**: Phase-bounded pair summaries plus bounded evidence rows reuse
the proven Phase 3 relationship pattern. This gives the UI a stable
join-friendly contract and preserves explainability without forcing consumers
to recompute pair activity from raw messages.

**Alternatives considered**:
- Summary-only pair rows
  - rejected because downstream consumers still need evidence for explanation
- Membership-only outputs with downstream aggregation
  - rejected because it would recreate temporal pair semantics in consumers
- Debug blobs instead of evidence rows
  - rejected because they are less queryable and harder to validate

## Decision: Suppress weak phases from published outputs and record them only in diagnostics

**Rationale**: Weak phases should not appear in the main contract as if they
were equally trustworthy. Suppression keeps the initial UI contract cleaner and
lets diagnostics explain what was omitted, merged, or retained without
polluting phase list/detail flows.

**Alternatives considered**:
- Emit weak phases with low confidence markers
  - rejected because it still pushes ambiguous objects into the main contract
- Merge all weak phases into neighboring stronger phases
  - rejected because some weak segments should be suppressed, not forced into a
    false neighboring phase
- Publish weak phases in a separate debug table only
  - rejected because the diagnostics table already covers the operator need

## Decision: Keep phase outputs owner-centric and defer curated labels or overrides

**Rationale**: ADR 005 already sets the first rollout as owner-centric inferred
segments first. Deferring curated labels and overrides keeps this slice focused
on deterministic upstream outputs and avoids mixing Phase 4 derivation with
later curation workflows.

**Alternatives considered**:
- Start with multi-person or per-person personalized phases
  - rejected because it expands scope beyond the initial Phase 4 contract
- Add curated labels in the first pass
  - rejected because the contract and UI need a stable inferred base first

## Decision: Keep diagnostics bounded and explanation-oriented

**Rationale**: Diagnostics need to explain phase boundaries, suppressions,
representative interactions, and top-ranked aggregates without becoming an
exhaustive event ledger. Run-level counts plus a small deterministic sample per
phase and boundary case are enough for validation and operations.

**Alternatives considered**:
- Exhaustive message-level boundary logs
  - rejected because they break bounded-output discipline
- Counts only with no representative evidence
  - rejected because operators still need explanation hooks
- Free-form logs only
  - rejected because tests and downstream consumers need stable categories
