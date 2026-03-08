# Implementation Plan: Cross-Repo Contract

**Branch**: `002-formalize-cross-repo-contract` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-formalize-cross-repo-contract/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Define one shared contract that separates canonical source-of-truth records,
derived enrichment, candidate assertions, reviewed assertions, and promoted
overrides across `archive-graph-data` and `archive-graph-spacy`. The design
keeps canonical records and all post-review curation state in
`archive-graph-data`, keeps derived enrichment and candidate assertion
generation in `archive-graph-spacy`, requires immutable canonical IDs for
cross-repo joins, and captures these guarantees in a contract artifact, data
model, quickstart, and ADR linkage.

## Technical Context

**Language/Version**: Markdown-first planning artifacts for a Python 3.12 repository  
**Primary Dependencies**: Existing repo docs/spec workflow, pytest, `uv`, GitHub issues/projects  
**Storage**: Markdown specs under `specs/`; ADRs under `docs/adr/`  
**Testing**: Spec quality checklist review; future implementation must use `uv run pytest` for affected behavior  
**Target Platform**: Local repository workflow for `archive-graph-spacy` plus linked planning and implementation work across GitHub repos  
**Project Type**: Cross-repository architecture contract and planning artifact set  
**Performance Goals**: Enable blocked roadmap issues to reference one shared contract without redefining ownership or join semantics; maintainers should classify at least five representative flows and five assertion examples consistently using the contract alone  
**Constraints**: Keep the design minimal; no implementation-specific storage or API design in the contract; candidate assertions originate in `archive-graph-spacy`; reviewed assertions and promoted overrides live in `archive-graph-data`; cross-repo joins use immutable canonical IDs only; documentation and ADR references must stay in sync  
**Scale/Scope**: Covers the initial roadmap boundary for canonical records, derived enrichment, candidate assertions, reviewed assertions, promotion rules, provenance, confidence semantics, and interface guarantees needed by currently blocked roadmap issues

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
  `PASS` (`docs/adr/002-cross-repo-contract.md`)

**Post-Design Re-Check**: `PASS`. Phase 0 research and Phase 1 design stayed
within the documented scope, kept the contract technology-agnostic, preserved
documentation parity across plan artifacts, and maintained the ADR requirement
for the architectural boundary.

## Project Structure

### Documentation (this feature)

```text
specs/002-formalize-cross-repo-contract/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cross-repo-boundary.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
├── ROADMAP.md
└── adr/
   ├── 001-nlpdata-search-workspace.md
   └── 002-cross-repo-contract.md

src/archive_graph_spacy/
├── extract/
├── link/
├── evaluate/
├── nlpdata/
└── scripts/

tests/
├── test_nlpdata_*.py
├── test_link_person.py
└── test_scripts_*.py
```

**Structure Decision**: This feature is documentation-first and architecture
first. The source implementation remains split between existing Python modules
and later cross-repo work, while the immediate deliverables live under
`specs/002-formalize-cross-repo-contract/` and `docs/adr/`. The contract
itself is authored in this repository because it already owns the planning
entry point and the derived-work boundary.

## Complexity Tracking

No constitution violations are currently required. The plan intentionally
avoids specifying repository-internal APIs, storage schemas, or workflow
mechanics beyond the minimum contract needed to unblock reviewed assertions and
dependent roadmap items.
