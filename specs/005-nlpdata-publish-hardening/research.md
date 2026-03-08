# Phase 0 Research: nlpdata Publish Hardening

## Decision: Use a coordinated publish-finalization step per bounded scope

**Rationale**: The current failure mode comes from finalizing current-state
tables independently. A bounded run is safer when all rows for the affected
scope stage first and one publish-finalization step promotes the new scope
state together.

**Alternatives considered**:
- Keep table-by-table finalization
  - rejected because failure after one table deactivates current rows can leave
    the scope in a mixed old/new state
- Add compensating rollback logic to every table update
  - rejected because it increases complexity without producing a clearer
    recovery model than coordinated finalization

## Decision: Serialize only overlapping bounded current-state scopes

**Rationale**: Full serialization is safer than overlapping writes, but
serializing every bounded publish would unnecessarily slow backfills. The
minimal useful rule is to serialize only runs whose affected current-state
scope overlaps.

**Alternatives considered**:
- Serialize all bounded publishes
  - rejected because non-overlapping scopes can run independently without
    conflicting current-state replacement
- Allow overlapping publishes and rely on rerun recovery
  - rejected because overlapping current-state writes would reintroduce the
    exact ambiguity this issue is meant to remove

## Decision: Model publish outcome as staged, finalized, failed, or partial

**Rationale**: Operators need to know whether a run only staged data, fully
finalized it, or left the scope incomplete. A small explicit publish-state
model is enough to support recovery and diagnostics without redesigning run
metadata broadly.

**Alternatives considered**:
- Keep only a generic completed/failed run status
  - rejected because it cannot distinguish staging success from publish
    success, or a partial finalization from a fully failed run
- Add a large event log for every publish step
  - rejected because the current issue only requires bounded-scope recovery and
    operational clarity, not full event-sourcing

## Decision: Treat rerun of the same failed bounded scope as the primary recovery path

**Rationale**: The issue asks for rerunnable bounded runs. Recovery should
default to rerunning the same scope against staged or freshly restaged data,
with manual intervention reserved only for cases the diagnostics explicitly
mark as unrecoverable.

**Alternatives considered**:
- Require manual cleanup after any failed publish
  - rejected because it defeats the core safety goal and increases operator
    burden
- Automatically revert all partial work on any failure
  - rejected because rollback complexity is higher than the current
    requirement, and rerun semantics are easier to test and reason about

## Decision: Persist publish diagnostics in the deploy result and `nlp_runs`

**Rationale**: Operators need the same recovery signal whether they inspect the
CLI result immediately or later inspect run metadata. Persisting the publish
diagnostics payload in both places keeps the deploy path simple while still
making recovery posture durable.

**Alternatives considered**:
- Return diagnostics only from the CLI command
  - rejected because run-level diagnostics would disappear once the command
    output was lost
- Create a separate diagnostics table for publish state
  - rejected because the current issue only requires bounded publish recovery
    clarity, not a broader publish event model

## Decision: Extend the existing deploy tests instead of introducing a separate publish harness

**Rationale**: `tests/test_nlpdata_deploy.py` already exercises the staging and
SQL statement flow. The simplest compliant path is to add bounded failure and
recovery tests there, then extend pipeline/build tests only where diagnostics
surface outward.

**Alternatives considered**:
- Create a dedicated publish-simulation framework
  - rejected because the current test surface already covers the relevant
    deployment path
- Test recovery only through manual quickstart steps
  - rejected because the constitution requires local automated tests for code
    behavior changes
