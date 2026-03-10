# Quickstart: Phase and Temporal Outputs

## Goal

Validate that Phase 4 is specific enough to implement
`archive-graph-spacy#13` inside the existing `nlpdata` pipeline and provide a
stable upstream contract for `archive-graph-data#78`.

## Artifacts

- [spec.md](spec.md)
- [plan.md](plan.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [phase-output-contracts.md](contracts/phase-output-contracts.md)
- bounded fixture bundle under `data_samples/phase_temporal_outputs/` with
  `contacts.jsonl` and `messages.jsonl`

## Validation Scenarios

### Scenario 1: Confirm phase-object contract shape

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and
   [phase-output-contracts.md](contracts/phase-output-contracts.md).
2. Confirm that the Phase 4 contract uses one `phases` table plus child tables
   for central people, themes, temporal pairs, representative interactions,
   and diagnostics.
3. Confirm that downstream consumers can support phase list/detail exploration
   without recomputing segmentation locally.

### Scenario 2: Confirm boundary semantics

1. Read [spec.md](spec.md), [research.md](research.md), and
   [phase-output-contracts.md](contracts/phase-output-contracts.md).
2. Confirm that phase boundaries are produced from deterministic time-gap
   segmentation plus merge rules.
3. Confirm that weak segments are suppressed from the main contract and only
   recorded in diagnostics.

### Scenario 3: Confirm temporal pair and aggregate outputs

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and
   [phase-output-contracts.md](contracts/phase-output-contracts.md).
2. Confirm that each published phase can be joined to central people, dominant
   themes, temporal pair summaries, temporal pair evidence, and representative
   interactions using published artifacts only.
3. Confirm that `pair_id` reuse from Phase 3 remains explicit.

### Scenario 4: Confirm the downstream handoff boundary

1. Read [spec.md](spec.md), [plan.md](plan.md), and
   [phase-output-contracts.md](contracts/phase-output-contracts.md).
2. Confirm that `archive-graph-data#78` is expected to consume and render the
   published phase outputs rather than define local temporal semantics.
3. Confirm that curated labels and manual boundary overrides are out of scope
   for this upstream slice.

## Local Verification Commands

Run these before implementation or merge:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
uv run pytest tests/test_phase_outputs.py tests/test_nlpdata_pipeline.py tests/test_scripts_build_nlpdata.py
uv run pytest tests/test_nlpdata_deploy.py tests/test_nlpdata_databricks.py tests/test_nlpdata_runs.py
uv run pytest
```

## Expected Outcome

- `archive-graph-spacy#13` has an implementation-ready plan for first-class
  inferred phase outputs
- the upstream Phase 4 contract is stable enough for `archive-graph-data#78`
  to plan against
- the repo boundary stays explicit: upstream derivation owns semantics and the
  UI consumes those published outputs
