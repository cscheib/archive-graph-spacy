# Tasks: nlpdata Publish Hardening

**Input**: Design documents from `/specs/005-nlpdata-publish-hardening/`
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/bounded-publish-semantics.md](contracts/bounded-publish-semantics.md)

**Tests**: Local automated test tasks are REQUIRED for every code change. Each
story and deployment candidate must identify the tests that prove the behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Deploy/publish logic lives under `src/archive_graph_spacy/nlpdata/`
- CLI result exposure lives under `src/archive_graph_spacy/scripts/`
- Tests live under `tests/`
- Planning and contract artifacts live under `specs/005-nlpdata-publish-hardening/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Reconcile the generated plan artifacts with the current repo structure and bounded publish scope

- [X] T001 Confirm active feature references and issue scope in `specs/005-nlpdata-publish-hardening/spec.md`
- [X] T002 Review and reconcile implementation scope in `specs/005-nlpdata-publish-hardening/plan.md`
- [X] T003 [P] Refine publish-model decisions in `specs/005-nlpdata-publish-hardening/research.md`
- [X] T004 [P] Refine the publish-state data model in `specs/005-nlpdata-publish-hardening/data-model.md`
- [X] T005 [P] Refine the bounded publish contract in `specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md`
- [X] T006 [P] Refine the validation walkthrough in `specs/005-nlpdata-publish-hardening/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared publish-state primitives and diagnostics scaffolding that every story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Add publish-state and recovery metadata records in `src/archive_graph_spacy/nlpdata/models.py`
- [X] T008 [P] Extend run metadata helpers for publish diagnostics in `src/archive_graph_spacy/nlpdata/runs.py`
- [X] T009 [P] Add shared bounded-scope and overlap helpers in `src/archive_graph_spacy/nlpdata/deploy.py`
- [X] T010 Update pipeline/build result plumbing for publish diagnostics in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T011 Update agent context for the active publish-hardening implementation slice in `AGENTS.md`
- [X] T012 [P] Create ADR 004 for bounded publish semantics in `docs/adr/004-nlpdata-publish-semantics.md`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Recover Safely After a Failed Bounded Publish (Priority: P1) 🎯 MVP

**Goal**: Make failed bounded publishes rerunnable without leaving affected current-state tables in mixed partial state

**Independent Test**: Simulate a bounded publish failure and rerun the same scope to verify one consistent final current-state view with no manual cleanup

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Add partial-failure and rerun-recovery tests in `tests/test_nlpdata_deploy.py`
- [X] T014 [P] [US1] Add publish-result assertions for recovery diagnostics in `tests/test_scripts_build_nlpdata.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement coordinated bounded-scope finalization in `src/archive_graph_spacy/nlpdata/deploy.py`
- [X] T016 [P] [US1] Add publish-state field definitions and examples in `specs/005-nlpdata-publish-hardening/data-model.md`
- [X] T017 [US1] Encode rerun-safe recovery rules in `specs/005-nlpdata-publish-hardening/spec.md`
- [X] T018 [US1] Add manual-intervention recovery cases to `tests/test_nlpdata_deploy.py`
- [X] T019 [US1] Surface publish outcome and recovery posture in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T020 [US1] Document coordinated finalization guarantees in `specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md`
- [X] T021 [US1] Add quickstart validation steps for failed bounded publish reruns in `specs/005-nlpdata-publish-hardening/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Publish Backfills With Clear Safety Rules (Priority: P2)

**Goal**: Define and enforce when bounded publishes may overlap and when they must serialize

**Independent Test**: Evaluate overlapping and non-overlapping bounded publish examples and verify that serialization rules are explicit and enforced

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Add overlap and serialization behavior tests in `tests/test_nlpdata_deploy.py`
- [X] T023 [P] [US2] Add bounded-scope coordination expectations in `tests/test_nlpdata_pipeline.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement overlap detection and serialization decisions in `src/archive_graph_spacy/nlpdata/deploy.py`
- [X] T025 [P] [US2] Add overlap-class fields and validation rules in `specs/005-nlpdata-publish-hardening/data-model.md`
- [X] T026 [US2] Record sequential versus parallel backfill rules in `specs/005-nlpdata-publish-hardening/research.md`
- [X] T027 [US2] Carry overlap-policy diagnostics through `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T028 [US2] Update the bounded publish contract for overlapping-scope behavior in `specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md`
- [X] T029 [US2] Add quickstart checks for overlapping versus non-overlapping bounded publishes in `specs/005-nlpdata-publish-hardening/quickstart.md`
- [X] T030 [US2] Add five representative publish classifications in `specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Diagnose Failed or Partial Publication Clearly (Priority: P3)

**Goal**: Expose run-level publish diagnostics that clearly distinguish staged, partial, failed, and finalized outcomes

**Independent Test**: Inspect publish diagnostics from representative success and failure cases and verify that operators can determine outcome and next recovery action without additional tribal knowledge

### Tests for User Story 3 ⚠️

- [X] T031 [P] [US3] Add publish-diagnostics record tests in `tests/test_nlpdata_deploy.py`
- [X] T032 [P] [US3] Add CLI diagnostics exposure tests in `tests/test_scripts_build_nlpdata.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Add publish-diagnostics record tests in `tests/test_nlpdata_deploy.py`
- [X] T032 [P] [US3] Add CLI diagnostics exposure tests in `tests/test_scripts_build_nlpdata.py`
- [X] T033 [P] [US3] Implement publish-stage and recovery diagnostics in `src/archive_graph_spacy/nlpdata/deploy.py`
- [X] T034 [P] [US3] Extend run metadata serialization for publish diagnostics in `src/archive_graph_spacy/nlpdata/runs.py`
- [X] T035 [US3] Expose publish diagnostics through `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T036 [US3] Define diagnostics record fields in `specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md`
- [X] T037 [US3] Add diagnostics validation steps and recovery examples in `specs/005-nlpdata-publish-hardening/quickstart.md`
- [X] T038 [US3] Update `specs/005-nlpdata-publish-hardening/plan.md` so the issue-closing and downstream-unblocking summary matches the final diagnostics surface
- [X] T039 [US3] Normalize publish outcome terminology across `specs/005-nlpdata-publish-hardening/spec.md`, `specs/005-nlpdata-publish-hardening/plan.md`, and `specs/005-nlpdata-publish-hardening/contracts/bounded-publish-semantics.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation parity, and validation across the publish-hardening slice

- [X] T040 [P] Update `README.md` with hardened publish semantics and recovery guidance
- [X] T041 [P] Update `docs/ROADMAP.md` if the publish-hardening milestone wording changes
- [X] T042 [P] Reconcile `AGENTS.md` with the final publish-hardening implementation language
- [X] T043 [P] Run `uv run pytest tests/test_nlpdata_deploy.py tests/test_nlpdata_pipeline.py tests/test_scripts_build_nlpdata.py` and record the command set in `specs/005-nlpdata-publish-hardening/quickstart.md`
- [X] T044 Run `uv run pytest` and record the full validation command in `specs/005-nlpdata-publish-hardening/quickstart.md`
- [X] T045 Run the quickstart walkthrough in `specs/005-nlpdata-publish-hardening/quickstart.md` and reconcile any drift in `specs/005-nlpdata-publish-hardening/spec.md`
- [X] T046 Update `archive-graph-spacy#3` with the final artifact/code set and close it if the documented closure criteria are satisfied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1’s bounded publish model and recovery semantics staying stable
- **User Story 3 (P3)**: Depends on User Story 1 and User Story 2 because diagnostics must describe the finalized publish/recovery model

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Shared publish-state structures before deploy-path behavior
- Deploy behavior before CLI/result exposure
- Documentation and ADR updates before the story is considered done
- Story complete before moving to next priority

### Dependency Graph

- `US1 -> US2 -> US3`
- Polish depends on `US1`, `US2`, and `US3`

### Parallel Opportunities

- Setup tasks `T003` to `T006`
- Foundational tasks `T008`, `T009`, and `T012`
- US1 test tasks `T013` and `T014`, then implementation tasks `T015` and `T016`
- US2 test tasks `T022` and `T023`, then implementation tasks `T024` and `T025`
- US3 test tasks `T031` and `T032`, then implementation tasks `T033` and `T034`
- Polish tasks `T040` to `T043`

---

## Parallel Example: User Story 1

```bash
# Launch the US1 tests together:
Task: "Add partial-failure and rerun-recovery tests in tests/test_nlpdata_deploy.py"
Task: "Add publish-result assertions for recovery diagnostics in tests/test_scripts_build_nlpdata.py"

# Launch the core US1 implementation tasks together:
Task: "Implement coordinated bounded-scope finalization in src/archive_graph_spacy/nlpdata/deploy.py"
Task: "Add publish-state field definitions and examples in specs/005-nlpdata-publish-hardening/data-model.md"
```

---

## Parallel Example: User Story 2

```bash
# Launch the US2 tests together:
Task: "Add overlap and serialization behavior tests in tests/test_nlpdata_deploy.py"
Task: "Add bounded-scope coordination expectations in tests/test_nlpdata_pipeline.py"

# Launch the core US2 implementation tasks together:
Task: "Implement overlap detection and serialization decisions in src/archive_graph_spacy/nlpdata/deploy.py"
Task: "Add overlap-class fields and validation rules in specs/005-nlpdata-publish-hardening/data-model.md"
```

---

## Parallel Example: User Story 3

```bash
# Launch the US3 tests together:
Task: "Add publish-diagnostics record tests in tests/test_nlpdata_deploy.py"
Task: "Add CLI diagnostics exposure tests in tests/test_scripts_build_nlpdata.py"

# Launch the core US3 implementation tasks together:
Task: "Implement publish-stage and recovery diagnostics in src/archive_graph_spacy/nlpdata/deploy.py"
Task: "Extend run metadata serialization for publish diagnostics in src/archive_graph_spacy/nlpdata/runs.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate failed bounded publish reruns independently before expanding scope

### Incremental Delivery

1. Finish Setup + Foundational to establish shared publish-state primitives
2. Add User Story 1 and validate rerun-safe bounded publish recovery
3. Add User Story 2 and validate overlap/serialization rules
4. Add User Story 3 and validate publish diagnostics and recovery posture
5. Finish with ADR/docs parity and full local test validation
