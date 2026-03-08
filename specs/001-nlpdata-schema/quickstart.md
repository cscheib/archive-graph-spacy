# Quickstart: NLP Search Workspace

## Goal

Validate the `nlpdata` search-workspace design locally, then deploy and verify a
message-level derived workspace in `personal_archive_dev`.

## 1. Prepare Local Tooling

```bash
uv sync --dev
uv run pytest tests/test_nlpdata_links.py tests/test_nlpdata_search_docs.py
uv run pytest tests/test_nlpdata_themes.py tests/test_nlpdata_runs.py tests/test_nlpdata_pipeline.py
uv run pytest tests/test_nlpdata_databricks.py tests/test_nlpdata_deploy.py
uv run pytest tests/test_scripts_build_nlpdata.py
uv run python -m archive_graph_spacy.scripts.build_nlpdata data_samples
```

## 2. Validate Read-Only Upstream Inputs

Confirm the implementation is reading canonical inputs from `graph-data` as a
read-only upstream source rather than writing new pipeline code there.

## 3. Verify Contract Expectations

Before implementation, confirm the planned v1 contract artifacts:

- [data-model.md](/Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/data-model.md)
- [nlpdata-tables.md](/Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/contracts/nlpdata-tables.md)
- [research.md](/Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/research.md)

## 4. Implement And Deploy To `personal_archive_dev.nlpdata`

Deployment-ready implementation must:

- create the `nlpdata` schema in the dev catalog if it does not already exist
- create or reuse the target Delta tables using the local `nlpdata` DDL
  contracts
- derive message-level mentions, person links, theme tags, and search docs
- write run metadata for every refresh
- support rerunning a bounded scope without leaving duplicate current rows

Example deployment command:

```bash
uv run python -m archive_graph_spacy.scripts.build_nlpdata \
  data_exports/graph-data-sample \
  --deploy \
  --profile cscheib-free-ws \
  --catalog personal_archive_dev \
  --schema nlpdata
```

Bundle-managed deployment:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev nlpdata_refresh
```

The bundle-managed refresh uses Spark SQL for source reads and writes inside
Databricks. Use the SDK/SQL Statements path only for small validation queries,
not for full backfills.

For the agreed historical backfill plan, run the canned sequential bundle job:

```bash
databricks bundle run -t dev nlpdata_backfill
```

## 5. Post-Deployment Validation

After deployment, validate:

- expected `nlpdata` tables exist
- row counts are recorded in `nlp_runs`
- current-state uniqueness holds for:
  - search documents by `message_id`
  - person links by `(message_id, person_id, role)`
  - theme tags by `(message_id, theme)`
- search documents include source references but not duplicated full text

## 6. Release Gate

Do not deploy unless:

- the active spec is current
- the ADR is written or updated
- local automated tests pass
- documentation changes are ready in the same change
