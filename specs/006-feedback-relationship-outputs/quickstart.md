# Quickstart: Feedback Consumption and Relationship Outputs

## Goal

Validate that Phase 3 is specific enough to implement `archive-graph-spacy#10`
and `archive-graph-spacy#11`, plus the first expansion slice of
`archive-graph-spacy#14`, inside the existing `nlpdata` pipeline.

## Artifacts

- [spec.md](spec.md)
- [plan.md](plan.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [feedback-and-relationship-contracts.md](contracts/feedback-and-relationship-contracts.md)

## Validation Scenarios

### Scenario 1: Confirm reviewed-feedback consumption semantics

1. Read [spec.md](spec.md), [research.md](research.md), and
   [feedback-and-relationship-contracts.md](contracts/feedback-and-relationship-contracts.md).
2. Confirm that reviewed inputs are consumed directly from `graph-data` review
   tables and remain read-only in `archive-graph-spacy`.
3. Confirm that accepted reviewed outcomes can apply downstream effects, while
   rejected or resolved cases suppress re-emission for the same semantic case.
4. Confirm that materially conflicting accepted reviewed outcomes are marked
   `conflicted` and are not auto-applied.

### Scenario 2: Confirm replay matching behavior

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and
   [feedback-and-relationship-contracts.md](contracts/feedback-and-relationship-contracts.md).
2. Confirm that replay uses a strict semantic key plus bounded evidence-window
   tolerance.
3. Confirm that exact subject and claim semantics remain mandatory.
4. Confirm that broad fuzzy replay is explicitly out of scope.

### Scenario 3: Confirm relationship-output contract shape

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and
   [feedback-and-relationship-contracts.md](contracts/feedback-and-relationship-contracts.md).
2. Confirm that the initial contract publishes:
   - one canonical summary row per pair in `person_person_edges`
   - bounded supporting evidence rows in `person_person_edge_evidence`
3. Confirm that downstream consumers can explain a pair from published fields
   plus bounded evidence without recomputing pair semantics.

### Scenario 4: Confirm candidate-family expansion behavior

1. Read [spec.md](spec.md), [research.md](research.md), and
   [feedback-and-relationship-contracts.md](contracts/feedback-and-relationship-contracts.md).
2. Confirm that `relationship_evidence_review` is the first new candidate
   family in this Phase 3 slice.
3. Confirm that it remains `derived_only` and uses the same reviewed lifecycle,
   replay model, and diagnostics categories as the existing candidate families.

## Local Verification Commands

Run these before implementation or merge:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
uv run pytest tests/test_nlpdata_candidate_assertions.py tests/test_nlpdata_pipeline.py tests/test_person_person_edges.py tests/test_scripts_build_nlpdata.py tests/test_scripts_build_edges.py
uv run pytest tests/test_nlpdata_runs.py tests/test_nlpdata_deploy.py tests/test_nlpdata_databricks.py
uv run pytest
```

## Latest Validation Result

- `2026-03-10`: implementation validation passed
- Focused Phase 3 suite:
  - `uv run pytest -o addopts='' tests/test_nlpdata_candidate_assertions.py tests/test_nlpdata_pipeline.py tests/test_person_person_edges.py tests/test_scripts_build_nlpdata.py tests/test_scripts_build_edges.py tests/test_nlpdata_runs.py tests/test_nlpdata_deploy.py tests/test_nlpdata_databricks.py`
  - result: `38 passed`
- Full local regression:
  - `uv run pytest -o addopts=''`
  - result: `91 passed, 1 skipped`

## Expected Outcome

- `archive-graph-spacy#10` has an implementation-ready plan for read-only
  reviewed-feedback consumption and replay handling
- `archive-graph-spacy#11` has one explicit pairwise relationship contract for
  `nlpdata`
- the first expansion slice of `archive-graph-spacy#14` is bounded to
  `relationship_evidence_review` inside the shared reviewed lifecycle
- `archive-graph-spacy#13` can plan against stable reviewed and relationship
  outputs rather than unresolved Phase 3 seams
