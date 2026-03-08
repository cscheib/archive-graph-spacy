# Tasks: Reviewed Assertions Pipeline

**Input**: Design documents from `/specs/003-reviewed-assertions-pipeline/`
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/reviewed-assertions-lifecycle.md](contracts/reviewed-assertions-lifecycle.md)

**Tests**: Local automated test tasks are REQUIRED for every code change. This feature is documentation-first, so local validation includes `uv run pytest` plus quickstart/contract review checks for every story completion.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Documentation-first planning artifacts live under `specs/003-reviewed-assertions-pipeline/`
- Decision records live under `docs/adr/`
- Repo guidance updates live in `README.md`, `docs/ROADMAP.md`, and `AGENTS.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the feature artifact set and verify the planning baseline

- [X] T001 Confirm active feature paths and branch references in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T002 Review and reconcile implementation scope in `specs/003-reviewed-assertions-pipeline/plan.md`
- [X] T003 [P] Refine the research decisions in `specs/003-reviewed-assertions-pipeline/research.md`
- [X] T004 [P] Refine the data model in `specs/003-reviewed-assertions-pipeline/data-model.md`
- [X] T005 [P] Refine the lifecycle contract in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`
- [X] T006 [P] Refine the validation walkthrough in `specs/003-reviewed-assertions-pipeline/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared boundaries and issue-closing scope that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Align `specs/003-reviewed-assertions-pipeline/plan.md` with `specs/002-formalize-cross-repo-contract/plan.md` and `docs/adr/002-cross-repo-contract.md`
- [X] T008 [P] Record the first-wave assertion-type decisions in `specs/003-reviewed-assertions-pipeline/research.md`
- [X] T009 [P] Add explicit issue linkage for `archive-graph-spacy#4`, `archive-graph-spacy#2`, `archive-graph-data#70`, and `archive-graph-data#71` in `specs/003-reviewed-assertions-pipeline/plan.md`
- [X] T010 Add the reviewed-storage ownership rule and explicit human-promotion rule in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T011 Update agent context for this planning slice in `AGENTS.md`

**Checkpoint**: Foundation ready - user story planning work can now proceed in parallel

---

## Phase 3: User Story 1 - Define Reviewable Assertion Records (Priority: P1) 🎯 MVP

**Goal**: Define the core reviewed-assertions entities and first-wave assertion types clearly enough to close the model gap in `archive-graph-spacy#4`

**Independent Test**: Reviewers can use the artifacts alone to classify five representative examples as candidate, review decision, accepted assertion, or canonical override without inventing extra states

### Tests for User Story 1 ⚠️

> **NOTE: Validate the artifact set before considering this story done**

- [X] T012 [P] [US1] Verify the representative state-classification examples in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T013 [P] [US1] Verify the lifecycle examples in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`

### Implementation for User Story 1

- [X] T014 [P] [US1] Define candidate assertion fields and validation rules in `specs/003-reviewed-assertions-pipeline/data-model.md`
- [X] T015 [P] [US1] Define review decision, accepted assertion, promotion rule, and promotion outcome entities in `specs/003-reviewed-assertions-pipeline/data-model.md`
- [X] T016 [US1] Add the first-wave assertion-type scope and lifecycle requirements in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T017 [US1] Add the explicit assertion-type classification table in `specs/003-reviewed-assertions-pipeline/data-model.md`
- [X] T018 [US1] Capture the candidate-to-reviewed lifecycle narrative in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`
- [X] T019 [US1] Add quickstart validation steps for state classification in `specs/003-reviewed-assertions-pipeline/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Define Review Decisions And Promotion Rules (Priority: P2)

**Goal**: Make acceptance, review, and promotion boundaries explicit so only eligible accepted assertions can become canonical overrides

**Independent Test**: Reviewers can take five representative assertions and consistently determine whether each is rejected, accepted-but-derived-only, or promotion-eligible using the spec and contract alone

### Tests for User Story 2 ⚠️

- [X] T020 [P] [US2] Verify promotion-eligibility examples in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T021 [P] [US2] Verify promotion guardrails and examples in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`

### Implementation for User Story 2

- [X] T022 [P] [US2] Record the acceptance-versus-promotion research decisions in `specs/003-reviewed-assertions-pipeline/research.md`
- [X] T023 [P] [US2] Define promotion-rule fields and validation rules in `specs/003-reviewed-assertions-pipeline/data-model.md`
- [X] T024 [US2] Add the acceptance, promotion, and ownership requirements in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T025 [US2] Add the promotion rules, explicit human-action rule, and assertion-type promotion classes in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`
- [X] T026 [US2] Add quickstart validation steps for acceptance-versus-promotion boundary checks in `specs/003-reviewed-assertions-pipeline/quickstart.md`
- [X] T027 [US2] Draft the ADR decision summary and related issue intent in `specs/003-reviewed-assertions-pipeline/plan.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Define Downstream Integration Boundaries (Priority: P3)

**Goal**: Define the minimum downstream inputs, outputs, and ownership boundaries that `archive-graph-data` review UI and override workflows require

**Independent Test**: A downstream maintainer can map at least three interactions, candidate display, review decision capture, and promotion handoff, to the documented contract without inventing local boundary rules

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Verify downstream integration interactions in `specs/003-reviewed-assertions-pipeline/quickstart.md`
- [X] T029 [P] [US3] Verify UI and override integration points in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`

### Implementation for User Story 3

- [X] T030 [P] [US3] Define the exact candidate-handoff, review-decision-capture, and promotion-handoff fields in `specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md`
- [X] T031 [P] [US3] Add explicit downstream payload-field requirements in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T032 [US3] Add integration-boundary rationale and issue-unblocking notes in `specs/003-reviewed-assertions-pipeline/research.md`
- [X] T033 [US3] Add quickstart checks for downstream review UI and override workflow mapping in `specs/003-reviewed-assertions-pipeline/quickstart.md`
- [X] T034 [US3] Update `specs/003-reviewed-assertions-pipeline/plan.md` so the summary and related-issues section explicitly describe the issues this slice closes or unblocks

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation parity, and validation across the full planning slice

- [X] T035 [P] Create or update `docs/adr/003-reviewed-assertions-promotion-model.md` with the implementation target and decision scope for this feature
- [X] T036 [P] Update `README.md` with any new reviewed-assertions contract references introduced by this feature
- [X] T037 [P] Update `docs/ROADMAP.md` with the reviewed-assertions lifecycle and issue linkage if the roadmap references change
- [X] T038 Reconcile `AGENTS.md` with the final planning artifact language for `003-reviewed-assertions-pipeline`
- [X] T039 Run `uv run pytest` and record the validation command set in `specs/003-reviewed-assertions-pipeline/quickstart.md`
- [X] T040 Run the quickstart walkthrough in `specs/003-reviewed-assertions-pipeline/quickstart.md` and reconcile any drift in `specs/003-reviewed-assertions-pipeline/spec.md`
- [X] T041 Update `archive-graph-spacy#4` with the final artifact set and close it if the documented closure criteria are satisfied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1’s lifecycle/data-model terminology staying stable
- **User Story 3 (P3)**: Depends on User Story 1 and User Story 2 because downstream integration points require stable reviewed and promotion states

### Within Each User Story

- Validation tasks before final story signoff
- Entity/data-model updates before contract examples
- Contract updates before quickstart validation
- Documentation parity before story completion

### Dependency Graph

- `US1 -> US2 -> US3`
- Polish depends on `US1`, `US2`, and `US3`

### Parallel Opportunities

- Setup tasks `T003` to `T006`
- Foundational tasks `T008` and `T009`
- US1 validation tasks `T012` and `T013`, then model tasks `T014` and `T015`
- US2 validation tasks `T020` and `T021`, then data-model/research tasks `T022` and `T023`
- US3 validation tasks `T028` and `T029`, then contract/spec tasks `T030` and `T031`
- Polish tasks `T035` to `T037`

---

## Parallel Example: User Story 1

```bash
# Launch the US1 validation checks together:
Task: "Verify the representative state-classification examples in specs/003-reviewed-assertions-pipeline/spec.md"
Task: "Verify the lifecycle examples in specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md"

# Launch the core US1 model updates together:
Task: "Define candidate assertion fields and validation rules in specs/003-reviewed-assertions-pipeline/data-model.md"
Task: "Define review decision, accepted assertion, promotion rule, and promotion outcome entities in specs/003-reviewed-assertions-pipeline/data-model.md"
```

---

## Parallel Example: User Story 2

```bash
# Launch the US2 validation checks together:
Task: "Verify promotion-eligibility examples in specs/003-reviewed-assertions-pipeline/spec.md"
Task: "Verify promotion guardrails and examples in specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md"

# Launch the US2 preparation tasks together:
Task: "Record the acceptance-versus-promotion research decisions in specs/003-reviewed-assertions-pipeline/research.md"
Task: "Define promotion-rule fields and validation rules in specs/003-reviewed-assertions-pipeline/data-model.md"
```

---

## Parallel Example: User Story 3

```bash
# Launch the US3 validation checks together:
Task: "Verify downstream integration interactions in specs/003-reviewed-assertions-pipeline/quickstart.md"
Task: "Verify UI and override integration points in specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md"

# Launch the US3 contract work together:
Task: "Add candidate-review-display, review-decision-capture, and promotion-handoff inputs/outputs in specs/003-reviewed-assertions-pipeline/contracts/reviewed-assertions-lifecycle.md"
Task: "Add downstream integration requirements in specs/003-reviewed-assertions-pipeline/spec.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm the core reviewed-assertions model closes the issue scope for `archive-graph-spacy#4`

### Incremental Delivery

1. Complete Setup + Foundational
2. Add User Story 1 → Validate reviewed-record model
3. Add User Story 2 → Validate promotion boundaries
4. Add User Story 3 → Validate downstream integration boundaries
5. Finish polish, ADR, and test-command parity

### Parallel Team Strategy

With multiple developers:

1. One person finalizes plan/research alignment
2. One person develops the data model and examples
3. One person develops the lifecycle contract and quickstart checks
4. Reconcile spec/ADR/README updates together before final validation

---

## Notes

- All tasks follow the required checkbox, ID, and file-path format
- User-story phases use `US1`, `US2`, and `US3` labels consistently
- The task list is documentation-first but still includes the constitution-required local test gate via `uv run pytest`
- `archive-graph-spacy#4` should not be closed until the ADR and lifecycle contract are complete and validated
