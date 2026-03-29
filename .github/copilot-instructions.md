# Copilot Instructions

## Repository Purpose

This repository is an **experimental spaCy and entity-linking workspace** for
analysis on exports from `graph-data`. It is **not** the system of record.
`graph-data` owns canonical entities, ingestion, and the durable graph. This
repo is for testing mention extraction, candidate linking, scoring, local
derivation of `nlpdata`-style search tables, and analysis of failure modes
before changes flow back to the main project.

## Project Layout

```text
src/archive_graph_spacy/         # All application code
  io.py                          # Export-loading helpers
  models.py                      # Shared data models
  config.py                      # Config and env loading
  ner.py                         # spaCy NER utilities
  nlpdata/                       # Canonical pipeline (SUPPORTED)
  extract/                       # Mention extraction logic
  link/                          # Candidate entity linking
  evaluate/                      # Metrics and scoring [EXPERIMENTAL]
  edges/                         # Person-message and person-person edge builders
  scripts/                       # CLI entrypoints (see Surface Classification)
  webapp.py                      # Local graph viewer [EXPERIMENTAL]
tests/                           # Automated tests mirroring src/ modules
data_samples/                    # Small checked-in redacted fixtures
specs/                           # Feature spec documents (numbered 001–008)
docs/adr/                        # Architecture Decision Records
docs/PROCESS_TRANSFORMATIONS.md  # Internal pipeline data flow reference
docs/ROADMAP.md                  # Planned surface retirement
tools/                           # Developer tools (version guard, deploy helper)
databricks.yml                   # Databricks Asset Bundle definition
pyproject.toml                   # Python project and dependency config
```

## Python Version and Tooling

- Python is pinned to **3.12** (see `.python-version` and `pyproject.toml`).
- Dependency management uses **`uv`** (not pip or poetry).
- Testing uses **`pytest`** only — no other test framework.

## Essential Commands

```bash
# Set up environment
uv sync --dev

# Run all tests (required before deployment)
uv run pytest

# Run the primary local derivation pipeline
uv run python -m archive_graph_spacy.scripts.build_nlpdata data_samples

# Run the sample extraction/linking pipeline against a fixture
uv run python -m archive_graph_spacy.scripts.run_sample data_samples/sample_messages.jsonl

# Derive person-message and person-person edges
uv run python -m archive_graph_spacy.scripts.build_edges data_exports/<name>

# Query derived edge tables with DuckDB
uv run python -m archive_graph_spacy.scripts.query_edges data_exports/<name>/derived --query top_pairs

# Visualize an ego network as HTML
uv run python -m archive_graph_spacy.scripts.visualize_ego data_exports/<name>/derived <person_id>

# Start the local web app
uv run python -m archive_graph_spacy.scripts.webapp --port 8000

# Refresh dependency lockfile
uv lock

# Install a spaCy model for local experimentation
uv run python -m spacy download en_core_web_sm

# Enable the repo pre-commit hook (run once per clone)
git config core.hooksPath .githooks
```

## Surface Classification

### Supported (Primary Product Path)

| Surface | Description |
|---------|-------------|
| `scripts/build_nlpdata.py` | Primary derivation pipeline; contract-enforced; Databricks-publishable |
| `scripts/build_edges.py` | Local person-message and person-person edge derivation |
| `scripts/query_edges.py` | DuckDB query helper for local derived edge tables |
| `scripts/visualize_ego.py` | Local ego-network HTML rendering |
| `scripts/visualize_graph.py` | Local full person-network HTML rendering |
| `nlpdata/` | All canonical pipeline modules (pipeline, deploy, contracts, models) |

### Experimental (Local Exploration Only)

These carry an `[EXPERIMENTAL]` marker in their module docstrings and are
**not** primary product surfaces:

| Surface | Description | Superseded By |
|---------|-------------|--------------|
| `scripts/run_export.py` | Raw extraction/linking against an export bundle | `build_nlpdata` pipeline |
| `scripts/run_sample.py` | Extraction/linking against sample fixtures | `pytest` or `build_nlpdata data_samples` |
| `scripts/webapp.py` / `webapp.py` | Local graph viewer web app | Downstream review UI in `archive-graph-data` |
| `evaluate/scoring.py` | Simple candidate-link summarizer | `nlpdata` candidate assertions diagnostics |

## Coding Style and Conventions

- **4-space indentation**, type hints on all public functions.
- `snake_case` for modules, files, functions, and variables; `PascalCase` for
  classes.
- Small modules with explicit responsibilities — prefer deterministic helpers
  and explicit scoring reasons over opaque magic.
- Keep the repo focused on experiments, not canonical graph ownership.
- Do not commit real archives, contact dumps, or credentials. Large or sensitive
  exports belong in `data_exports/` (git-ignored).

## Testing Guidelines

- Every code change must include or update local automated tests.
- Bug fixes must add a test that **fails before the fix**.
- Name test files `test_<behavior>.py` and functions `test_<expected_outcome>()`.
- Mirror the module under test: `tests/test_link_person.py` covers
  `src/archive_graph_spacy/link/person.py`.
- Keep tests focused on observable behavior, not internal implementation details.
- Favor small redacted fixtures in `data_samples/` over live archive material.

## nlpdata Pipeline Overview

The primary pipeline (`nlpdata/`) runs through these stages:

1. **Load** — read `contacts.jsonl` + `messages.jsonl` from a bundle directory
   (or Databricks source tables when `--deploy` is used).
2. **Extract** — derive `message_mentions` from raw message text using spaCy.
3. **Link** — map mentions and senders/recipients to canonical person IDs,
   producing `message_person_links`.
4. **Replay** — re-apply accepted `reviewed_assertions` from
   `graph-data`/`memory` tables to override raw link decisions.
5. **Theme** — tag messages with `message_theme_tags`.
6. **Search docs** — produce `message_search_docs` for workspace search.
7. **Candidate assertions** — emit `candidate_assertions.jsonl` +
   `candidate_assertions_summary.json` for first-wave human review.
8. **Edges** — derive `person_person_edges` and related evidence tables.
9. **Phases** — segment the accumulated message stream into bounded temporal
   phases producing `phases.jsonl` and `phase_*` child tables.
10. **Deploy** (optional, `--deploy`) — bounded publish to
    `personal_archive_dev.nlpdata` Delta tables on Databricks.

### Bounded Publish Semantics

Current-state tables (`message_person_links`, `message_theme_tags`,
`message_search_docs`) use a two-phase publish:
- **Stage**: new rows are written as `is_current=False`.
- **Finalize**: old current rows are deactivated, staged rows activated, per
  table.

Diagnostics report `staged`, `finalized`, `partial`, or `failed` outcomes and
include recovery guidance when `manual_intervention` is required.

## Derived Output Files

Running `build_nlpdata` against a bundle writes to
`data_exports/<bundle>/derived/nlpdata/`:

```text
nlp_runs.jsonl
message_mentions.jsonl
message_person_links.jsonl
message_theme_tags.jsonl
message_search_docs.jsonl
candidate_assertions.jsonl
candidate_assertions_summary.json
reviewed_effects.jsonl
person_person_edges.jsonl
person_person_edge_evidence.jsonl
phases.jsonl
phase_central_people.jsonl
phase_theme_summaries.jsonl
phase_pair_summaries.jsonl
phase_pair_evidence.jsonl
phase_representative_interactions.jsonl
phase_diagnostics.jsonl
```

## Candidate Assertions

First-wave candidate generation produces pre-review, non-canonical candidates:

- `relay_sender_identity` — relay-like unresolved senders with supporting
  inferred person-link signal (promotion-eligible after human acceptance).
- `person_link_disambiguation` — multi-candidate, no-clear-winner first-name
  ambiguity cases (derived-only).
- `relationship_evidence_review` — pairwise cases with mixed direct/indirect
  evidence.

See `specs/004-candidate-assertions/` and
`specs/003-reviewed-assertions-pipeline/` for lifecycle contracts.

## Key Design Decisions (ADRs)

| ADR | Topic |
|-----|-------|
| `docs/adr/001-nlpdata-search-workspace.md` | nlpdata pipeline and schema |
| `docs/adr/002-cross-repo-contract.md` | Cross-repo boundary with `archive-graph-data` |
| `docs/adr/003-reviewed-assertions-promotion-model.md` | Reviewed assertions lifecycle |
| `docs/adr/004-nlpdata-publish-semantics.md` | Bounded publish with finalization |
| `docs/adr/005-phase-first-class-object.md` | Phase as derived first-class object |
| `docs/adr/006-phase-output-contract.md` | Phase output contract surface |

## Cross-Repo Boundary

The shared boundary between `archive-graph-spacy` and `archive-graph-data` is
defined in `specs/002-formalize-cross-repo-contract/`. Always consult those
documents for ownership, join semantics, provenance, reviewed assertions, and
promotion boundaries rather than repeating that logic in code comments or issue
bodies.

## Environment Setup

Copy `.env.example` to `.env` and set `OWNER_PERSON_ID` to your archive
owner's person ID. All Python entrypoints load `.env` automatically via
`python-dotenv`. You can override with `--owner-person-id` on the CLI.

## Commit and PR Guidelines

- Use short, imperative commit messages with optional type prefixes:
  `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- PR descriptions should include: a brief description, the related spec or
  issue, the test command(s) run, and any documentation or ADR updates required.

## Pre-commit Hook

The `.githooks/pre-commit` hook runs `tools/check_wheel_version.py`. It
requires a `[project].version` bump in `pyproject.toml` whenever staged changes
touch packaged source under `src/archive_graph_spacy/`, and ensures
`databricks.yml`'s `variables.wheel_version.default` stays in sync. Enable it
once per clone with `git config core.hooksPath .githooks`.

## Databricks Integration

When `--deploy` is passed to `build_nlpdata`, the pipeline stages the derived
artifacts to DBFS and writes Delta tables through the Databricks SQL Statements
API. The Databricks Asset Bundle (`databricks.yml`) manages the project wheel
and the `nlpdata_refresh` and `nlpdata_backfill` jobs.

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
uv run python tools/deploy_bundle.py dev   # use when packaged Python changed
databricks bundle run -t dev nlpdata_refresh
databricks bundle run -t dev nlpdata_backfill
```

Use `tools/deploy_bundle.py` (not `databricks bundle deploy` directly) when
packaged Python code has changed, to ensure the wheel path in Databricks
serverless caching is refreshed.

## Known Patterns and Gotchas

- Web app bundle discovery only includes directories containing **both**
  `contacts.jsonl` and `messages.jsonl`.
- Canonical person-pair IDs are produced by
  `edges.person_person.canonical_pair_id()`: sorted person IDs → SHA-1 digest →
  `pair-` prefix.
- `CURRENT_STATE_TABLES` (`message_person_links`, `message_theme_tags`,
  `message_search_docs`) are the only tables with `is_current` flag that
  participate in coordinated publish finalization.
- Never run `databricks bundle deploy` without first ensuring the wheel version
  is bumped when packaged source changed — the hook and
  `tools/check_wheel_version.py` enforce this, but CI will fail without it.
- `data_exports/` is git-ignored. Never commit real export bundles. Use
  `data_samples/` for small checked-in fixtures only.
