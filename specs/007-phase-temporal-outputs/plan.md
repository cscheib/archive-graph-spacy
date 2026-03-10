# Implementation Plan: Phase and Temporal Outputs

**Branch**: `007-phase-temporal-outputs` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-phase-temporal-outputs/spec.md`

**Related Issues**:
- Intended to close `archive-graph-spacy#13`
- Depends on completed Phase 3 feedback and relationship outputs from `archive-graph-spacy#10`, `archive-graph-spacy#11`, and `archive-graph-spacy#14`
- Unblocks downstream consumption in `archive-graph-data#78`
- Must remain consistent with [ADR 005](../../../docs/adr/005-phase-first-class-object.md)

## Summary

Extend the existing `nlpdata` derivation with a first-class Phase 4 contract:
infer owner-centric temporal segments using deterministic time-gap
segmentation plus merge rules; publish one canonical `phases` table plus child
tables for central people, dominant themes, temporal pair summaries, temporal
pair evidence, representative interactions, and phase diagnostics; and keep
weak segments out of the main contract by suppressing them into diagnostics.
The design stays inside the existing `build_nlpdata` and deploy path so
`archive-graph-data#78` can plan against stable phase outputs rather than
reconstructing temporal semantics locally.

## Technical Context

**Language/Version**: Python 3.12 for local pipeline, deployment, and validation code  
**Primary Dependencies**: Existing `archive_graph_spacy.nlpdata` pipeline/deploy modules, Phase 3 relationship outputs, Databricks SQL client helpers, pytest, `uv`  
**Storage**: Local JSONL-derived outputs plus Databricks Delta tables in `personal_archive_dev.nlpdata`; phase outputs remain derived-only and are published through the current `nlpdata` contract surface  
**Testing**: `uv run pytest` with focused coverage in phase-oriented pipeline, deploy, script, and Databricks suites plus the full local regression suite  
**Target Platform**: Local CLI-driven derivation plus Databricks-backed source/deploy path  
**Project Type**: Python library plus CLI-backed data-derivation and contract-publication pipeline  
**Performance Goals**: Preserve bounded-run behavior by deriving phases, child aggregates, and diagnostics within the current `build_nlpdata` pass; keep representative interactions and pair evidence deterministic and capped per phase aggregate; keep diagnostics operator-readable and bounded  
**Constraints**: Use one canonical `phases` table plus child tables; derive boundaries from deterministic time-gap segmentation with merge rules; publish phase-bounded pair summary rows plus bounded evidence rows; reuse canonical `pair_id` and relationship-output inputs from Phase 3 `person_person_edges`; suppress weak phases from published outputs and record them only in diagnostics; keep outputs owner-centric and clearly non-canonical; defer curated labels and boundary overrides  
**Scale/Scope**: One Phase 4 upstream slice covering inferred phases, phase aggregates, temporal pair outputs, bounded diagnostics, and the contract handoff required for `archive-graph-data#78`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec exists and is current for the work described in this plan. `PASS`
- Approach uses the simplest design that satisfies the current documented requirement; any extra complexity is listed in Complexity Tracking with a rejected simpler alternative. `PASS`
- Local tests required for this change are identified, including the commands that must pass before deployment. `PASS`
- Documentation updates required by behavior changes are identified and scoped. `PASS`
- Architectural changes identify the decision record to create or amend. `PASS` ([ADR 005](../../../docs/adr/005-phase-first-class-object.md) plus new `docs/adr/006-phase-output-contract.md`)

**Post-Design Re-Check**: `PASS`. The design stays inside the current
`nlpdata` derivation and deploy path, introduces one explicit Phase 4 contract
instead of UI-side reconstruction, and records the table-level boundary in an
ADR rather than leaving it implicit in issue text.

## Project Structure

### Documentation (this feature)

```text
specs/007-phase-temporal-outputs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── phase-output-contracts.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
└── adr/
   ├── 005-phase-first-class-object.md
   └── 006-phase-output-contract.md

data_samples/
└── phase_temporal_outputs/
   ├── contacts.jsonl
   └── messages.jsonl

src/archive_graph_spacy/
├── nlpdata/
│   ├── contracts.py
│   ├── deploy.py
│   ├── models.py
│   ├── pipeline.py
│   ├── runs.py
│   ├── spark_views.py
│   └── source_loader.py
└── scripts/
   └── build_nlpdata.py

tests/
├── test_nlpdata_pipeline.py
├── test_nlpdata_deploy.py
├── test_nlpdata_databricks.py
├── test_nlpdata_runs.py
├── test_phase_outputs.py
└── test_scripts_build_nlpdata.py
```

**Structure Decision**: Implement Phase 4 entirely inside the existing
`archive_graph_spacy` derivation stack. `pipeline.py` orchestrates phase and
child-aggregate derivation, `models.py`/`contracts.py`/`spark_views.py` define
the published contract, `runs.py` records bounded diagnostics,
`deploy.py` extends Databricks table management, `build_nlpdata.py` surfaces
the new outputs, and fixture-driven tests validate determinism without adding
a second temporal subsystem.

## Complexity Tracking

No constitution violations are currently required. The plan explicitly rejects:

- adding a separate temporal segmentation job outside `build_nlpdata`
- publishing only raw phase membership and forcing consumers to reconstruct
  summaries locally
- introducing curated labels or manual boundary overrides in the first Phase 4
  upstream slice
- emitting weak phases into the main contract with placeholder confidence rows
