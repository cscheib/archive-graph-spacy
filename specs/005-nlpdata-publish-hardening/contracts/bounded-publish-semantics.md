# Contract: Bounded Publish Semantics

## Purpose

Define the bounded-scope publish model for `archive-graph-spacy#3` so publish
recovery, reruns, and diagnostics follow one explicit rule set.

## Related Issues

- Intended to close `archive-graph-spacy#3`
- Unblocks diagnostics and review surfaces in `archive-graph-data#73`

## Coordinated Publish Rule

- A bounded run must stage all rows for its affected scope before any
  coordinated publish-finalization step promotes the new current-state view.
- Current-state tables participating in coordinated finalization are the ones
  that replace prior `is_current = true` rows for the affected scope.
- A bounded run is not considered published until coordinated finalization
  completes for all affected current-state tables.

## Overlap And Serialization Rules

| Scope Relationship | Allowed Behavior | Operator Rule |
|--------------------|------------------|---------------|
| Same bounded scope rerun after failure | Allowed | Rerun the same scope serially until one finalized outcome succeeds |
| Overlapping current-state scope | Not allowed in parallel | Serialize publish attempts |
| Non-overlapping current-state scope | Allowed | Runs may proceed independently |

## Publish Outcomes

| Outcome | Meaning | Recovery Posture |
|---------|---------|------------------|
| `staged` | Artifacts copied and ready, but finalization not started | Safe to finalize or rerun according to operator workflow |
| `finalized` | Coordinated finalization completed across all affected tables | No recovery required |
| `partial` | Finalization started but the bounded scope is not fully consistent | Same-scope rerun required unless diagnostics mark manual intervention |
| `failed` | Publish attempt ended without a valid finalized scope | Rerun or follow explicit diagnostics guidance |

## Diagnostics Requirements

Every publish attempt must expose diagnostics sufficient to answer:

- what bounded scope was affected
- which publish stage was reached
- which tables finalized successfully
- whether the run ended in `finalized`, `partial`, or `failed` state
- whether same-scope rerun is allowed directly
- whether manual intervention is required before rerun
- whether overlap serialization prevented concurrent publish

## Recovery Guarantees

- Same-scope rerun is the preferred recovery mechanism for failed or partial
  bounded publishes when diagnostics do not require manual intervention.
- Manual intervention is required when diagnostics cannot confirm the bounded
  scope, cannot confirm the finalization stage reached, or show that another
  overlapping publish for the same current-state scope is still active.
- Publish diagnostics must distinguish staging success from final publish
  success.
- Operators must not infer parallel safety locally; the publish contract is the
  source of truth for overlap behavior.

## Representative Publish Examples

| Example | Classification | Reason |
|---------|----------------|--------|
| Same bounded scope rerun after a `failed` publish | Safe only as rerun | The rerun completes the same bounded scope without introducing a conflicting new publish |
| Same bounded scope rerun after a `partial` publish | Safe only as rerun | Recovery stays inside the original bounded scope and restores one final current-state view |
| Two publishes with overlapping current-state scope | Requires serialization | Parallel finalization could produce conflicting current rows |
| Two publishes with non-overlapping current-state scope | Safe to overlap | Their coordinated finalization does not target the same current-state rows |
| Publish with missing scope/finalization diagnostics or an active overlapping publish | Manual intervention required | Operators cannot prove rerun safety from diagnostics alone |
