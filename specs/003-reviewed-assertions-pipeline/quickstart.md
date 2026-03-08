# Quickstart: Reviewed Assertions Pipeline

## Goal

Validate that the reviewed-assertions planning set is sufficient to close
`archive-graph-spacy#4` and unblock the dependent review workflow issues.

## Artifacts

- [spec.md](spec.md)
- [plan.md](plan.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [reviewed-assertions-lifecycle.md](contracts/reviewed-assertions-lifecycle.md)
- [ADR 002](../../docs/adr/002-cross-repo-contract.md)
- [ADR 003](../../docs/adr/003-reviewed-assertions-promotion-model.md)

## Validation Scenarios

### Scenario 1: Classify reviewed states

1. Read [spec.md](spec.md) and [data-model.md](data-model.md).
2. Take five representative assertions:
   - accepted relay sender identity
   - rejected relay sender identity
   - accepted-but-not-promoted disambiguation
   - promotion-eligible accepted assertion awaiting human promotion
   - promoted canonical override outcome
3. Confirm each example can be classified as candidate-only, review decision,
   accepted reviewed assertion, or promotion outcome without contradiction.

### Scenario 2: Confirm acceptance vs promotion boundary

1. Read [spec.md](spec.md) and [reviewed-assertions-lifecycle.md](contracts/reviewed-assertions-lifecycle.md).
2. Trace an assertion from candidate generation to accepted reviewed storage.
3. Confirm that no step writes canonical truth until an explicit human promotion
   action occurs.

### Scenario 3: Confirm downstream integration readiness

1. Read [reviewed-assertions-lifecycle.md](contracts/reviewed-assertions-lifecycle.md).
2. Map at least three downstream interactions:
   - display a candidate assertion in a review UI
   - capture a review decision
   - hand off a promotion-eligible accepted assertion to override workflows
3. Confirm each interaction has a defined input/output boundary and owner.

### Scenario 4: Confirm explicit field-level handoff contract

1. Read [data-model.md](data-model.md) and [reviewed-assertions-lifecycle.md](contracts/reviewed-assertions-lifecycle.md).
2. Confirm the following field groups are named consistently in both artifacts:
   - candidate handoff fields
   - review decision capture fields
   - promotion handoff fields
3. Confirm no downstream team would need to invent local payload fields for the
   initial workflow.

## Local Verification Commands

Run these before closing the planning issue or starting follow-on code work:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
uv run pytest
```

Validation recorded on 2026-03-08:

- `uv run pytest` -> `62 passed`
- `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` confirmed the active feature path resolves to `specs/003-reviewed-assertions-pipeline/`

## Expected Outcome

- `archive-graph-spacy#4` has one complete planning set for the reviewed
  assertions lifecycle.
- The issue explicitly closes the model/workflow gap left by ADR 002.
- `archive-graph-spacy#2`, `archive-graph-data#70`, and
  `archive-graph-data#71` can reference this lifecycle contract instead of
  inventing local review-state rules.
