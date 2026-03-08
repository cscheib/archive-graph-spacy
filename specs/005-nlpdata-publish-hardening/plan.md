# Implementation Plan: nlpdata Publish Hardening

**Branch**: `005-nlpdata-publish-hardening` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-nlpdata-publish-hardening/spec.md`

**Related Issues**:
- Intended to close `archive-graph-spacy#3`
- Depends on the current `nlpdata` deployment path in `archive-graph-spacy`
- Unblocks diagnostics and review surfaces in `archive-graph-data#73`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Harden the `nlpdata` publish path so bounded runs stage their full affected
scope first, then finalize current-state updates through one coordinated
publish step. The implementation will document and test rerun recovery,
overlap/serialization rules, and run-level publish diagnostics without
introducing a separate deployment subsystem.
Manual intervention is reserved for cases where diagnostics cannot confirm the
bounded scope, cannot confirm the finalization stage reached, or show that an
overlapping publish for the same current-state scope is still active.

## Technical Context

**Language/Version**: Python 3.12 for local pipeline, deployment, and validation code  
**Primary Dependencies**: Existing `archive_graph_spacy.nlpdata` deploy/pipeline modules, Databricks SQL client helpers, pytest, `uv`  
**Storage**: Local JSONL-derived outputs plus Databricks Delta tables in `personal_archive_dev.nlpdata`  
**Testing**: `uv run pytest` with focused coverage in `tests/test_nlpdata_deploy.py` plus related pipeline/build tests  
**Target Platform**: Local CLI-driven publish flow and Databricks SQL/DBFS deployment path  
**Project Type**: Python library plus CLI-backed data-derivation and deployment pipeline  
**Performance Goals**: Preserve current bounded-run throughput while making publish recovery deterministic; operators must be able to rerun a failed bounded scope without manual row cleanup  
**Constraints**: Keep the design inside the existing `build_nlpdata --deploy` path; use one coordinated publish-finalization step per bounded scope; serialize overlapping bounded scopes; avoid speculative global transaction orchestration outside current requirements  
**Scale/Scope**: One repo-local hardening slice covering current-state `nlpdata` publication, rerun recovery, bounded-scope overlap rules, and diagnostics sufficient to close `archive-graph-spacy#3`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec exists and is current for the work described in this plan. `PASS`
- Approach uses the simplest design that satisfies the current documented requirement; any extra complexity is listed in Complexity Tracking with a rejected simpler alternative. `PASS`
- Local tests required for this change are identified, including the commands that must pass before deployment. `PASS`
- Documentation updates required by behavior changes are identified and scoped. `PASS`
- Architectural changes identify the decision record to create or amend. `PASS` (`docs/adr/004-nlpdata-publish-semantics.md`)

**Post-Design Re-Check**: `PASS`. The design keeps publish hardening inside the
existing deployment path, adds only the minimum publish-state/diagnostics model
needed for current requirements, and records the operational model in one new
ADR plus the feature contract artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/005-nlpdata-publish-hardening/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── bounded-publish-semantics.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
├── ROADMAP.md
└── adr/
   ├── 003-reviewed-assertions-promotion-model.md
   └── 004-nlpdata-publish-semantics.md

src/archive_graph_spacy/
├── nlpdata/
│   ├── deploy.py
│   ├── models.py
│   ├── pipeline.py
│   └── runs.py
└── scripts/
   └── build_nlpdata.py

tests/
├── test_nlpdata_deploy.py
├── test_nlpdata_pipeline.py
└── test_scripts_build_nlpdata.py
```

**Structure Decision**: Implement publish hardening in the existing
`archive_graph_spacy.nlpdata` deployment path. `deploy.py` owns the coordinated
publish-finalization rules, `runs.py`/`models.py` extend run diagnostics as
needed, `build_nlpdata.py` exposes the resulting diagnostics and CLI recovery
posture, and the new
contract artifact documents bounded-scope safety and recovery behavior.

## Complexity Tracking

No constitution violations are currently required. The plan explicitly rejects
adding a separate publish coordinator service or cross-run lock manager because
the current requirement is bounded-scope safety and rerun clarity, not a new
distributed deployment architecture.
