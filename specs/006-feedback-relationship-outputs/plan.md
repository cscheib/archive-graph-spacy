# Implementation Plan: Feedback Consumption and Relationship Outputs

**Branch**: `006-feedback-relationship-outputs` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-feedback-relationship-outputs/spec.md`

**Related Issues**:
- Intended to close `archive-graph-spacy#10`
- Intended to close `archive-graph-spacy#11`
- Covers the first implementation slice of `archive-graph-spacy#14`
- Depends on completed reviewed-state and publish-hardening work from `archive-graph-spacy#3` and `archive-graph-spacy#4`
- Unblocks `archive-graph-spacy#13` and downstream UI consumption in `archive-graph-data#78`

## Summary

Extend the existing `nlpdata` pipeline so Phase 3 becomes contract-bearing and
replayable: consume reviewed outcomes directly from `graph-data` review tables,
apply deterministic downstream reviewed effects, publish one canonical
`person_person_edges` row per pair plus bounded `person_person_edge_evidence`,
and add the first non-v1 candidate assertion family
`relationship_evidence_review`. The design stays inside the existing
`build_nlpdata` orchestration and publish path, reuses the shared candidate
assertion lifecycle, and records small explicit diagnostics categories instead
of introducing a second review or relationship pipeline.

## Technical Context

**Language/Version**: Python 3.12 for local pipeline, deployment, and validation code  
**Primary Dependencies**: Existing `archive_graph_spacy.nlpdata` pipeline/deploy modules, `archive_graph_spacy.edges`, Databricks SQL client helpers, pytest, `uv`  
**Storage**: Local JSONL-derived outputs plus Databricks Delta tables in `personal_archive_dev.nlpdata`; reviewed inputs read from `personal_archive_dev.memory`  
**Testing**: `uv run pytest` with focused coverage in `tests/test_nlpdata_candidate_assertions.py`, `tests/test_nlpdata_pipeline.py`, `tests/test_person_person_edges.py`, `tests/test_scripts_build_nlpdata.py`, and Databricks/deploy tests where output contracts change  
**Target Platform**: Local CLI-driven derivation plus Databricks-backed source/deploy path  
**Project Type**: Python library plus CLI-backed data-derivation and contract-publication pipeline  
**Performance Goals**: Preserve deterministic bounded-run behavior while keeping reviewed-input replay and relationship publication cheap enough for normal `build_nlpdata` reruns; diagnostics must remain bounded and operator-readable  
**Constraints**: Keep the design inside the existing `build_nlpdata` and `nlpdata` publish path; consume review tables directly rather than adding snapshot storage; use strict semantic replay keys with bounded evidence-window tolerance; publish one summary row per pair plus bounded evidence rows; keep `relationship_evidence_review` inside the shared reviewed lifecycle and `derived_only` boundary  
**Scale/Scope**: One Phase 3 spacy slice covering reviewed-feedback consumption, pairwise relationship contracts, one expanded candidate family, and the diagnostics needed to support later phase-oriented derivation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec exists and is current for the work described in this plan. `PASS`
- Approach uses the simplest design that satisfies the current documented requirement; any extra complexity is listed in Complexity Tracking with a rejected simpler alternative. `PASS`
- Local tests required for this change are identified, including the commands that must pass before deployment. `PASS`
- Documentation updates required by behavior changes are identified and scoped. `PASS`
- Architectural changes identify the decision record to create or amend. `PASS` (`docs/adr/003-reviewed-assertions-promotion-model.md` and `docs/adr/005-phase-first-class-object.md`)

**Post-Design Re-Check**: `PASS`. The design stays within the existing
pipeline, extends current contracts rather than adding parallel storage or
review paths, and records the Phase 3 boundary by amending existing ADRs
instead of creating a speculative new architecture layer.

## Project Structure

### Documentation (this feature)

```text
specs/006-feedback-relationship-outputs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── feedback-and-relationship-contracts.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
└── adr/
   ├── 003-reviewed-assertions-promotion-model.md
   └── 005-phase-first-class-object.md

src/archive_graph_spacy/
├── edges/
│   └── person_person.py
├── nlpdata/
│   ├── contracts.py
│   ├── deploy.py
│   ├── models.py
│   ├── pipeline.py
│   ├── person_links.py
│   ├── runs.py
│   ├── source_loader.py
│   └── spark_views.py
└── scripts/
   ├── build_edges.py
   └── build_nlpdata.py

tests/
├── test_nlpdata_candidate_assertions.py
├── test_nlpdata_databricks.py
├── test_nlpdata_pipeline.py
├── test_nlpdata_runs.py
├── test_nlpdata_source_loader.py
├── test_person_person_edges.py
├── test_scripts_build_edges.py
└── test_scripts_build_nlpdata.py
```

**Structure Decision**: Implement Phase 3 entirely inside the existing
`archive_graph_spacy` derivation stack. `source_loader.py` and
`pipeline.py` own reviewed-input loading and orchestration,
`person_links.py` extends candidate families and replay behavior,
`edges/person_person.py` plus `pipeline.py` own pairwise relationship
aggregation, `contracts.py`/`spark_views.py`/`deploy.py` extend the published
artifact and Databricks contract surfaces, and tests stay fixture-driven in the
existing pipeline suites.

## Complexity Tracking

No constitution violations are currently required. The plan explicitly rejects:

- creating a second durable reviewed-state store in `archive-graph-spacy`
- introducing a special-case relationship review queue outside candidate assertions
- publishing multi-row-per-pair facet tables in the first contract pass
