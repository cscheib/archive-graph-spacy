# Archive Graph Spacy

Experimental spaCy and entity-linking workspace for analysis on exports from
`graph-data`.

## Tooling

- `uv` manages the virtual environment, dependency resolution, and lockfile.
- Python is pinned to `3.12` because spaCy support typically lags the newest
  CPython release.

## Purpose

This repository is not the system of record. `graph-data` owns canonical
entities, ingestion, and the durable graph. This repo is for testing:

- mention extraction from message text
- candidate linking from mentions to canonical people
- scoring and evaluation on exported snapshots
- local derivation of `nlpdata`-style search tables before Databricks deployment
- analysis of failure modes before changes flow back to the main project

## Cross-Repo Contract

The shared boundary between `archive-graph-data` and `archive-graph-spacy` is
published here:

- [Cross-Repo Contract Spec](specs/002-formalize-cross-repo-contract/spec.md)
- [Cross-Repo Boundary Contract](specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md)
- [ADR 002: Cross-Repo Contract](docs/adr/002-cross-repo-contract.md)

Use those documents as the source of truth for ownership, join semantics,
provenance, reviewed assertions, and promotion boundaries instead of repeating
that logic in local notes or issue bodies.

## Reviewed Assertions Model

The first reviewed-assertions lifecycle for candidate review and explicit
promotion is also published here:

- [Reviewed Assertions Spec](specs/003-reviewed-assertions-pipeline/spec.md)
- [Reviewed Assertions Lifecycle Contract](specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md)
- [ADR 003: Reviewed Assertions Promotion Model](docs/adr/003-reviewed-assertions-promotion-model.md)

Use those documents when implementing candidate review, review decisions,
accepted reviewed storage, or upstream promotion handoff. They intentionally
separate candidate generation in this repo from durable review and override
ownership in `archive-graph-data`.

## Quickstart

```bash
uv python install 3.12
uv sync --dev
uv run pytest
uv run python -m archive_graph_spacy.scripts.build_nlpdata data_samples
uv run python -m archive_graph_spacy.scripts.run_sample data_samples/sample_messages.jsonl
uv run python -m archive_graph_spacy.scripts.run_export data_exports/graph-data-sample
uv run python -m archive_graph_spacy.scripts.build_edges data_exports/graph-data-sample
uv run python -m archive_graph_spacy.scripts.query_edges data_exports/graph-data-sample/derived --query top_pairs
uv run python -m archive_graph_spacy.scripts.visualize_ego data_exports/graph-data-sample/derived p-alice
```

## Environment

Python entrypoints load `.env` automatically via `python-dotenv`. Set the
archive owner once and let the query and visualization tools use it as the
default owner filter:

```bash
cp .env.example .env
```

Example `.env`:

```dotenv
OWNER_PERSON_ID=p_0270000ea9de
```

You can still override this explicitly with `--owner-person-id` on the CLI or
with the Owner Controls in the web app. The default owner mode is `downrank`,
which keeps the owner visible but surfaces non-owner relationships first.

## Install a spaCy model

```bash
uv run python -m spacy download en_core_web_sm
```

## Project layout

```text
src/archive_graph_spacy/io.py          # Export-loading helpers
src/archive_graph_spacy/nlpdata/       # Derived search-workspace pipeline
src/archive_graph_spacy/extract/       # Mention extraction logic
src/archive_graph_spacy/link/          # Candidate entity linking
src/archive_graph_spacy/evaluate/      # Metrics and scoring
src/archive_graph_spacy/scripts/       # Small experiment entrypoints
data_samples/                          # Small checked-in redacted fixtures
tests/                                 # Local automated tests
```

## Export workflow

1. Export a small message/contact snapshot from `graph-data`.
2. Normalize it into the schemas used in `archive_graph_spacy.io`.
3. Run extraction and linking experiments here.
4. Review scored results before deciding what belongs in the main project.

Example export command from `graph-data`:

```bash
uv run python scripts/export_spacy_snapshot.py \
  data_exports/graph-data-sample \
  --people-limit 250 \
  --message-limit 1000
```

This writes:

```text
data_exports/graph-data-sample/
├── contacts.jsonl
└── messages.jsonl
```

To build queryable person-message edges from that bundle:

```bash
uv run python -m archive_graph_spacy.scripts.build_edges data_exports/graph-data-sample
```

To build local `nlpdata` tables from the same bundle:

```bash
uv run python -m archive_graph_spacy.scripts.build_nlpdata data_exports/graph-data-sample
```

This writes:

```text
data_exports/<bundle>/derived/nlpdata/
├── nlp_runs.jsonl
├── message_mentions.jsonl
├── message_person_links.jsonl
├── message_theme_tags.jsonl
└── message_search_docs.jsonl
```

To stage and deploy those derived tables into Databricks:

```bash
uv run python -m archive_graph_spacy.scripts.build_nlpdata \
  data_exports/graph-data-sample \
  --deploy \
  --profile cscheib-free-ws \
  --catalog personal_archive_dev \
  --schema nlpdata
```

This uses the local Databricks CLI for auth and DBFS staging, then writes Delta
tables through the SQL Statements API.

For managed Databricks assets and deployment, this repo now includes a
Databricks Asset Bundle:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev nlpdata_refresh
```

The bundle deploys the project wheel plus a notebook-driven refresh job that
uses Spark SQL to read directly from `personal_archive_dev.gold` and
`personal_archive_dev.memory`, then writes `personal_archive_dev.nlpdata`.

For the agreed historical backfill windows, use the canned sequential job:

```bash
databricks bundle run -t dev nlpdata_backfill
```

That job runs these windows in order:
- `1974-01-01` to `2013-01-01`
- `2013-01-01` to `2017-07-01`
- `2017-07-01` to `2018-07-01`
- `2018-07-01` to `2019-07-01`
- `2019-07-01` to `2020-07-01`
- `2020-07-01` to `2021-07-01`
- `2021-07-01` to `2022-07-01`
- `2022-07-01` to `2023-07-01`
- `2023-07-01` to `2024-07-01`
- `2024-07-01` to `2025-07-01`
- `2025-07-01` to `2026-07-01`

The emitted rows distinguish explicit metadata edges (`sender`, `recipient`)
from inferred mention edges (`mentioned`).

The command now returns two views:

- `person_message_edges`: one aggregated row per `(person_id, message_id, role)`
- `person_message_edge_evidence`: the supporting evidence rows used to build
  those aggregates
- `person_person_edges`: one aggregated row per person-pair across messages
- `person_person_edge_evidence`: the message-level evidence rows behind those
  person-pair relationships

It also writes persistent JSONL tables under:

```text
data_exports/<bundle>/derived/
```

You can inspect them quickly with DuckDB:

```bash
uv run python -m archive_graph_spacy.scripts.query_edges \
  data_exports/graph-data-sample/derived \
  --query top_pairs
```

And render a small ego-network HTML view:

```bash
uv run python -m archive_graph_spacy.scripts.visualize_ego \
  data_exports/graph-data-sample/derived \
  p-alice \
  --output analysis/ego_p_alice.html
```

To render the whole person-only network instead:

```bash
uv run python -m archive_graph_spacy.scripts.visualize_graph \
  data_exports/graph-data-sample/derived \
  --output analysis/network_graph.html
```

To browse and refresh these visualizations from a local web app instead of
running the render scripts manually:

```bash
uv run python -m archive_graph_spacy.scripts.webapp --port 8000
```

Then open `http://127.0.0.1:8000/`.

Keep large or sensitive exports out of Git. Use `data_exports/` locally and
only commit small redacted fixtures under `data_samples/`.
