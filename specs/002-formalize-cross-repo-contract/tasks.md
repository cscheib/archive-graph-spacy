# Tasks: Cross-Repo Contract

**Input**: Design documents from `/specs/002-formalize-cross-repo-contract/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/cross-repo-boundary.md](contracts/cross-repo-boundary.md)

**Tests**: Local automated test commands must be identified for any code changes that follow from this contract. For this documentation-first feature, validation tasks focus on spec, ADR, and prerequisite checks.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation of each contract slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the local feature artifact set and validation scaffolding.

- [x] T001 Verify feature paths and active branch with `.specify/scripts/bash/check-prerequisites.sh --json` for `specs/002-formalize-cross-repo-contract/spec.md`
- [x] T002 Reconcile the technical context, constraints, and structure summary in [specs/002-formalize-cross-repo-contract/plan.md]
- [x] T003 [P] Confirm requirements-checklist coverage in [specs/002-formalize-cross-repo-contract/checklists/requirements.md]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the contract artifacts every user story depends on.

**⚠️ CRITICAL**: No user story work should be considered complete until this phase is complete.

- [x] T004 Reconcile the ownership, join-key, provenance, and promotion decisions in [specs/002-formalize-cross-repo-contract/research.md]
- [x] T005 [P] Reconcile the entity definitions, uniqueness rules, and lifecycle transitions in [specs/002-formalize-cross-repo-contract/data-model.md]
- [x] T006 [P] Reconcile the authoritative ownership and interface guarantees in [specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md]
- [x] T007 Reconcile the adoption workflow, validation steps, and release gate in [specs/002-formalize-cross-repo-contract/quickstart.md]
- [x] T008 Create the architecture decision record in [docs/adr/002-cross-repo-contract.md]

**Checkpoint**: Foundation ready. User story slices can now be completed and validated independently.

---

## Phase 3: User Story 1 - Shared Ownership Boundary (Priority: P1) 🎯 MVP

**Goal**: Deliver one authoritative ownership contract for canonical records, derived enrichment, candidate assertions, reviewed assertions, and promoted overrides.

**Independent Test**: A maintainer can read the contract artifacts and determine which repository owns each major data class without needing an additional architecture clarification.

### Validation for User Story 1

- [x] T009 [P] [US1] Validate ownership language and acceptance coverage in [specs/002-formalize-cross-repo-contract/spec.md]
- [x] T010 [P] [US1] Validate ownership entities and transitions in [specs/002-formalize-cross-repo-contract/data-model.md]

### Implementation for User Story 1

- [x] T011 [US1] Document repository ownership for canonical records, derived enrichment, candidate assertions, reviewed assertions, and promoted overrides in [specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md]
- [x] T012 [US1] Document the reviewed-assertion handoff boundary in [docs/adr/002-cross-repo-contract.md]
- [x] T013 [US1] Update the roadmap pointer and local source-of-truth note in [docs/ROADMAP.md]
- [x] T014 [US1] Update repository workflow guidance to reference the shared contract in [README.md]
- [x] T015 [US1] Record the publish-once reference model for both repositories in [specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md]

**Checkpoint**: User Story 1 is complete when ownership can be determined from the contract and linked local docs alone.

---

## Phase 4: User Story 2 - Stable Interface And Join Semantics (Priority: P2)

**Goal**: Define stable join-key, provenance, confidence, and interface-map rules that downstream features can implement consistently.

**Independent Test**: A maintainer can classify at least five representative data flows using the contract artifacts and identify the required join keys and provenance minimums without inventing missing rules.

### Validation for User Story 2

- [x] T016 [P] [US2] Validate join-key and provenance requirements in [specs/002-formalize-cross-repo-contract/spec.md]
- [x] T017 [P] [US2] Validate interface-map and identifier definitions in [specs/002-formalize-cross-repo-contract/data-model.md]
- [x] T018 [P] [US2] Run the five-flow review exercise described in [specs/002-formalize-cross-repo-contract/quickstart.md]

### Implementation for User Story 2

- [x] T019 [US2] Document immutable canonical-ID join rules and natural-identifier limitations in [specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md]
- [x] T020 [US2] Document provenance and confidence guarantees for derived and reviewed records in [specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md]
- [x] T021 [US2] Add interface-map guidance, downstream reference guidance, and five-flow validation notes in [specs/002-formalize-cross-repo-contract/quickstart.md]
- [x] T022 [US2] Record the contract rationale for immutable cross-repo join keys in [docs/adr/002-cross-repo-contract.md]

**Checkpoint**: User Story 2 is complete when downstream work can consume one stable interface definition without redefining join or provenance semantics.

---

## Phase 5: User Story 3 - Promotion And Reference Rules (Priority: P3)

**Goal**: Define reviewed-assertion lifecycle states, promotion eligibility, and durable audit boundaries for curation workflows.

**Independent Test**: A maintainer can classify at least five representative assertion examples as derived-only, reviewable, or promotion-eligible using the contract and ADR alone.

### Validation for User Story 3

- [x] T023 [P] [US3] Validate review-state and promotion acceptance coverage in [specs/002-formalize-cross-repo-contract/spec.md]
- [x] T024 [P] [US3] Validate reviewed-assertion lifecycle and promotion-rule modeling in [specs/002-formalize-cross-repo-contract/data-model.md]
- [x] T025 [P] [US3] Run the five-assertion classification exercise described in [specs/002-formalize-cross-repo-contract/quickstart.md]

### Implementation for User Story 3

- [x] T026 [US3] Document review-state, promotion-eligibility, accepted-but-not-promoted handling, and deferred questions in [specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md]
- [x] T027 [US3] Document promotion-rule rationale, rejected alternatives, and deferred questions in [docs/adr/002-cross-repo-contract.md]
- [x] T028 [US3] Add downstream adoption checks and five-assertion validation notes in [specs/002-formalize-cross-repo-contract/quickstart.md]

**Checkpoint**: User Story 3 is complete when review and promotion boundaries are explicit enough to unblock candidate-generation and curation workflow planning.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, validation, and release-readiness across all stories.

- [x] T029 [P] Refresh the implementation summary and constitution check in [specs/002-formalize-cross-repo-contract/plan.md]
- [x] T030 [P] Re-run and update the requirements checklist in [specs/002-formalize-cross-repo-contract/checklists/requirements.md]
- [x] T031 [P] Re-validate the quickstart adoption steps in [specs/002-formalize-cross-repo-contract/quickstart.md]
- [x] T032 [P] Add the exact local test command and release-gate command sequence to [specs/002-formalize-cross-repo-contract/quickstart.md]
- [x] T033 Run `uv run pytest` and capture any contract-related follow-up in [specs/002-formalize-cross-repo-contract/tasks.md]
- [x] T034 Run `.specify/scripts/bash/check-prerequisites.sh --json` and reconcile any path or numbering issues against [specs/002-formalize-cross-repo-contract/tasks.md]

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion; serves as the MVP contract slice.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and should build on the ownership boundaries finalized in US1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and should build on US1 ownership plus US2 interface semantics.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends conceptually on US1 because stable interfaces must attach to explicit ownership boundaries.
- **US3 (P3)**: Depends conceptually on US1 and US2 because promotion rules require both repository ownership and stable identifier/provenance semantics.

### Within Each User Story

- Validation tasks should run before story-specific documentation changes are treated as done.
- Contract updates should precede or accompany ADR updates for the same story.
- Quickstart and roadmap/reference updates should happen before the story is considered complete.

### Parallel Opportunities

- `T003`, `T005`, and `T006` can run in parallel during Setup and Foundational work.
- Within **US1**, `T009` and `T010` can run in parallel, followed by `T013` and `T014` in parallel once the core contract text is stable.
- Within **US2**, `T016`, `T017`, and `T018` can run in parallel, followed by `T021` and `T022` in parallel.
- Within **US3**, `T023`, `T024`, and `T025` can run in parallel.
- In the Polish phase, `T029`, `T030`, `T031`, and `T032` can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Validate the story slice in parallel
Task: "Validate ownership language and acceptance coverage in specs/002-formalize-cross-repo-contract/spec.md"
Task: "Validate ownership entities and transitions in specs/002-formalize-cross-repo-contract/data-model.md"

# After the contract text is stable, update linked docs in parallel
Task: "Update the roadmap pointer and local source-of-truth note in docs/ROADMAP.md"
Task: "Update repository workflow guidance to reference the shared contract in README.md"
```

## Parallel Example: User Story 2

```bash
# Validate interface semantics in parallel
Task: "Validate join-key and provenance requirements in specs/002-formalize-cross-repo-contract/spec.md"
Task: "Validate interface-map and identifier definitions in specs/002-formalize-cross-repo-contract/data-model.md"
Task: "Run the five-flow review exercise described in specs/002-formalize-cross-repo-contract/quickstart.md"

# Then update operator and architectural guidance in parallel
Task: "Add interface-map guidance and validation notes for downstream issue authors in specs/002-formalize-cross-repo-contract/quickstart.md"
Task: "Record the contract rationale for immutable cross-repo join keys in docs/adr/002-cross-repo-contract.md"
```

## Parallel Example: User Story 3

```bash
# Validate lifecycle semantics in parallel
Task: "Validate review-state and promotion acceptance coverage in specs/002-formalize-cross-repo-contract/spec.md"
Task: "Validate reviewed-assertion lifecycle and promotion-rule modeling in specs/002-formalize-cross-repo-contract/data-model.md"
Task: "Run the five-assertion classification exercise described in specs/002-formalize-cross-repo-contract/quickstart.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate that ownership boundaries are unambiguous across the contract, ADR, roadmap pointer, and README.

### Incremental Delivery

1. Complete Setup + Foundational to establish the contract artifact set.
2. Deliver US1 to lock ownership boundaries.
3. Deliver US2 to lock join-key, provenance, and interface guarantees.
4. Deliver US3 to lock review and promotion rules.
5. Finish with Polish tasks to revalidate numbering, checklist state, quickstart instructions, and the local test gate.

### Parallel Team Strategy

1. One contributor finalizes foundational artifacts in `research.md`, `data-model.md`, and `contracts/cross-repo-boundary.md`.
2. After Foundational completion:
   - Contributor A completes US1 reference updates.
   - Contributor B completes US2 interface semantics.
   - Contributor C completes US3 promotion semantics.
3. Rejoin for ADR finalization and final validation in Phase 6.

---

## Notes

- All tasks use the required checklist format with task ID, optional parallel marker, optional story label, and an exact file path.
- User story tasks are organized for independent validation rather than code-level coupling.
- This feature is documentation-first; downstream code changes should create separate implementation tasks once the contract is accepted.
- Five-flow review exercise completed on 2026-03-08 using the recommended set in `quickstart.md`; no additional ownership, join-key, or provenance rules were required.
- Five-assertion classification exercise completed on 2026-03-08 using the recommended set in `quickstart.md`; each example fit the documented `derived_only`, `reviewable`, or `promotion_eligible` classifications.
- `uv run pytest` passed on 2026-03-08 with 55 tests passing and no failures.
