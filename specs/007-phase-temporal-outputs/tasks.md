# Tasks: Phase and Temporal Outputs

**Input**: Design documents from `/specs/007-phase-temporal-outputs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Local automated test tasks are REQUIRED for every code change. Each
story below includes the focused tests that must fail before implementation and
pass again before the story is complete.

**Organization**: Tasks are grouped by user story so each slice can be
implemented and validated independently where the spec allows. This feature has
an intentional dependency chain: US2 depends on US1, and US3 depends on US1
plus US2.

## Phase 1: Setup (Shared Fixtures and Inputs)

**Purpose**: Create the bounded fixture and source inputs the rest of the
implementation depends on.

- [X] T001 Create the Phase 4 sample bundle with `contacts.jsonl` and `messages.jsonl` source inputs in `data_samples/phase_temporal_outputs/`
- [X] T002 [P] Add bounded multi-period fixture coverage notes in `specs/007-phase-temporal-outputs/quickstart.md`
- [X] T003 [P] Add phase-oriented sample expectations in `specs/007-phase-temporal-outputs/contracts/phase-output-contracts.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend shared contracts, models, and pipeline hooks before any
user story implementation begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Extend Phase 4 typed records in `src/archive_graph_spacy/nlpdata/models.py`
- [X] T005 [P] Extend published table contracts in `src/archive_graph_spacy/nlpdata/contracts.py`
- [X] T006 [P] Extend Spark view definitions in `src/archive_graph_spacy/nlpdata/spark_views.py`
- [X] T007 Add phase-oriented run diagnostics helpers in `src/archive_graph_spacy/nlpdata/runs.py`
- [X] T008 Add source-loader hooks for the Phase 4 fixture and reused Phase 3 relationship inputs from `person_person_edges` in `src/archive_graph_spacy/nlpdata/source_loader.py`

**Checkpoint**: Shared fixture, contract, and diagnostics scaffolding exists
for phase rows, child tables, and bounded diagnostics.

---

## Phase 3: User Story 1 - Publish First-Class Phase Outputs (Priority: P1) 🎯 MVP

**Goal**: Derive first-class owner-centric phase rows with deterministic ids,
time bounds, ordering, and representative interaction references.

**Independent Test**: Run `build_nlpdata` on the Phase 4 fixture bundle and
verify that the emitted phase tables support phase list/detail exploration with
stable ids, time bounds, and provenance-bearing representative interactions.

### Tests for User Story 1 ⚠️

- [X] T009 [P] [US1] Add phase segmentation and determinism tests in `tests/test_phase_outputs.py`
- [X] T010 [P] [US1] Add phase pipeline integration tests in `tests/test_nlpdata_pipeline.py`
- [X] T011 [P] [US1] Add script-level phase artifact tests in `tests/test_scripts_build_nlpdata.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement deterministic time-gap segmentation and merge rules in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T013 [US1] Implement first-class `phases` records and representative interaction selection in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T014 [US1] Surface phase rows and representative interactions in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T015 [US1] Extend Databricks deploy and schema support for `phases` outputs in `src/archive_graph_spacy/nlpdata/deploy.py`
- [X] T016 [US1] Add Databricks/view coverage for phase outputs in `tests/test_nlpdata_databricks.py` and `tests/test_nlpdata_deploy.py`

**Checkpoint**: `build_nlpdata` publishes stable first-class phase rows and
representative interactions for the bounded fixture.

---

## Phase 4: User Story 2 - Publish Temporal Relationship and Centrality Outputs (Priority: P2)

**Goal**: Publish central people, dominant themes, and phase-bounded pair
outputs so phase detail flows can be supported from `nlpdata` only.

**Independent Test**: Build `nlpdata` for the bounded fixture and verify that
each phase can be joined to central people, dominant themes, temporal pair
summaries, and temporal pair evidence using published Phase 4 artifacts only.

### Tests for User Story 2 ⚠️

- [X] T017 [P] [US2] Add central-people and dominant-theme tests in `tests/test_phase_outputs.py`
- [X] T018 [P] [US2] Add temporal pair output tests in `tests/test_nlpdata_pipeline.py`
- [X] T019 [P] [US2] Add end-to-end artifact tests for phase child tables in `tests/test_scripts_build_nlpdata.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `phase_central_people` and `phase_theme_summaries` aggregation in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T021 [US2] Implement `phase_pair_summaries` and bounded `phase_pair_evidence` derivation in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T022 [US2] Extend Phase 4 publish contracts for child tables in `src/archive_graph_spacy/nlpdata/contracts.py`
- [X] T023 [US2] Extend Databricks deploy and view support for phase child tables in `src/archive_graph_spacy/nlpdata/deploy.py` and `src/archive_graph_spacy/nlpdata/spark_views.py`
- [X] T024 [US2] Surface child-table counts and summaries in `src/archive_graph_spacy/scripts/build_nlpdata.py`

**Checkpoint**: Downstream consumers can read phase-level people, themes, and
temporal pair outputs directly from the published Phase 4 contract.

---

## Phase 5: User Story 3 - Publish Phase Diagnostics and Boundary Explanations (Priority: P3)

**Goal**: Publish bounded diagnostics that explain phase boundaries,
suppression, and aggregate claims without polluting the main contract.

**Independent Test**: Run the phase derivation flow on the bounded fixture and
verify that diagnostics expose segmentation inputs, representative evidence,
suppression behavior, and deterministic ordering for unchanged inputs.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Add phase suppression and boundary-decision tests in `tests/test_phase_outputs.py`
- [X] T026 [P] [US3] Add phase diagnostics result-category tests in `tests/test_nlpdata_runs.py`
- [X] T027 [P] [US3] Add bounded diagnostics and evidence-cap tests in `tests/test_scripts_build_nlpdata.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement phase boundary decision and suppression diagnostics in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T029 [US3] Implement phase diagnostics record aggregation in `src/archive_graph_spacy/nlpdata/runs.py`
- [X] T030 [US3] Persist `phase_diagnostics` and suppressed-phase summaries in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T031 [US3] Surface diagnostics and suppression summaries in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T032 [US3] Extend deploy/view support for diagnostics outputs in `src/archive_graph_spacy/nlpdata/deploy.py` and `src/archive_graph_spacy/nlpdata/spark_views.py`
- [X] T033 [US3] Assert deterministic caps for representative interactions, temporal pair evidence, and diagnostics in `tests/test_phase_outputs.py`

**Checkpoint**: Weak phases are suppressed from published phase rows and remain
explainable through bounded diagnostics and representative evidence.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align ADRs, docs, and final validation across all three stories.

- [X] T034 [P] Create the Phase 4 contract ADR in `docs/adr/006-phase-output-contract.md`
- [X] T035 [P] Amend Phase 4 roadmap boundary details in `docs/adr/005-phase-first-class-object.md`
- [X] T036 [P] Update Phase 4 behavior and usage notes in `README.md`
- [X] T037 Run the focused Phase 4 suite in `tests/test_phase_outputs.py`, `tests/test_nlpdata_pipeline.py`, `tests/test_nlpdata_runs.py`, `tests/test_nlpdata_deploy.py`, `tests/test_nlpdata_databricks.py`, and `tests/test_scripts_build_nlpdata.py`
- [X] T038 Run the full local regression suite with `uv run pytest` from `/Users/chris/src/archive-graph-spacy`
- [X] T039 Run the quickstart validation documented in `specs/007-phase-temporal-outputs/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; starts immediately
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational; this is the MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 because phase child
  tables require stable first-class phase rows
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because
  diagnostics explain published phases and their aggregates
- **Polish (Phase 6)**: Depends on all selected user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational completion
- **User Story 2 (P2)**: Starts after User Story 1 is functionally complete
- **User Story 3 (P3)**: Starts after User Story 2 is functionally complete

### Within Each User Story

- Tests must be written and fail before implementation
- Shared models/contracts from Phase 2 must exist before story code changes
- Pipeline integration comes after story-specific tests
- CLI/export surfacing comes after pipeline behavior exists
- Story-specific validation must pass before the next dependent story begins

### Parallel Opportunities

- Setup tasks `T002` and `T003`
- Foundational tasks `T005` and `T006`
- US1 tests `T009` through `T011`
- US2 tests `T017` through `T019`
- US3 tests `T025` through `T027`
- Polish docs tasks `T034` through `T036`

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests together
Task: "Add phase segmentation and determinism tests in tests/test_phase_outputs.py"
Task: "Add phase pipeline integration tests in tests/test_nlpdata_pipeline.py"
Task: "Add script-level phase artifact tests in tests/test_scripts_build_nlpdata.py"
```

## Parallel Example: User Story 2

```bash
# Launch US2 tests together
Task: "Add central-people and dominant-theme tests in tests/test_phase_outputs.py"
Task: "Add temporal pair output tests in tests/test_nlpdata_pipeline.py"
Task: "Add end-to-end artifact tests for phase child tables in tests/test_scripts_build_nlpdata.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 tests together
Task: "Add phase suppression and boundary-decision tests in tests/test_phase_outputs.py"
Task: "Add phase diagnostics result-category tests in tests/test_nlpdata_runs.py"
Task: "Add bounded diagnostics and evidence-cap tests in tests/test_scripts_build_nlpdata.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate phase-row derivation and determinism end to end

### Incremental Delivery

1. Finish Setup + Foundational
2. Deliver User Story 1 and validate phase-object semantics
3. Deliver User Story 2 and validate phase child-table contracts
4. Deliver User Story 3 and validate diagnostics and suppression behavior
5. Finish ADR, README, quickstart, and full test validation

### Parallel Team Strategy

1. One contributor handles Setup + Foundational
2. After Foundational:
   - Contributor A: US1 implementation
3. After US1:
   - Contributor A or B: US2 implementation
4. After US2:
   - Contributor A or B: US3 implementation

---

## Notes

- All tasks use exact repository paths
- The task chain is intentionally sequential across stories because the spec
  defines a Phase 4 dependency chain
- `[P]` means tasks can run in parallel because they touch different files and
  do not depend on unfinished prior tasks
- `tasks.md` is written so an implementation agent can execute it directly
