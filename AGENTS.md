# Repository Guidelines

## Project Structure & Module Organization

This repository is a small `src/`-layout Python project for spaCy-based NER
work. Application code lives in `src/archive_graph_spacy/`. Keep reusable NLP
helpers there, grouped by concern rather than by experiment. Tests live in
`tests/` and should mirror the module they cover, for example
`tests/test_ner.py` for `src/archive_graph_spacy/ner.py`.

Project process templates and the governing constitution live under
`.specify/`. Treat `.codex/`, `.venv/`, and local caches as machine-local state,
not source material.

## Build, Test, and Development Commands

- `uv sync --dev`: create/update the local virtual environment and install app
  plus dev dependencies.
- `uv run pytest`: run the local automated test suite. This is required before
  deployment.
- `uv run python -m spacy download en_core_web_sm`: install a local English
  model for manual experimentation.
- `uv lock`: refresh `uv.lock` after dependency changes.

Use Python `3.12` as pinned in `.python-version`.

## Coding Style & Naming Conventions

Follow standard Python conventions: 4-space indentation, type hints on public
functions, and small modules with explicit responsibilities. Use `snake_case`
for modules, files, functions, and variables; use `PascalCase` for classes.
Prefer simple, current-need implementations over premature abstractions or
speculative feature flags.

## Testing Guidelines

Use `pytest`. Every code change must include or update local automated tests,
and bug fixes must add a test that fails before the fix. Name tests
`test_<behavior>.py` and functions `test_<expected_outcome>()`. Keep tests
focused on observable behavior, not internal implementation details.

## Commit & Pull Request Guidelines

Recent history uses short, imperative commits with optional prefixes, such as
`docs: ratify constitution v1.0.0 and align spec templates`. Prefer
`type: summary` when a clear category exists (`docs`, `feat`, `fix`, `test`).

Pull requests should include a brief description, the related spec or issue,
the local test command(s) run, and any documentation or ADR updates required by
the change.
