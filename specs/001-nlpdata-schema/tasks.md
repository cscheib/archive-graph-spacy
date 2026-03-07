# Tasks: NLP Search Workspace

**Input**: Design documents from `/Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Local automated test tasks are REQUIRED for every code change. Each
story and deployment candidate must identify the tests that prove the behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Implementation work for the `nlpdata` pipeline happens in this repository
  under `/Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/`
- `graph-data` is a read-only upstream source of canonical inputs
- Feature specs, quickstart, and ADR updates for this planning track live in
  `/Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/` and
  `/Users/chris/src/archive-graph-spacy/docs/adr/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the implementation scaffolding and architecture record

- [X] T001 Create the ADR skeleton in /Users/chris/src/archive-graph-spacy/docs/adr/001-nlpdata-search-workspace.md
- [X] T002 Create the nlpdata package scaffold in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/__init__.py
- [X] T003 [P] Create the shared pipeline test scaffold in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_pipeline.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema and refresh infrastructure that MUST exist before any
user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add local nlpdata table contracts in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/contracts.py
- [X] T005 [P] Define nlpdata entities and validation rules in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/models.py
- [X] T006 [P] Implement read-only source loading for canonical interactions, classifications, and overrides in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/source_loader.py
- [X] T007 Implement shared refresh orchestration and scope-replacement helpers in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/pipeline.py
- [X] T008 Wire the nlpdata build command into /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/scripts/build_nlpdata.py
- [X] T009 Add CLI coverage for the nlpdata build command in /Users/chris/src/archive-graph-spacy/tests/test_scripts_build_nlpdata.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Searchable Person Involvement (Priority: P1) 🎯 MVP

**Goal**: Produce person-message links and message-level search documents that
support person-centric retrieval without mutating source archive tables

**Independent Test**: Run a bounded refresh and verify that a chosen canonical
person returns both explicit-participant and inferred-mention interactions from
`personal_archive_dev.nlpdata` without manual joins to source tables

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation, and
> run them locally again before deployment**

- [X] T010 [P] [US1] Add person-link derivation unit tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_links.py
- [X] T011 [P] [US1] Add message-level search document integration tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_search_docs.py

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement message mention derivation in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/mentions.py
- [X] T013 [P] [US1] Implement canonical person-message link derivation with effective classification handling in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/person_links.py
- [X] T014 [US1] Implement person-oriented message search document projection in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/search_docs.py
- [X] T015 [US1] Wire message mentions, person links, and search document generation into /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/pipeline.py
- [X] T016 [US1] Add classification override, inclusion, and suppressed person-link coverage in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_links.py

**Checkpoint**: User Story 1 should now be fully functional and testable
independently

---

## Phase 4: User Story 2 - Searchable Conversation Themes (Priority: P2)

**Goal**: Add searchable message-level themes and support combined person+theme
retrieval

**Independent Test**: Run a bounded refresh over curated topical interactions
and verify that filtering by both person and theme returns only the expected
messages with reviewable evidence

### Tests for User Story 2 ⚠️

- [X] T017 [P] [US2] Add theme-tag derivation unit tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_themes.py
- [X] T018 [P] [US2] Add combined person-and-theme retrieval tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_search_docs.py

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement message-level theme tagging in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/themes.py
- [X] T020 [US2] Implement low-confidence theme suppression in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/themes.py
- [X] T021 [US2] Extend theme projection and filtered publication rules in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/search_docs.py
- [X] T022 [US2] Add suppressed theme-row coverage in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_search_docs.py

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Repeatable Refreshes And Auditability (Priority: P3)

**Goal**: Make refreshes traceable, rerunnable, and safe for bounded backfills
and corrections

**Independent Test**: Run the same bounded refresh twice and verify that
run-level metadata is recorded while current-state rows remain unique and free
of stale duplicates

### Tests for User Story 3 ⚠️

- [X] T023 [P] [US3] Add current-state replacement and rerun safety tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_runs.py
- [X] T024 [P] [US3] Add run-metadata and row-count tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_pipeline.py

### Implementation for User Story 3

- [X] T025 [P] [US3] Implement refresh run metadata recording in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/runs.py
- [X] T026 [US3] Implement bounded-scope stale-state cleanup and current-row replacement in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/pipeline.py
- [X] T027 [US3] Surface run_id, counts, and quality metrics from the build command in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/scripts/build_nlpdata.py
- [X] T028 [US3] Add bounded refresh timing validation for 10,000 interactions in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_pipeline.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, contract alignment, and final validation across all stories

- [X] T029 [P] Finalize the ADR rationale and alternatives in /Users/chris/src/archive-graph-spacy/docs/adr/001-nlpdata-search-workspace.md
- [X] T030 [P] Update the feature quickstart with exact local test commands in /Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/quickstart.md
- [X] T031 [P] Update contributor guidance in /Users/chris/src/archive-graph-spacy/README.md and /Users/chris/src/archive-graph-spacy/AGENTS.md
- [X] T032 Add system-generated and unresolved-derivation handling coverage in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_pipeline.py
- [X] T033 Run the nlpdata local test suites documented in /Users/chris/src/archive-graph-spacy/specs/001-nlpdata-schema/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 because theme output extends the message-level search document surface
- **User Story 3 (Phase 5)**: Depends on User Story 1 because rerun/audit behavior operates on the current-state `nlpdata` tables created there
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies after Foundational
- **User Story 2 (P2)**: Depends on US1 search documents and person-link outputs
- **User Story 3 (P3)**: Depends on US1 tables and refresh orchestration; can proceed in parallel with US2 after US1 is stable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Normalized derivation logic before denormalized search projection
- Table writes before validation queries
- Core implementation before documentation updates
- Story complete before the feature is considered deployable

### Parallel Opportunities

- T003 can run in parallel with T001-T002
- T005-T006 can run in parallel after T004 starts the contract work
- T010-T011 can run in parallel for US1
- T012-T013 can run in parallel for US1
- T017-T018 can run in parallel for US2
- T023-T024 can run in parallel for US3
- T029-T031 can run in parallel in the polish phase

---

## Parallel Example: User Story 1

```bash
# Launch all User Story 1 tests together:
Task: "Add person-link derivation unit tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_links.py"
Task: "Add message-level search document integration tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_search_docs.py"

# Launch the independent derivation modules together:
Task: "Implement message mention derivation in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/mentions.py"
Task: "Implement canonical person-message link derivation with effective classification handling in /Users/chris/src/archive-graph-spacy/src/archive_graph_spacy/nlpdata/person_links.py"
```

## Parallel Example: User Story 2

```bash
# Launch all User Story 2 tests together:
Task: "Add theme-tag derivation unit tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_themes.py"
Task: "Add combined person-and-theme retrieval tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_search_docs.py"
```

## Parallel Example: User Story 3

```bash
# Launch all User Story 3 tests together:
Task: "Add current-state replacement and rerun safety tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_runs.py"
Task: "Add run-metadata and row-count tests in /Users/chris/src/archive-graph-spacy/tests/test_nlpdata_pipeline.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm person-centric retrieval works from
   `personal_archive_dev.nlpdata`
5. Update docs and ADR, then review for deployment readiness

### Incremental Delivery

1. Complete Setup + Foundational → managed `nlpdata` contract and refresh path ready
2. Add User Story 1 → validate person-centric retrieval → deploy/demo
3. Add User Story 2 → validate theme-aware retrieval → deploy/demo
4. Add User Story 3 → validate rerun safety and auditability → deploy/demo
5. Finish polish tasks and final local test runs before release

### Parallel Team Strategy

With multiple developers:

1. Complete Setup + Foundational together
2. Developer A completes US1
3. After US1 stabilizes:
   - Developer B completes US2
   - Developer C completes US3
4. Merge story phases independently once their local tests pass

## Notes

- [P] tasks = different files, no dependencies
- [US1], [US2], [US3] labels map tasks directly to the user stories in spec.md
- Every story includes local automated tests because the constitution requires a
  local test gate before deployment
- The suggested MVP scope is Phase 3 (User Story 1) only
