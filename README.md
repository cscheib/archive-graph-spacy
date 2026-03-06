# Archive Graph Spacy

Minimal Python project setup for named entity recognition work with spaCy.

## Tooling

- `uv` manages the virtual environment, dependency resolution, and lockfile.
- Python is pinned to `3.12` because spaCy support typically lags the newest
  CPython release.

## Quickstart

```bash
uv python install 3.12
uv sync
uv run pytest
```

## Install a spaCy model

```bash
uv run python -m spacy download en_core_web_sm
```

## Project layout

```text
src/archive_graph_spacy/   # Project package
tests/                     # Local automated tests
```

## Current scope

The initial package includes:

- a helper to build a blank English pipeline with an NER component
- a helper to extract entity spans from a processed `Doc`

As the project grows, add training configs, data assets, and decision records
only when there is a current documented need.
