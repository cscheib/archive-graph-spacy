# Implementation Plan: Reviewed Assertions Pipeline

**Branch**: `003-reviewed-assertions-pipeline` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-reviewed-assertions-pipeline/spec.md`

**Related Issues**:
- Intended to close `archive-graph-spacy#4`
- Defines the review/promotion model needed before `archive-graph-spacy#2`
- Unblocks downstream workflow design for `archive-graph-data#70` and `archive-graph-data#71`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Define the reviewed-assertions feedback-loop model that sits between
`archive-graph-spacy` candidate assertion generation and
`archive-graph-data` canonical override workflows. The design names the initial
assertion types in scope, separates candidate assertions from accepted reviewed
assertions, requires explicit human promotion for any upstream canonical
override, and publishes the lifecycle, data model, and downstream integration
contract needed to close `archive-graph-spacy#4` and unblock the issues that
depend on it.

## Technical Context

**Language/Version**: Markdown-first planning artifacts for a Python 3.12 repository  
**Primary Dependencies**: Existing repo docs/spec workflow, cross-repo boundary contract, pytest, `uv`, GitHub issues/projects  
**Storage**: Markdown specs under `specs/`; ADRs under `docs/adr/`  
**Testing**: Spec quality checklist review; future implementation must use `uv run pytest` for affected behavior  
**Target Platform**: Local repository workflow for `archive-graph-spacy` plus linked planning and implementation work across GitHub repos  
**Project Type**: Cross-repository workflow and data-model contract artifact set  
**Performance Goals**: Maintainers should classify at least five representative assertions and at least three review/promotion handoffs consistently using the model alone; downstream teams should identify promotion boundaries without contradictory interpretations  
**Constraints**: Keep the design minimal; no implementation-specific table or API design; initial scope is limited to relay sender identity and ambiguous person-link/disambiguation assertions; acceptance creates durable reviewed records first; promotion requires a separate explicit human action; reviewed assertions and promoted overrides remain owned by `archive-graph-data`; documentation and ADR references must stay in sync  
**Scale/Scope**: Covers the first-wave reviewed-assertions lifecycle, review decision states, provenance minimums, promotion eligibility, and UI/override integration boundaries needed to close `archive-graph-spacy#4` and unblock `archive-graph-spacy#2`, `archive-graph-data#70`, and `archive-graph-data#71`

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
  `PASS` (`docs/adr/003-reviewed-assertions-promotion-model.md`)

**Post-Design Re-Check**: `PASS`. Phase 0 research and Phase 1 design stayed
within the documented scope, reused the existing cross-repo boundary contract,
kept the new artifacts technology-agnostic, and preserved the ADR requirement
for the reviewed-assertions lifecycle boundary.

## Project Structure

### Documentation (this feature)

```text
specs/003-reviewed-assertions-pipeline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── reviewed-assertions-lifecycle.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
├── ROADMAP.md
└── adr/
   ├── 001-nlpdata-search-workspace.md
   ├── 002-cross-repo-contract.md
   └── 003-reviewed-assertions-promotion-model.md  # planned output of this feature

specs/
├── 001-nlpdata-schema/
├── 002-formalize-cross-repo-contract/
└── 003-reviewed-assertions-pipeline/

src/archive_graph_spacy/
├── nlpdata/
├── link/
├── evaluate/
└── scripts/

tests/
├── test_nlpdata_*.py
├── test_link_person.py
└── test_scripts_*.py
```

**Structure Decision**: This feature is documentation-first and architecture
first. The immediate deliverables live under
`specs/003-reviewed-assertions-pipeline/`, and this slice also authors ADR 003
under `docs/adr/`. Future code work remains in existing Python modules and
downstream UI systems. The lifecycle contract is published in this repository
because this repo already owns candidate assertion generation and the
authoritative cross-repo planning boundary.

## Complexity Tracking

No constitution violations are currently required. The plan intentionally
avoids table-level, API-level, or UI-implementation detail beyond the minimum
reviewed-assertions lifecycle and promotion boundary needed for the current
roadmap issues.
