# Data Model: nlpdata Publish Hardening

## Bounded Publish Scope

**Purpose**: Represent the set of rows whose current-state view is refreshed or
backfilled together in one coordinated publish.

**Fields**
- `run_id`: Publish attempt identifier
- `run_scope`: Source or bounded backfill scope already carried by the run
- `affected_message_ids`: Message-level keys or equivalent bounded identifiers
- `affected_tables`: Current-state tables participating in finalization
- `overlap_class`: Whether the scope overlaps another active bounded publish

**Validation Rules**
- Must identify the exact bounded scope affected by finalization
- Must be stable enough to compare overlap between runs
- Must distinguish overlapping from non-overlapping publish scopes

## Publish Stage

**Purpose**: Represent where a bounded publish stopped or completed.

**States**
- `staged`: Artifacts copied and ready for publish-finalization
- `finalizing`: Coordinated current-state replacement is in progress
- `finalized`: All affected tables reflect one consistent published scope
- `partial`: Some finalization work ran but the scope is not fully consistent
- `failed`: Publish attempt ended before a valid final state was reached

**Validation Rules**
- `finalized` implies all affected tables completed coordinated finalization
- `partial` implies rerun or manual recovery guidance is required
- `failed` must distinguish failure before versus during finalization

## Publish Diagnostics Record

**Purpose**: Extend run-level diagnostics with publish-specific recovery signal.

**Fields**
- `run_id`
- `publish_scope`
- `publish_stage`
- `publish_outcome`
- `overlap_policy`
- `recovery_action`
- `staged_path`
- `finalized_tables`
- `failed_tables`
- `manual_intervention_required`

**Validation Rules**
- Must distinguish staging success from publish success
- Must identify the next operator action for recovery
- Must remain readable from run metadata or CLI diagnostics
- Must set `manual_intervention_required = true` when scope or finalization
  stage cannot be confirmed, or when an overlapping publish remains active

## Recovery Rule

**Purpose**: Define whether a failed or partial run can be rerun directly.

**Fields**
- `publish_outcome`
- `rerun_allowed`
- `requires_serialization`
- `manual_intervention_required`
- `operator_notes`

**Validation Rules**
- Same-scope rerun should be the default recovery path when safe
- Manual intervention should be explicit and rare
- Overlap-sensitive scopes must carry serialization guidance

## Relationships

- One `RefreshRun` may have one bounded publish scope and one publish
  diagnostics record.
- One bounded publish scope may affect multiple current-state tables.
- One recovery rule is derived from one publish diagnostics record.
- One overlapping-scope assessment can govern whether another bounded run may
  proceed concurrently.
