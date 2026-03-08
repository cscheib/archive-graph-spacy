# ADR 004: nlpdata Publish Semantics

## Status

Accepted

## Context

`build_nlpdata --deploy` stages derived `nlpdata` JSONL artifacts to DBFS and
then writes Databricks Delta tables through the SQL Statements API. The prior
deploy flow deactivated and replaced current rows table-by-table, which left
bounded backfills vulnerable to mixed current-state results when a publish
failed mid-run.

Issue `archive-graph-spacy#3` requires safer partial-run behavior, same-scope
rerun recovery, explicit overlap guidance, and run-level publish diagnostics
without introducing a separate deployment subsystem.

## Decision

The deploy path remains inside `archive_graph_spacy.nlpdata.deploy`, but it now
uses these bounded publish rules:

- Stage the full bounded scope first by inserting current-state rows as
  non-current.
- Finalize the bounded scope in a dedicated pass that deactivates prior current
  rows and activates the staged rows for the new run.
- Record one publish outcome from the set `staged`, `finalized`, `partial`, or
  `failed`.
- Treat same-scope rerun as the default recovery action for `partial` and most
  `failed` outcomes.
- Require manual intervention only when diagnostics cannot confirm the bounded
  scope, cannot confirm the finalization stage reached, or show that another
  overlapping publish for the same current-state scope is still active.
- Keep overlap policy in the deploy layer through bounded-scope comparison
  helpers instead of adding a new coordinator service.

The deploy command returns publish diagnostics in its CLI output and also
stores those diagnostics in the `nlp_runs.publish_diagnostics` payload.

## Consequences

### Positive

- Failure before finalization leaves previously current rows intact.
- Failure during finalization becomes explicitly diagnosable as `partial`.
- A rerun of the same bounded scope can restore a consistent current-state view
  without manual row cleanup.
- Operator-facing tooling can distinguish staging success from publish success.

### Negative

- The design still relies on ordered SQL updates rather than true cross-table
  transactional guarantees.
- Historical staged rows from failed runs may remain as non-current records
  until later cleanup work is introduced.
- Overlap enforcement depends on bounded-scope information available to the
  deploy caller; this slice does not add a distributed lock manager.

## Alternatives Considered

### Keep table-by-table finalization

Rejected because a failure after one table update can leave bounded current
state inconsistent.

### Add compensating rollback to every table update

Rejected because it adds more complexity than the current safety requirement
needs and is harder to reason about than deterministic rerun recovery.

### Introduce a separate publish coordinator or lock service

Rejected because the current requirement is bounded-scope safety in the
existing deploy path, not a new deployment subsystem.
