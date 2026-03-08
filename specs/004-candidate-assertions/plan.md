# Implementation Plan: Candidate Assertions

**Branch**: `004-candidate-assertions` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-candidate-assertions/spec.md`

**Related Issues**:
- Intended to close `archive-graph-spacy#2`
- Extends the reviewed-assertions model from `archive-graph-spacy#4`
- Unblocks downstream candidate review work in `archive-graph-data#71`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add first-wave candidate assertion generation to the existing local `nlpdata`
pipeline. The implementation will emit reviewable candidate records for
`relay_sender_identity` and bounded `person_link_disambiguation` cases, write a
persisted candidate output surface alongside the existing derived artifacts,
and produce a human-readable diagnostics summary that makes candidate counts,
suppression reasons, and rerun semantics explicit. The design reuses the
cross-repo boundary and reviewed-assertions lifecycle contracts rather than
introducing a separate candidate-generation subsystem.

## Technical Context

**Language/Version**: Python 3.12 for local pipeline code and validation  
**Primary Dependencies**: Existing `archive_graph_spacy.nlpdata` pipeline modules, repo contracts/ADRs, pytest, `uv`  
**Storage**: Local JSONL-derived outputs under `data_exports/<bundle>/derived/nlpdata/` plus run-scoped diagnostics summaries in the same derived area  
**Testing**: `uv run pytest` with focused coverage in `tests/test_nlpdata_links.py`, `tests/test_nlpdata_pipeline.py`, `tests/test_scripts_build_nlpdata.py`, and new candidate-assertion tests  
**Target Platform**: Local repository workflow and CLI-driven bundle derivation in `archive-graph-spacy`  
**Project Type**: Python library plus CLI-backed data-derivation pipeline  
**Performance Goals**: Candidate generation must preserve deterministic rerun behavior for a given scope and expose at least five reviewable candidates with payloads and diagnostics on representative fixtures  
**Constraints**: Reuse the existing `nlpdata` pipeline shape; keep candidate assertions non-canonical; keep v1 limited to `relay_sender_identity` and multi-candidate/no-clear-winner `person_link_disambiguation`; emit both persisted candidate output and diagnostics summary; avoid speculative downstream API or database design  
**Scale/Scope**: One repo-local candidate-generation slice that extends current derived bundle outputs, closes `archive-graph-spacy#2`, and prepares downstream review ingestion for `archive-graph-data#71`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec exists and is current for the work described in this plan. `PASS`
- Approach uses the simplest design that satisfies the current documented requirement; any extra complexity is listed in Complexity Tracking with a rejected simpler alternative. `PASS`
- Local tests required for this change are identified, including the commands that must pass before deployment. `PASS`
- Documentation updates required by behavior changes are identified and scoped. `PASS`
- Architectural changes identify the decision record to create or amend. `PASS` (`docs/adr/003-reviewed-assertions-promotion-model.md`)

**Post-Design Re-Check**: `PASS`. The design keeps candidate generation inside
the existing `nlpdata` derivation path, amends ADR 003 instead of creating a
new architectural branch, and defines only the minimum persisted output and
diagnostics surfaces needed by the current issue.

## Project Structure

### Documentation (this feature)

```text
specs/004-candidate-assertions/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── candidate-assertions-surface.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
├── ROADMAP.md
└── adr/
   ├── 002-cross-repo-contract.md
   └── 003-reviewed-assertions-promotion-model.md

src/archive_graph_spacy/
├── link/
├── nlpdata/
│   ├── contracts.py
│   ├── models.py
│   ├── person_links.py
│   └── pipeline.py
└── scripts/
   └── build_nlpdata.py

tests/
├── test_nlpdata_links.py
├── test_nlpdata_pipeline.py
├── test_scripts_build_nlpdata.py
└── test_nlpdata_candidate_assertions.py
```

**Structure Decision**: Implement candidate generation as an extension of the
existing `nlpdata` derivation pipeline. `person_links.py` remains the likely
home for extracting the first-wave relay and ambiguity signals, `models.py`
gains candidate assertion record types, `pipeline.py` and `build_nlpdata.py`
carry those records into persisted outputs and diagnostics, and the new
contract artifact defines the downstream-readable candidate surface.

The implemented v1 scope further bounds those rules to:
- relay-like unresolved sender addresses for `relay_sender_identity`
- single-token leading-name ambiguities with multiple plausible people and no
  clear winner for `person_link_disambiguation`
- persisted outputs in `candidate_assertions.jsonl` and
  `candidate_assertions_summary.json`

## Complexity Tracking

No constitution violations are currently required. The design deliberately
avoids adding a separate review service, queue, or storage subsystem for v1 and
instead reuses the current run-scoped derived bundle outputs.
