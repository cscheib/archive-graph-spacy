# Repository Guidelines

## Project Structure & Module Organization

This repository is an experimentation harness around `graph-data` exports.
Application code lives in `src/archive_graph_spacy/` with subpackages for
`nlpdata/`, `extract/`, `link/`, `evaluate/`, and lightweight `scripts/`.
Tests live in `tests/` and should mirror the module they cover, for example
`tests/test_link_person.py` for `src/archive_graph_spacy/link/person.py`.

Project process templates and the governing constitution live under
`.specify/`. Treat `.codex/`, `.venv/`, and local caches as machine-local state,
not source material.

## Build, Test, and Development Commands

- `uv sync --dev`: create/update the local virtual environment and install app
  plus dev dependencies.
- `uv run pytest`: run the local automated test suite. This is required before
  deployment.
- `uv run python -m archive_graph_spacy.scripts.run_sample data_samples/sample_messages.jsonl`:
  run the sample extraction/linking pipeline against a fixture export.
- `uv run python -m archive_graph_spacy.scripts.build_nlpdata data_exports/<name>`:
  derive local `nlpdata` tables with run metadata, mentions, person links,
  theme tags, and search documents under `data_exports/<name>/derived/nlpdata/`.
- `uv run python -m archive_graph_spacy.scripts.build_nlpdata data_exports/<name> --deploy --profile <profile>`:
  stage the derived `nlpdata` bundle to DBFS and write
  `personal_archive_dev.nlpdata` Delta tables through the Databricks SQL
  Statements API.
- `databricks bundle validate -t dev`:
  validate the Databricks Asset Bundle in [databricks.yml](/Users/chris/src/archive-graph-spacy/databricks.yml).
- `databricks bundle deploy -t dev`:
  deploy the project wheel and `nlpdata_refresh` job resources to Databricks.
- `databricks bundle run -t dev nlpdata_refresh`:
  execute the bundle-managed refresh job against Databricks source tables.
- `uv run python -m archive_graph_spacy.scripts.run_export data_exports/<name>`:
  run the extraction/linking pipeline against a `graph-data` export bundle.
- `uv run python -m archive_graph_spacy.scripts.build_edges data_exports/<name>`:
  emit aggregated `person_message_edges` plus raw `person_message_edge_evidence`
  for sender/recipient/mentioned links, and derived `person_person_edges` from
  co-participation and mention relationships.
- `uv run python -m archive_graph_spacy.scripts.query_edges data_exports/<name>/derived --query top_pairs`:
  run a preset DuckDB query against persisted derived edge tables.
- `uv run python -m archive_graph_spacy.scripts.visualize_ego data_exports/<name>/derived <person_id>`:
  render a small HTML ego-network from `person_person_edges`.
- Python entrypoints load repo-local `.env` automatically. Set
  `OWNER_PERSON_ID` there when using owner-aware graph filters. The default
  owner mode is `downrank`; change it in the UI or with `--owner-mode`.
- `uv run python -m spacy download en_core_web_sm`: install a local English
  model for manual experimentation.
- `uv lock`: refresh `uv.lock` after dependency changes.

Use Python `3.12` as pinned in `.python-version`.

## Coding Style & Naming Conventions

Follow standard Python conventions: 4-space indentation, type hints on public
functions, and small modules with explicit responsibilities. Use `snake_case`
for modules, files, functions, and variables; use `PascalCase` for classes.
Prefer deterministic helpers and explicit scoring reasons over opaque magic.
Keep this repo focused on experiments, not canonical graph ownership.

## Testing Guidelines

Use `pytest`. Every code change must include or update local automated tests,
and bug fixes must add a test that fails before the fix. Name tests
`test_<behavior>.py` and functions `test_<expected_outcome>()`. Keep tests
focused on observable behavior, not internal implementation details. Favor
small redacted fixtures in `data_samples/` over live archive material.

## Data Handling

Do not commit real archives, contact dumps, or credentials. Large or sensitive
exports belong in ignored local directories such as `data_exports/`. If a
change depends on a real-world edge case, reduce it to the smallest safe
fixture before adding it to the repo.

## Commit & Pull Request Guidelines

Recent history uses short, imperative commits with optional prefixes, such as
`docs: ratify constitution v1.0.0 and align spec templates`. Prefer
`type: summary` when a clear category exists (`docs`, `feat`, `fix`, `test`).

Pull requests should include a brief description, the related spec or issue,
the local test command(s) run, and any documentation or ADR updates required by
the change.

## Active Technologies
- Python 3.12 for local validation and pipeline development + spaCy, pytest, Databricks Workspace/SQL client, Delta tables (001-nlpdata-schema)
- Databricks Delta tables in `personal_archive_dev.nlpdata`; source inputs from `personal_archive_dev.gold` and `personal_archive_dev.memory` (001-nlpdata-schema)
- Markdown-first planning artifacts for a Python 3.12 repository + Existing repo docs/spec workflow, pytest, `uv`, GitHub issues/projects (002-formalize-cross-repo-contract)
- Markdown specs under `specs/`; ADRs under `docs/adr/` (002-formalize-cross-repo-contract)

## Recent Changes
- 001-nlpdata-schema: Added the local `nlpdata` pipeline, builder CLI, run metadata, and message-level search workspace contracts
