# Tasks: Feedback Consumption and Relationship Outputs

**Input**: Design documents from `/specs/006-feedback-relationship-outputs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Local automated test tasks are REQUIRED for every code change. Each
story below includes the focused tests that must fail before implementation and
pass again before the story is complete.

**Organization**: Tasks are grouped by user story so each slice can be
implemented and validated independently where the spec allows. This feature has
an intentional dependency chain: US2 depends on US1, and US3 depends on US1
plus the pairwise outputs from US2.

## Phase 1: Setup (Shared Fixtures and Inputs)

**Purpose**: Create the bounded fixture and reviewed-input material the rest of
the implementation depends on.

- [X] T001 Create the Phase 3 sample bundle with `contacts.jsonl` and `messages.jsonl` source inputs in `data_samples/feedback_relationship_outputs/`
- [X] T002 [P] Add reviewed assertion fixture rows in `data_samples/feedback_relationship_outputs/reviewed_assertions.jsonl`
- [X] T003 [P] Add reviewed decision fixture rows in `data_samples/feedback_relationship_outputs/review_assertion_decisions.jsonl`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the shared pipeline contracts, models, and diagnostics
surfaces before any user story implementation begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Extend Phase 3 typed records in `src/archive_graph_spacy/nlpdata/models.py`
- [X] T005 [P] Extend published table contracts in `src/archive_graph_spacy/nlpdata/contracts.py`
- [X] T006 [P] Extend Spark view definitions in `src/archive_graph_spacy/nlpdata/spark_views.py`
- [X] T007 Add reviewed-effect result categories and run diagnostics helpers in `src/archive_graph_spacy/nlpdata/runs.py`
- [X] T008 Add reviewed-input loading hooks in `src/archive_graph_spacy/nlpdata/source_loader.py`

**Checkpoint**: Shared fixture, contract, and diagnostics scaffolding exists for
reviewed feedback, pair outputs, and expanded candidate families.

---

## Phase 3: User Story 1 - Consume Reviewed Feedback During Derivation (Priority: P1) 🎯 MVP

**Goal**: Make `build_nlpdata` consume reviewed outcomes read-only from
`graph-data`, replay them deterministically across reruns, and emit explicit
reviewed-effect diagnostics.

**Independent Test**: Run `build_nlpdata` on the Phase 3 fixture bundle and
verify that accepted reviewed outcomes apply downstream effects, rejected or
resolved outcomes suppress re-emission, and conflicts are surfaced as
`conflicted` instead of being auto-applied.

### Tests for User Story 1 ⚠️

- [X] T009 [P] [US1] Add reviewed-feedback replay tests in `tests/test_nlpdata_pipeline.py`
- [X] T010 [P] [US1] Add reviewed-input source-loading tests in `tests/test_nlpdata_source_loader.py`
- [X] T011 [P] [US1] Add run-diagnostics result-category tests in `tests/test_nlpdata_runs.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement reviewed-input boundary loading in `src/archive_graph_spacy/nlpdata/source_loader.py`
- [X] T013 [US1] Implement replay key normalization and reviewed-effect application in `src/archive_graph_spacy/nlpdata/person_links.py`
- [X] T014 [US1] Integrate reviewed-feedback consumption into `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T015 [US1] Surface reviewed-effect diagnostics and read-boundary metadata in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T016 [US1] Extend Databricks source-loading coverage for reviewed inputs in `tests/test_nlpdata_databricks.py`

**Checkpoint**: `build_nlpdata` replays reviewed outcomes deterministically and
produces stable reviewed-effect diagnostics for the bounded fixture.

---

## Phase 4: User Story 2 - Publish Durable Relationship Outputs From nlpdata (Priority: P2)

**Goal**: Publish one canonical summary row per pair plus bounded supporting
evidence so downstream code can consume pairwise relationship outputs directly
from `nlpdata`.

**Independent Test**: Run the Phase 3 fixture through `build_nlpdata` and
verify that `person_person_edges` and `person_person_edge_evidence` are both
emitted with deterministic pair identity, bounded evidence, and usable summary
fields for downstream consumers.

### Tests for User Story 2 ⚠️

- [X] T017 [P] [US2] Add canonical pair aggregation tests in `tests/test_person_person_edges.py`
- [X] T018 [P] [US2] Add end-to-end pair output artifact tests in `tests/test_scripts_build_nlpdata.py`
- [X] T019 [P] [US2] Add deploy and schema coverage for pair outputs in `tests/test_nlpdata_deploy.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement canonical pair summary aggregation in `src/archive_graph_spacy/edges/person_person.py`
- [X] T021 [US2] Persist `person_person_edges` and `person_person_edge_evidence` in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T022 [US2] Extend publish contracts for pair outputs in `src/archive_graph_spacy/nlpdata/contracts.py`
- [X] T023 [US2] Extend Databricks deploy and view support for pair outputs in `src/archive_graph_spacy/nlpdata/deploy.py` and `src/archive_graph_spacy/nlpdata/spark_views.py`
- [X] T024 [US2] Surface pair-output diagnostics in `src/archive_graph_spacy/scripts/build_nlpdata.py`

**Checkpoint**: Downstream consumers can read deterministic pair summaries and
bounded evidence directly from published Phase 3 outputs.

---

## Phase 5: User Story 3 - Expand the Candidate Assertion Framework for Additional Families (Priority: P3)

**Goal**: Add `relationship_evidence_review` as the first new candidate family
without creating a separate review pipeline or violating the `derived_only`
boundary.

**Independent Test**: Run the Phase 3 fixture through candidate generation and
verify that `relationship_evidence_review` uses the shared candidate schema,
replay rules, diagnostics, and reviewed-effect handling while remaining
`derived_only`.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Add `relationship_evidence_review` candidate tests in `tests/test_nlpdata_candidate_assertions.py`
- [X] T026 [P] [US3] Add family-level diagnostics tests in `tests/test_nlpdata_pipeline.py`
- [X] T027 [P] [US3] Add build-output summary tests for the new family in `tests/test_scripts_build_nlpdata.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `relationship_evidence_review` emission and `derived_only` rules in `src/archive_graph_spacy/nlpdata/person_links.py`
- [X] T029 [US3] Integrate family-level reviewed-effect summaries in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T030 [US3] Extend candidate summary and export output for the new family in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T031 [US3] Extend candidate-family contracts and views in `src/archive_graph_spacy/nlpdata/contracts.py` and `src/archive_graph_spacy/nlpdata/spark_views.py`
- [X] T032 [US3] Assert bounded evidence and diagnostics caps for the Phase 3 fixture in `tests/test_scripts_build_nlpdata.py`

**Checkpoint**: A third candidate family exists inside the same reviewed
lifecycle, with no separate queue or promotion semantics.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align decision records, docs, and final validation across all
three stories.

- [X] T033 [P] Amend reviewed-lifecycle ADR details in `docs/adr/003-reviewed-assertions-promotion-model.md`
- [X] T034 [P] Amend Phase 3 and Phase 4 boundary details in `docs/adr/005-phase-first-class-object.md`
- [X] T035 [P] Update behavior and usage notes in `README.md`
- [X] T036 Run the focused Phase 3 suite in `tests/test_nlpdata_candidate_assertions.py`, `tests/test_nlpdata_pipeline.py`, `tests/test_nlpdata_source_loader.py`, `tests/test_nlpdata_runs.py`, `tests/test_person_person_edges.py`, `tests/test_nlpdata_deploy.py`, `tests/test_nlpdata_databricks.py`, and `tests/test_scripts_build_nlpdata.py`
- [X] T037 Run the full local regression suite with `uv run pytest` from `/Users/chris/src/archive-graph-spacy`
- [X] T038 Run the quickstart validation documented in `specs/006-feedback-relationship-outputs/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; starts immediately
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational; this is the MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 because reviewed-feedback
  consumption is part of the Phase 3 contract boundary
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because
  the first new family is pair-scoped and reuses published pairwise outputs
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
- Polish docs tasks `T033` through `T035`

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests together
Task: "Add reviewed-feedback replay tests in tests/test_nlpdata_pipeline.py"
Task: "Add reviewed-input source-loading tests in tests/test_nlpdata_source_loader.py"
Task: "Add run-diagnostics result-category tests in tests/test_nlpdata_runs.py"
```

## Parallel Example: User Story 2

```bash
# Launch US2 tests together
Task: "Add canonical pair aggregation tests in tests/test_person_person_edges.py"
Task: "Add end-to-end pair output artifact tests in tests/test_scripts_build_nlpdata.py"
Task: "Add deploy and schema coverage for pair outputs in tests/test_nlpdata_deploy.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 tests together
Task: "Add relationship_evidence_review candidate tests in tests/test_nlpdata_candidate_assertions.py"
Task: "Add family-level diagnostics tests in tests/test_nlpdata_pipeline.py"
Task: "Add build-output summary tests for the new family in tests/test_scripts_build_nlpdata.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate reviewed-feedback replay and diagnostics end to end

### Incremental Delivery

1. Finish Setup + Foundational
2. Deliver User Story 1 and validate replay semantics
3. Deliver User Story 2 and validate pair output contracts
4. Deliver User Story 3 and validate the expanded candidate family
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
  defines a Phase 3 dependency chain
- `[P]` means tasks can run in parallel because they touch different files and
  do not depend on unfinished prior tasks
- `tasks.md` is written so an implementation agent can execute it directly
