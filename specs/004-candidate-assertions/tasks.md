# Tasks: Candidate Assertions

**Input**: Design documents from `/specs/004-candidate-assertions/`
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/candidate-assertions-surface.md](contracts/candidate-assertions-surface.md)

**Tests**: Local automated test tasks are REQUIRED for every code change. Each
story and deployment candidate must identify the tests that prove the behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Pipeline implementation lives under `src/archive_graph_spacy/nlpdata/`
- CLI and payload exposure live under `src/archive_graph_spacy/scripts/`
- Tests live under `tests/`
- Planning and contract artifacts live under `specs/004-candidate-assertions/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Reconcile the generated plan artifacts with the current repo structure and candidate-generation scope

- [X] T001 Confirm active feature references and issue scope in `specs/004-candidate-assertions/spec.md`
- [X] T002 Review and reconcile implementation scope in `specs/004-candidate-assertions/plan.md`
- [X] T003 [P] Refine implementation decisions in `specs/004-candidate-assertions/research.md`
- [X] T004 [P] Refine the candidate data model in `specs/004-candidate-assertions/data-model.md`
- [X] T005 [P] Refine the candidate surface contract in `specs/004-candidate-assertions/contracts/candidate-assertions-surface.md`
- [X] T006 [P] Refine the validation walkthrough in `specs/004-candidate-assertions/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared candidate-assertion primitives and pipeline wiring that every story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Add candidate assertion dataclasses and diagnostics summary records in `src/archive_graph_spacy/nlpdata/models.py`
- [X] T008 [P] Extend payload contracts for persisted candidate outputs in `src/archive_graph_spacy/nlpdata/contracts.py`
- [X] T009 [P] Add deterministic candidate ID helpers and shared candidate-generation utilities in `src/archive_graph_spacy/nlpdata/person_links.py`
- [X] T010 Update pipeline result and payload assembly for candidate outputs in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T011 Update CLI result reporting for candidate outputs and diagnostics in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T012 Update agent context for the active candidate-generation implementation slice in `AGENTS.md`
- [X] T013 [P] Add or update candidate-generation fixture bundles in `data_samples/` for relay sender and ambiguous person-link coverage

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Emit Relay Sender Identity Candidates (Priority: P1) 🎯 MVP

**Goal**: Emit reviewable `relay_sender_identity` candidates from derived enrichment with deterministic payloads and required evidence fields

**Independent Test**: Run the pipeline on a fixture with relay-address sender cases and verify that persisted candidate output includes reviewable relay sender identity candidates with no canonical mutation

### Tests for User Story 1 ⚠️

- [X] T014 [P] [US1] Add relay sender identity candidate tests in `tests/test_nlpdata_candidate_assertions.py`
- [X] T015 [P] [US1] Extend pipeline payload assertions for candidate outputs in `tests/test_nlpdata_pipeline.py`

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement relay sender candidate record construction in `src/archive_graph_spacy/nlpdata/person_links.py`
- [X] T017 [P] [US1] Add relay sender candidate fields and validation examples in `specs/004-candidate-assertions/data-model.md`
- [X] T018 [US1] Add explicit relay sender minimum emission rules in `specs/004-candidate-assertions/spec.md`
- [X] T019 [US1] Carry relay sender candidates through `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T020 [US1] Write relay sender candidates to `candidate_assertions.jsonl` in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T021 [US1] Document relay sender candidate output guarantees in `specs/004-candidate-assertions/contracts/candidate-assertions-surface.md`
- [X] T022 [US1] Add quickstart validation steps for relay sender candidate generation in `specs/004-candidate-assertions/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Surface High-Value Disambiguation Candidates (Priority: P2)

**Goal**: Emit `person_link_disambiguation` candidates only for multi-candidate/no-clear-winner cases worth human review

**Independent Test**: Run the pipeline on fixtures with clear winners, multi-candidate ambiguities, and low-confidence single-candidate cases and verify that only the multi-candidate/no-clear-winner cases emit disambiguation candidates

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Add disambiguation candidate selection tests in `tests/test_nlpdata_candidate_assertions.py`
- [X] T024 [P] [US2] Add person-link ambiguity fixture coverage in `tests/test_nlpdata_links.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement multi-candidate/no-clear-winner selection logic in `src/archive_graph_spacy/nlpdata/person_links.py`
- [X] T026 [P] [US2] Add disambiguation candidate fields and validation rules in `specs/004-candidate-assertions/data-model.md`
- [X] T027 [US2] Carry disambiguation candidates through `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T028 [US2] Record the bounded disambiguation rules in `specs/004-candidate-assertions/research.md`
- [X] T029 [US2] Update the candidate surface contract for `person_link_disambiguation` outputs in `specs/004-candidate-assertions/contracts/candidate-assertions-surface.md`
- [X] T030 [US2] Add quickstart checks for clear-winner versus ambiguous disambiguation behavior in `specs/004-candidate-assertions/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Publish Reviewable Candidate Outputs (Priority: P3)

**Goal**: Publish persisted candidate outputs and a diagnostics summary that downstream reviewers can inspect without confusing candidates with reviewed or canonical states

**Independent Test**: Build derived outputs from a fixture bundle and verify that the persisted candidate surface and diagnostics summary expose at least five emitted candidates with required fields, counts, and suppression reasons

### Tests for User Story 3 ⚠️

- [X] T031 [P] [US3] Add CLI output and diagnostics summary tests in `tests/test_scripts_build_nlpdata.py`
- [X] T032 [P] [US3] Add persisted candidate output contract tests in `tests/test_nlpdata_candidate_assertions.py`

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement persisted candidate output writing to `candidate_assertions.jsonl` in `src/archive_graph_spacy/nlpdata/pipeline.py`
- [X] T034 [P] [US3] Implement human-readable diagnostics summary generation for `candidate_assertions_summary.json` in `src/archive_graph_spacy/scripts/build_nlpdata.py`
- [X] T035 [US3] Add candidate output table/contract validation in `src/archive_graph_spacy/nlpdata/contracts.py`
- [X] T036 [US3] Define the persisted output and diagnostics artifact fields in `specs/004-candidate-assertions/contracts/candidate-assertions-surface.md`
- [X] T037 [US3] Add output-surface validation steps and rerun checks in `specs/004-candidate-assertions/quickstart.md`
- [X] T038 [US3] Update `specs/004-candidate-assertions/plan.md` so the issue-closing and downstream-unblocking summary matches the final output surfaces

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation parity, and validation across the candidate-generation slice

- [X] T039 [P] Amend `docs/adr/003-reviewed-assertions-promotion-model.md` with the candidate-generation decisions and output boundary
- [X] T040 [P] Update `README.md` with candidate-generation usage and output references
- [X] T041 [P] Update `docs/ROADMAP.md` if the candidate-generation milestone wording changes
- [X] T042 Reconcile `AGENTS.md` with the final candidate-generation implementation language
- [X] T043 Run `uv run pytest` and record the validation command set in `specs/004-candidate-assertions/quickstart.md`
- [X] T044 Run the quickstart walkthrough in `specs/004-candidate-assertions/quickstart.md` and reconcile any drift in `specs/004-candidate-assertions/spec.md`
- [X] T045 Update `archive-graph-spacy#2` with the final artifact/code set and close it if the documented closure criteria are satisfied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1’s candidate models and pipeline wiring staying stable
- **User Story 3 (P3)**: Depends on User Story 1 and User Story 2 because the published output surface must include both first-wave candidate types

### Within Each User Story

- Tests before final story signoff
- Models and selection logic before payload publication
- Pipeline output changes before CLI/reporting validation
- Documentation and ADR updates before story completion

### Dependency Graph

- `US1 -> US2 -> US3`
- Polish depends on `US1`, `US2`, and `US3`

### Parallel Opportunities

- Setup tasks `T003` to `T006`
- Foundational tasks `T008`, `T009`, and `T013`
- US1 test tasks `T014` and `T015`, then implementation tasks `T016` and `T017`
- US2 test tasks `T023` and `T024`, then implementation tasks `T025` and `T026`
- US3 test tasks `T031` and `T032`, then implementation tasks `T033` and `T034`
- Polish tasks `T039` to `T041`

---

## Parallel Example: User Story 1

```bash
# Launch the US1 tests together:
Task: "Add relay sender identity candidate tests in tests/test_nlpdata_candidate_assertions.py"
Task: "Extend pipeline payload assertions for candidate outputs in tests/test_nlpdata_pipeline.py"

# Launch the core US1 implementation tasks together:
Task: "Implement relay sender candidate record construction in src/archive_graph_spacy/nlpdata/person_links.py"
Task: "Add relay sender candidate fields and validation examples in specs/004-candidate-assertions/data-model.md"
```

---

## Parallel Example: User Story 2

```bash
# Launch the US2 tests together:
Task: "Add disambiguation candidate selection tests in tests/test_nlpdata_candidate_assertions.py"
Task: "Add person-link ambiguity fixture coverage in tests/test_nlpdata_links.py"

# Launch the core US2 implementation tasks together:
Task: "Implement multi-candidate/no-clear-winner selection logic in src/archive_graph_spacy/nlpdata/person_links.py"
Task: "Add disambiguation candidate fields and validation rules in specs/004-candidate-assertions/data-model.md"
```

---

## Parallel Example: User Story 3

```bash
# Launch the US3 tests together:
Task: "Add CLI output and diagnostics summary tests in tests/test_scripts_build_nlpdata.py"
Task: "Add persisted candidate output contract tests in tests/test_nlpdata_candidate_assertions.py"

# Launch the core US3 implementation tasks together:
Task: "Implement persisted candidate output writing in src/archive_graph_spacy/nlpdata/pipeline.py"
Task: "Implement human-readable diagnostics summary generation in src/archive_graph_spacy/scripts/build_nlpdata.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate relay sender candidate outputs independently before expanding scope

### Incremental Delivery

1. Finish Setup + Foundational to establish shared candidate primitives
2. Add User Story 1 and validate relay sender candidates
3. Add User Story 2 and validate bounded disambiguation candidate generation
4. Add User Story 3 and validate persisted candidate outputs plus diagnostics
5. Finish with ADR/docs parity and full local test validation
