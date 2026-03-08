# Feature Specification: nlpdata Publish Hardening

**Feature Branch**: `005-nlpdata-publish-hardening`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Improve nlpdata publication so bounded backfills and refreshes are safer under failure and easier to recover without inconsistent current-state tables. Review staging vs publish behavior, improve partial-run safety, improve rerun idempotence and bounded-scope recovery, clarify sequential vs parallel backfill safety, and improve run-level diagnostics around failed or partial publication."

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-08

- Q: Where should the publish safety boundary live for a bounded `nlpdata` run? → A: All affected rows for the bounded scope stage first, then one coordinated publish-finalization step promotes them together.
- Q: When may bounded publishes run in parallel? → A: Serialize only publishes whose affected current-state scope overlaps; non-overlapping scopes may run independently.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recover Safely After a Failed Bounded Publish (Priority: P1)

An operator running a bounded refresh or backfill needs a failed publish to be
safe to rerun without leaving current-state `nlpdata` tables in a mixed old/new
state for the affected scope.

**Why this priority**: Partial-run safety is the core failure mode named by the
issue. If reruns are not safe, every later backfill or diagnostics feature sits
on unstable publish semantics.

**Independent Test**: Trigger a publish failure during a bounded run, rerun the
same bounded scope, and verify that the published rows for the affected scope
end in one consistent final state with no duplicated current rows.

**Acceptance Scenarios**:

1. **Given** a bounded publish that fails after some tables are updated,
   **When** the same bounded scope is rerun, **Then** the final published state
   for that scope is internally consistent across all affected `nlpdata`
   tables.
2. **Given** a bounded rerun after a failed publish, **When** the rerun
   completes successfully, **Then** operators do not need manual table cleanup
   to restore a valid current-state view for that scope.

---

### User Story 2 - Publish Backfills With Clear Safety Rules (Priority: P2)

An operator planning multiple backfills needs explicit guidance on which runs
may execute sequentially, which may overlap safely, and which scopes require
serialization to avoid conflicting current-state updates.

**Why this priority**: Once rerun safety exists, the next operational risk is
using the publish mechanism incorrectly during backfills. The system needs
clear, test-backed rules for bounded run coordination.

**Independent Test**: Evaluate documented sequential and overlapping backfill
examples and verify that operators can classify them as safe, unsafe, or
requires serialization without inventing local rules.

**Acceptance Scenarios**:

1. **Given** two bounded publish jobs with overlapping affected scope,
   **When** an operator evaluates the publish rules, **Then** it is clear
   whether those runs must be serialized.
2. **Given** two bounded publish jobs with non-overlapping affected scope,
   **When** an operator evaluates the publish rules, **Then** it is clear
   whether they can run independently without corrupting current-state tables.

---

### User Story 3 - Diagnose Failed or Partial Publication Clearly (Priority: P3)

An operator investigating a failed or incomplete publish needs run-level
diagnostics that explain what publish stage ran, what scope was affected, and
whether recovery or rerun is required.

**Why this priority**: Harder publish semantics are not useful if failures are
opaque. Operators need enough diagnostics to distinguish safe reruns from
manual intervention cases.

**Independent Test**: Inspect the documented run diagnostics for successful,
failed, and partial publish cases and verify that an operator can determine the
publish outcome and the next recovery step.

**Acceptance Scenarios**:

1. **Given** a publish that fails before finalizing its affected scope,
   **When** the operator inspects run diagnostics, **Then** the diagnostics show
   that the publish was incomplete and identify the affected scope.
2. **Given** a successful rerun after an incomplete publish, **When** the
   operator inspects run diagnostics, **Then** the diagnostics make it clear
   that the scope is now fully published and no stale partial state remains.

### Edge Cases

- What happens when a publish fails after staging data remotely but before all
  affected tables finalize their new current rows?
- What happens when a rerun begins while a previous run for the same bounded
  scope is still incomplete?
- How does the system behave when one bounded run overlaps only part of the
  message scope or current-state scope of another run?
- What happens when a publish fails after current rows are deactivated in one
  table but before matching rows are activated in another?
- How does the system diagnose a run that staged artifacts successfully but
  never reached its publish-finalization step?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define one bounded-scope publish strategy for
  `nlpdata` tables that avoids leaving affected current-state tables in a
  partially finalized state after failure.
- **FR-001a**: In the first implementation, all rows for the bounded publish
  scope MUST stage before any coordinated publish-finalization step promotes
  the new current-state view for the affected scope.
- **FR-002**: The system MUST support safe rerun of a failed bounded publish
  for the same scope without requiring manual cleanup of current-state rows.
- **FR-003**: The system MUST define how staged artifacts, publish activation,
  and current-row replacement relate to each other during a bounded publish.
- **FR-004**: The system MUST make rerun idempotence explicit for the bounded
  publish scope so operators can distinguish safe reruns from conflicting new
  publishes.
- **FR-005**: The system MUST define which `nlpdata` tables participate in
  coordinated publish-finalization for current-state behavior.
- **FR-006**: The system MUST clarify whether overlapping bounded publishes are
  safe, unsafe, or require serialization for each affected scope class.
- **FR-007**: The system MUST document the operational safety rules for
  sequential versus parallel backfills.
- **FR-007a**: In the first implementation, bounded publishes whose affected
  current-state scope overlaps MUST be serialized, while non-overlapping
  bounded scopes MAY run independently.
- **FR-008**: The system MUST record run-level publish diagnostics that identify
  the publish scope, publish stage reached, and whether the run ended in a
  `staged`, `finalized`, `failed`, or `partial` state.
- **FR-009**: The system MUST distinguish staging success from publish success
  in run-level diagnostics and recovery rules.
- **FR-010**: The system MUST define the recovery path for an incomplete
  bounded publish, including when rerun alone is sufficient and when manual
  intervention is required.
- **FR-010a**: In the first implementation, manual intervention MUST be
  required when diagnostics cannot confirm the bounded scope, cannot confirm
  the finalization stage reached, or show that another overlapping publish for
  the same current-state scope is still active.
- **FR-011**: The system MUST keep publish semantics clearly documented so
  downstream operators and diagnostics consumers do not infer conflicting local
  rules.
- **FR-012**: The system MUST provide automated tests that cover partial-run
  failure, rerun recovery, and bounded-scope publish consistency.

### Key Entities *(include if feature involves data)*

- **Bounded Publish Scope**: The set of interactions or derived rows whose
  current-state view is being refreshed or backfilled together.
- **Publish Stage**: A named step in the publish lifecycle such as staging,
  activation, deactivation, finalization, or cleanup.
- **Partial Publish State**: A run outcome in which some publish stages
  completed for the bounded scope but the scope was not fully finalized across
  all affected tables.
- **Recovery Rule**: An explicit rule describing whether a failed or partial
  publish can be rerun directly or requires manual intervention.
- **Publish Diagnostics Record**: Run-level metadata describing scope, stage,
  outcome, and recovery posture for a publish attempt.

## Assumptions

- This feature is focused on local `nlpdata` publish semantics and does not
  change cross-repo ownership boundaries from ADR 002.
- The affected publish path includes both local derived artifacts and the
  Databricks table publication flow used by `build_nlpdata --deploy`.
- Current-state tables such as `message_person_links`, `message_theme_tags`,
  and `message_search_docs` are the highest-risk surfaces for partial-run
  inconsistency because they replace prior current rows.
- Bounded-scope safety matters more than global all-table atomicity in the
  first hardening pass.
- The first hardening pass will use a coordinated publish-finalization step per
  bounded scope rather than allowing each table to finalize independently.
- The first hardening pass will allow independent execution only for bounded
  publishes whose affected current-state scopes do not overlap.
- The initial implementation may tighten publish ordering and diagnostics
  without redesigning the entire staging mechanism.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `README.md`, `docs/ROADMAP.md`,
  `specs/005-nlpdata-publish-hardening/` planning artifacts, and any publish or
  Databricks usage guidance touched by the final strategy
- **Behavior Change Summary**: Documentation must explain the hardened publish
  lifecycle, rerun and recovery rules, coordinated current-state behavior, and
  sequential versus parallel backfill safety
- **Local Test Plan**: Add or update automated tests for partial-run failure,
  rerun recovery, bounded publish consistency, and run diagnostics; run
  `uv run pytest` before deployment

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/004-nlpdata-publish-semantics.md`
- **Architectural Scope**: Defines the bounded publish lifecycle, current-state
  coordination rules, and recovery/diagnostics model for `nlpdata`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a bounded publish failure simulation, operators can rerun the
  same scope and restore a single consistent published state for all affected
  current-state tables without manual row cleanup.
- **SC-002**: Maintainers can classify at least five representative backfill or
  refresh examples as safe to overlap, requires serialization, or safe only as
  a rerun of the same failed scope with no contradictory interpretation.
- **SC-003**: Automated tests cover failed publish, rerun recovery, and
  bounded-scope consistency so regressions in publish semantics are caught
  locally before deployment.
- **SC-004**: Operators can inspect run diagnostics for successful, failed, and
  partial publish cases and determine whether the run is `staged`,
  `finalized`, `failed`, or `partial` plus the next recovery step without
  consulting unpublished tribal knowledge.
