# Quickstart: nlpdata Publish Hardening

## Goal

Validate that the publish-hardening design is specific enough to implement
`archive-graph-spacy#3` inside the existing `nlpdata` deployment path.

## Artifacts

- [spec.md](spec.md)
- [plan.md](plan.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [bounded-publish-semantics.md](contracts/bounded-publish-semantics.md)

## Validation Scenarios

### Scenario 1: Confirm coordinated publish-finalization

1. Read [spec.md](spec.md), [research.md](research.md), and
   [bounded-publish-semantics.md](contracts/bounded-publish-semantics.md).
2. Confirm that a bounded run stages its full affected scope before
   current-state finalization begins.
3. Confirm that a run is not considered published until all affected
   current-state tables finalize together.

### Scenario 2: Confirm rerun recovery behavior

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and
   [bounded-publish-semantics.md](contracts/bounded-publish-semantics.md).
2. Check the documented outcomes `staged`, `finalized`, `partial`, and
   `failed`.
3. Confirm that same-scope rerun is the default recovery path when diagnostics
   do not require manual intervention.
4. Confirm that manual intervention is required when diagnostics cannot confirm
   the bounded scope, cannot confirm the finalization stage reached, or show an
   active overlapping publish for the same current-state scope.

### Scenario 3: Confirm overlap and serialization rules

1. Read [spec.md](spec.md) and
   [bounded-publish-semantics.md](contracts/bounded-publish-semantics.md).
2. Evaluate five examples:
   - rerun of the same failed bounded scope
   - rerun of the same partial bounded scope
   - two publishes with overlapping affected current-state scope
   - two publishes with non-overlapping affected current-state scope
   - publish with missing scope or finalization diagnostics
3. Confirm that the examples classify cleanly as safe to overlap, requires
   serialization, safe only as rerun, or manual intervention required.

### Scenario 4: Confirm publish diagnostics expectations

1. Read [spec.md](spec.md), [data-model.md](data-model.md), and
   [bounded-publish-semantics.md](contracts/bounded-publish-semantics.md).
2. Confirm that diagnostics must show:
   - bounded scope
   - publish stage reached
   - tables finalized or failed
   - recovery posture
   - whether manual intervention is required before rerun
3. Confirm that staging success and publish success are explicitly distinct and
   that outcome labels use `staged`, `finalized`, `partial`, and `failed`.

## Local Verification Commands

Run these before implementation or merge:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
uv run pytest tests/test_nlpdata_deploy.py tests/test_nlpdata_runs.py tests/test_nlpdata_pipeline.py tests/test_scripts_build_nlpdata.py
uv run pytest tests/test_nlpdata_deploy.py
uv run pytest
```

## Latest Validation Result

- `uv run pytest tests/test_nlpdata_deploy.py tests/test_nlpdata_runs.py tests/test_nlpdata_pipeline.py tests/test_scripts_build_nlpdata.py` -> `17 passed`
- `uv run pytest` -> `73 passed`

## Expected Outcome

- `archive-graph-spacy#3` has one implementation-ready publish semantics plan
- maintainers can explain rerun recovery and overlap safety without inventing
  local rules
- downstream diagnostics work in `archive-graph-data#73` can rely on explicit
  publish outcome and recovery semantics
