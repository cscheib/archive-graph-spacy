<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
  - Principle slot 1 -> I. Local Test Gate Before Deployment
  - Principle slot 2 -> II. Minimal Complexity
  - Principle slot 3 -> III. Spec Before Code
  - Principle slot 4 -> IV. Documentation Parity
  - Principle slot 5 -> V. Decision Records for Architecture
- Added sections:
  - Delivery Constraints
  - Review and Release Process
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ /Users/chris/src/archive-graph-spacy/.specify/templates/plan-template.md
  - ✅ /Users/chris/src/archive-graph-spacy/.specify/templates/spec-template.md
  - ✅ /Users/chris/src/archive-graph-spacy/.specify/templates/tasks-template.md
  - ⚠ pending /Users/chris/src/archive-graph-spacy/.specify/templates/commands/*.md (directory not present)
- Follow-up TODOs:
  - None
-->
# Archive Graph Spacy Constitution

## Core Principles

### I. Local Test Gate Before Deployment
Every code change MUST have automated local tests that execute on the developer
machine before deployment. A change is not deployable until the relevant test
suite is added or updated, run locally, and passes. Bug fixes MUST include a
test that fails before the fix and passes after it. Manual verification may
supplement tests, but it does not replace the local test gate.

Rationale: deployment without local proof of behavior creates avoidable
regressions and hides broken assumptions until the most expensive stage.

### II. Minimal Complexity
Implementations MUST solve the current requirement with the simplest design that
meets the documented need. Premature abstractions, speculative error handling,
and feature flags for hypothetical future scenarios are prohibited unless a
current requirement explicitly demands them. Reviewers MUST reject complexity
that is not tied to a present, documented use case.

Rationale: unused flexibility increases maintenance cost, obscures intent, and
slows future changes.

### III. Spec Before Code
Implementation work MUST start from a written spec that defines user scenarios,
requirements, and success criteria before code changes begin. If behavior
changes during implementation, the spec MUST be updated in the same commit as
the code. Work without an up-to-date spec is non-compliant.

Rationale: a current spec gives the team a stable contract for scope, tradeoffs,
and acceptance.

### IV. Documentation Parity
Documentation that explains behavior, usage, operational steps, or interfaces
MUST stay consistent with the code in the same commit that changes behavior.
This includes quickstarts, usage guidance, contract descriptions, and any
developer workflow notes. Drift between code and documentation is treated as a
defect.

Rationale: stale documentation produces incorrect implementations and invalid
operational decisions.

### V. Decision Records for Architecture
Any architectural choice that changes system structure, core dependencies,
integration boundaries, data contracts, or operational model MUST have a
decision record created or updated in the same change. The record MUST capture
the decision, the reason it was made, and the simpler alternatives considered.
Purely local refactors that do not alter architecture do not require a new
record.

Rationale: architectural choices outlive individual changes and require durable,
auditable context.

## Delivery Constraints

- All work MUST be scoped to current requirements captured in the active spec.
- If a proposed solution requires added complexity, the implementation plan MUST
  record the justification and the simpler option that was rejected.
- Every deployment candidate MUST identify the local test command set that was
  run and the documentation updated alongside the change.
- Architectural changes MUST reference the corresponding decision record before
  implementation is approved.

## Review and Release Process

- Plans MUST pass a constitution check before research and design proceed.
- Specs MUST exist before implementation tasks are generated.
- Task lists MUST include local test creation or updates, documentation updates,
  and decision record work when architecture changes.
- Code review MUST verify four things before approval: current spec coverage,
  minimal complexity, documentation parity, and passing local tests.
- Deployment approval MUST be blocked if any required local test has not been
  run successfully on the change being released.

## Governance

This constitution supersedes conflicting local process guidance. Amendments
MUST be made through a documented change to this file, MUST include updates to
affected templates or workflow documents in the same change, and MUST record
the version bump rationale.

Versioning follows semantic versioning for governance:
- MAJOR: removes or redefines a principle or governance rule in a
  backward-incompatible way.
- MINOR: adds a principle, section, or materially stronger requirement.
- PATCH: clarifies wording without changing the required behavior.

Compliance review is mandatory for every plan, spec, task list, code review, and
deployment decision. Reviewers and authors share responsibility for enforcing
this constitution. Non-compliant work MUST be corrected before merge or release.

**Version**: 1.0.0 | **Ratified**: 2026-03-06 | **Last Amended**: 2026-03-06
