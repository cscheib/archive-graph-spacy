# Feature Specification: Deprecate Superseded AI-Derived and Experimental Surfaces

**Feature Branch**: `008-deprecate-experimental-surfaces`
**Created**: 2026-03-12
**Status**: Accepted
**Input**: GitHub issue #14: Deprecate superseded AI-derived and experimental surfaces

**Implementation Readiness**: This spec is complete. Code changes must not
introduce new product-path conflicts or remove the `[EXPERIMENTAL]` markers
without confirming deterministic replacement coverage.

## Clarifications

### Session 2026-03-12

- Q: Which surfaces are "experimental" versus "supported"? → A: The `nlpdata`
  pipeline and its associated scripts (`build_nlpdata`, `build_edges`,
  `query_edges`) are the supported primary path. The local web app (`webapp`),
  raw export processing scripts (`run_export`, `run_sample`), and direct use of
  `extract`/`link`/`evaluate` modules outside the pipeline are experimental
  utilities retained for exploratory work only.
- Q: Should experimental modules be deleted or demoted? → A: Demoted and
  clearly marked `[EXPERIMENTAL]` for now. Removal happens only after
  deterministic replacement paths are confirmed and no active use is detected.
- Q: Where should the deprecation timeline live? → A: In this spec and the
  roadmap pointer in `docs/ROADMAP.md`. GitHub Project owns sequencing.

## Inventory of Experimental and Legacy Surfaces

### Experimental Utilities (Retained, Clearly Demoted)

| Surface | Module | Replacement Path | Notes |
|---------|--------|-----------------|-------|
| Local web app | `webapp.py`, `scripts/webapp.py` | `build_nlpdata` + downstream review UI in `archive-graph-data` | Retained for local exploration; not a product surface |
| Raw export pipeline | `scripts/run_export.py` | `scripts/build_nlpdata.py` | Superseded by the coordinated pipeline; kept for ad hoc debugging |
| Sample fixture runner | `scripts/run_sample.py` | `uv run pytest` + `build_nlpdata data_samples` | Kept as a developer smoke test helper only |
| Standalone summarizer | `evaluate/scoring.py` | Candidate assertions diagnostics in `nlpdata/pipeline.py` | Kept as a simple helper used by experimental scripts |

### Legacy AI-Derived Concepts (Superseded by Reviewed Assertions)

| Concept | Prior Location | Replacement |
|---------|---------------|------------|
| Unreviewed candidate links emitted directly | `scripts/run_export.py` output | `nlpdata` candidate assertions with reviewed-assertions lifecycle |
| Ad hoc mention→person link scoring | `evaluate/scoring.py` + `link/person.py` | `nlpdata/person_links.py` with provenance, bounded semantics, and assertions |
| Uncontrolled graph derivation | `scripts/build_edges.py` standalone | `build_nlpdata` pipeline (edges now derived inside the contract surface) |

### Supported Primary Surfaces

| Surface | Module | Notes |
|---------|--------|-------|
| `build_nlpdata` | `scripts/build_nlpdata.py`, `nlpdata/` | Primary derivation pipeline; contract-enforced; Databricks-publishable |
| `build_edges` | `scripts/build_edges.py` | Supported for local edge inspection alongside `build_nlpdata` |
| `query_edges` | `scripts/query_edges.py` | Supported DuckDB query helper for local derived tables |
| `visualize_ego` | `scripts/visualize_ego.py` | Supported local rendering for ego-network review |
| `visualize_graph` | `scripts/visualize_graph.py` | Supported local rendering for full person-network review |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Surface Classification Is Explicit in Docs (Priority: P1)

A maintainer reading the README and project layout should be able to determine
immediately which scripts and modules are part of the supported product path and
which are experimental or deprecated.

**Why this priority**: Without clear labeling, contributors treat experimental
scripts as production surfaces and add complexity that conflicts with the
reviewed-assertions and phase-oriented roadmap.

**Independent Test**: Read `README.md` and confirm it includes a section that
distinguishes supported, experimental, and planned-for-retirement surfaces
without ambiguity.

**Acceptance Scenarios**:

1. **Given** a new contributor reads only `README.md`, **When** they choose
   which script to run for a new bundle, **Then** they correctly identify
   `build_nlpdata` as the primary path and `run_export` / `webapp` as
   experimental.
2. **Given** a maintainer reads an experimental module, **When** they see the
   module docstring, **Then** they see an explicit `[EXPERIMENTAL]` marker and
   understand it is not a primary product surface.

---

### User Story 2 - Roadmap Explicitly Includes Retirement Phase (Priority: P2)

A roadmap reader should be able to find the planned retirement of superseded
surfaces and understand that removal is conditioned on deterministic replacement.

**Why this priority**: Without an explicit cleanup phase in the roadmap,
experimental surfaces accumulate indefinitely and confuse the long-term product
direction.

**Independent Test**: Read `docs/ROADMAP.md` and confirm it references the
deprecation plan and conditions retirement on confirmed replacement paths.

**Acceptance Scenarios**:

1. **Given** a planner reads `docs/ROADMAP.md`, **When** they look for the
   cleanup phase, **Then** they find a reference to surface retirement with a
   clear condition: removal only after replacement is confirmed.
2. **Given** a review is started for removing an experimental surface, **When**
   the reviewer checks the roadmap, **Then** they can confirm retirement is
   planned and not a surprise.

---

### Edge Cases

- If a downstream consumer depends on `run_export.py` output format, that
  consumer must be migrated to the `nlpdata` candidate assertions contract
  before `run_export.py` is removed.
- The `webapp` has active test coverage (`test_webapp.py`); tests must remain
  passing for as long as the module is retained.
- `evaluate/scoring.py` is currently imported by both `run_export.py` and
  `run_sample.py`; it cannot be removed until those callers are gone.

## Requirements

### Functional Requirements

1. `README.md` MUST include a "Surface Classification" section that explicitly
   labels each major script or module group as one of: `supported`, `experimental`,
   or `planned for retirement`.
2. All retained experimental module docstrings MUST include the text
   `[EXPERIMENTAL]` so that automated search or human review can find them.
3. `docs/ROADMAP.md` MUST include an explicit note that a cleanup phase for
   retiring superseded experimental surfaces is part of the roadmap, conditioned
   on confirmed deterministic replacement.
4. The README MUST NOT imply that `run_export`, `run_sample`, or `webapp` are
   equivalent production alternatives to `build_nlpdata`.

### Non-Functional Requirements

5. No existing automated tests may be removed or modified to accommodate this
   change.
6. No code behavior changes are required; only documentation and module-level
   markers are in scope.

## Out of Scope

- Actual code removal of any experimental surface (deferred to a later cleanup
  issue once replacement is confirmed).
- Migrating any downstream consumers off experimental surfaces (deferred).
- Adding new deprecation warnings at runtime (deferred until removal timeline is set).
