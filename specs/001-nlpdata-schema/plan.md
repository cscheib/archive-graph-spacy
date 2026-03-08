# Implementation Plan: NLP Search Workspace

**Branch**: `001-nlpdata-schema` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-nlpdata-schema/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Create a new derived workspace in `personal_archive_dev.nlpdata` that supports
person-centric and theme-aware search over archive interactions. The design
keeps canonical source data in existing archive tables, writes message-level
Delta outputs into `nlpdata`, preserves provenance and run metadata, avoids
duplicating full interaction text into the search-ready layer, and aligns
Databricks table contracts and refresh behavior with proven upstream patterns.

## Technical Context

**Language/Version**: Python 3.12 for local validation and pipeline development  
**Primary Dependencies**: spaCy, pytest, Databricks Workspace/SQL client, Delta tables  
**Storage**: Databricks Delta tables in `personal_archive_dev.nlpdata`; source inputs from `personal_archive_dev.gold` and `personal_archive_dev.memory`  
**Testing**: `pytest` for local behavior plus validation queries against the dev schema  
**Target Platform**: Local `uv`-managed Python tooling and Databricks SQL warehouse / Unity Catalog  
**Project Type**: Data pipeline and search-workspace derivation  
**Performance Goals**: Support bounded refresh validation on 10,000 interactions in under 15 minutes and record run metadata for every produced dataset  
**Constraints**: Dev catalog only; message-level search records only in v1; no duplicated full interaction text in `nlpdata`; reuse canonical people and effective classifications; local tests must pass before deployment  
**Scale/Scope**: Initial workspace includes run metadata, message mentions, person-message links, theme tags, and message-level search documents for the full dev interaction corpus

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec exists and is current for the work described in this plan. `PASS`
- Approach uses the simplest design that satisfies the current documented
  requirement; any extra complexity is listed in Complexity Tracking with a
  rejected simpler alternative. `PASS`
- Local tests required for this change are identified, including the commands
  that must pass before deployment. `PASS`
- Documentation updates required by behavior changes are identified and scoped.
  `PASS`
- Architectural changes identify the decision record to create or amend.
  `PASS` (`docs/adr/001-nlpdata-search-workspace.md`)

## Project Structure

### Documentation (this feature)

```text
specs/001-nlpdata-schema/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── nlpdata-tables.md
└── tasks.md
```

### Source Code (repository root)

```text
src/archive_graph_spacy/
├── config.py
├── io.py
├── nlpdata/
│   ├── __init__.py
│   ├── contracts.py
│   ├── models.py
│   ├── source_loader.py
│   ├── mentions.py
│   ├── person_links.py
│   ├── themes.py
│   ├── search_docs.py
│   ├── runs.py
│   └── pipeline.py
├── scripts/
│   └── build_nlpdata.py
└── webapp.py

tests/
├── test_nlpdata_models.py
├── test_nlpdata_links.py
├── test_nlpdata_themes.py
├── test_nlpdata_search_docs.py
├── test_nlpdata_runs.py
├── test_nlpdata_pipeline.py
└── test_scripts_build_nlpdata.py
```

**Structure Decision**: `archive-graph-spacy` owns implementation, validation,
and deployment of `personal_archive_dev.nlpdata`. `graph-data` remains a
read-only upstream source of canonical people, interactions, classifications,
and overrides. The implementation may borrow patterns from `graph-data`, but
`graph-data` is not an implementation dependency for this feature.

## Complexity Tracking

No constitution violations are currently required. The design intentionally
avoids thread-level search documents, full-text duplication, and speculative
LLM-only enrichment in the first rollout.
