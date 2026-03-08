# Quickstart: Candidate Assertions

## Goal

Validate that the candidate-generation design is specific enough to implement
`archive-graph-spacy#2` on top of the current `nlpdata` pipeline and hand off a
reviewable candidate surface to downstream consumers.

## Artifacts

- [spec.md](spec.md)
- [plan.md](plan.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [candidate-assertions-surface.md](contracts/candidate-assertions-surface.md)
- [Reviewed Assertions Lifecycle](../003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md)
- [ADR 003](../../docs/adr/003-reviewed-assertions-promotion-model.md)

## Validation Scenarios

### Scenario 1: Confirm first-wave assertion types and review classes

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and [candidate-assertions-surface.md](contracts/candidate-assertions-surface.md).
2. Confirm that only `relay_sender_identity` and `person_link_disambiguation`
   are emitted in v1.
3. Confirm that `relay_sender_identity` remains `promotion_eligible` and
   `person_link_disambiguation` remains `derived_only`.

### Scenario 2: Confirm disambiguation selection rules

1. Read [spec.md](spec.md) and [research.md](research.md).
2. Check three mention-link examples:
   - one with a clear winning canonical person
   - one with multiple plausible candidates and no clear winner
   - one low-confidence case with only one plausible person
3. Confirm that only the multi-candidate/no-clear-winner case emits a
   `person_link_disambiguation` candidate.

### Scenario 3: Confirm persisted output and diagnostics summary requirements

1. Read [data-model.md](data-model.md) and [candidate-assertions-surface.md](contracts/candidate-assertions-surface.md).
2. Confirm that the design requires both:
   - `candidate_assertions.jsonl`
   - `candidate_assertions_summary.json`
3. Confirm that both surfaces name the required payload fields and that neither
   surface implies canonical truth.

### Scenario 3a: Confirm relay sender minimum emission rules

1. Read [spec.md](spec.md) and [candidate-assertions-surface.md](contracts/candidate-assertions-surface.md).
2. Confirm that a relay sender candidate requires:
   - a subject canonical ID
   - an unresolved relay-like sender address
   - at least one supporting link signal beyond the raw sender value
   - provenance naming the source message and derivation path
3. Confirm that weaker relay cases are suppressed rather than emitted as reviewable candidates.

### Scenario 4: Confirm deterministic rerun semantics

1. Read [spec.md](spec.md), [research.md](research.md), and [candidate-assertions-surface.md](contracts/candidate-assertions-surface.md).
2. Confirm that candidate identity is stable within a generation scope.
3. Confirm that reruns regenerate the same logical candidate set rather than
   inventing duplicate competing records.

## Local Verification Commands

Run these before implementation or merge:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
uv run python -m archive_graph_spacy.scripts.build_nlpdata data_samples/candidate_assertions
uv run pytest
```

Expected local candidate fixture result:

- `candidate_assertions.jsonl` contains 5 records
- `candidate_assertions_summary.json` reports:
  - 2 `relay_sender_identity`
  - 3 `person_link_disambiguation`
  - suppression of low-value ambiguity cases such as shared surnames or
    single-candidate low-confidence mentions
- On 2026-03-08, `uv run pytest` passed with `67 passed`
- On 2026-03-08, `uv run python -m archive_graph_spacy.scripts.build_nlpdata data_samples/candidate_assertions`
  completed with:
  - `input_interaction_count = 7`
  - `output_row_counts.candidate_assertions = 5`
  - `quality_metrics.suppressed_disambiguation_low_value = 3`

## Expected Outcome

- `archive-graph-spacy#2` has one implementation-ready planning slice for
  candidate generation.
- The design stays within the ownership and lifecycle rules from ADR 002 and
  ADR 003.
- `archive-graph-data#71` can consume a named candidate surface instead of
  inventing a local pre-review payload.
