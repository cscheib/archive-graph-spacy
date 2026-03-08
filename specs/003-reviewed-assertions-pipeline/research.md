# Phase 0 Research: Reviewed Assertions Pipeline

## Decision: Keep the first reviewed-assertions scope limited to relay sender identity and ambiguous person-link/disambiguation assertions

**Rationale**: The active roadmap already identifies these as the first
high-value reviewable assertion types. Constraining v1 to those two categories
keeps the model specific enough to test and avoids speculative schema work for
assertion families that are not yet prioritized.

**Alternatives considered**:
- Define a generic model for all future assertion types immediately
  - rejected because it would force premature abstraction and weaken the
    examples needed to close `archive-graph-spacy#4`
- Leave assertion types unnamed in v1
  - rejected because downstream teams would still not know which first-wave
    review workflows this issue actually unblocks

## Decision: Classify relay sender identity as `promotion_eligible` and person-link/disambiguation as `reviewable` but `derived_only` in v1

**Rationale**: Relay sender identity can plausibly produce durable canonical
override candidates when supported by strong evidence and explicit review.
Ambiguous person-link/disambiguation assertions are still valuable for review
and downstream diagnostics, but they carry higher merge-risk and should not
rewrite canonical truth in the initial workflow.

**Alternatives considered**:
- Mark both first-wave assertion types as `promotion_eligible`
  - rejected because initial disambiguation workflows should stay safer and
    avoid early canonical merge promotion
- Mark both first-wave assertion types as `derived_only`
  - rejected because the roadmap explicitly needs at least one real promotion
    path to define the feedback loop

## Decision: Treat acceptance and promotion as separate lifecycle steps

**Rationale**: The reviewed-assertions model exists to prevent candidate or
reviewed facts from silently mutating canonical truth. Separating
`accepted_reviewed` from `promoted_override` preserves auditability and makes
the reviewed store useful even for assertions that should never become
canonical overrides.

**Alternatives considered**:
- Make acceptance and promotion the same step
  - rejected because it collapses reviewed history into canonical mutation and
    recreates the silent-feedback-loop risk this feature is meant to stop
- Skip durable accepted reviewed storage and store only rejected or promoted
  - rejected because accepted-but-not-promoted assertions are part of the
    durable curation record

## Decision: Require explicit human action for every promotion to canonical override

**Rationale**: The initial reviewed-assertions workflow should be reviewable,
auditable, and safe by default. Requiring explicit human promotion aligns with
the clarified spec and reduces the risk of automatic self-reinforcement.

**Alternatives considered**:
- Allow automatic promotion once an assertion type and evidence satisfy rules
  - rejected because it weakens the explicit review boundary too early
- Allow background promotion for some assertion types in v1
  - rejected because the current scope does not justify the added complexity

## Decision: Keep reviewed assertions and promoted overrides in `archive-graph-data`, while `archive-graph-spacy` defines the candidate-side handoff contract

**Rationale**: ADR 002 already establishes that human review begins in
`archive-graph-data`. This plan should extend that boundary with a concrete
lifecycle model rather than moving durable review state back into
`archive-graph-spacy`.

**Alternatives considered**:
- Move reviewed assertion storage into `archive-graph-spacy`
  - rejected because it would contradict the accepted cross-repo contract
- Split accepted reviewed storage across both repos
  - rejected because it would create duplicate durable state and ownership
    confusion

## Decision: Publish one lifecycle contract artifact that downstream UI and override workflows can both reference

**Rationale**: `archive-graph-spacy#4` is primarily a model-and-workflow issue.
A single contract artifact with examples, state rules, and integration points is
the smallest deliverable that can close the issue and unblock downstream work.

**Alternatives considered**:
- Put the lifecycle rules only in the ADR
  - rejected because downstream teams need a directly referenceable workflow
    contract with concrete entities and examples
- Put the lifecycle rules only in the spec
  - rejected because the spec is issue-specific and not the best durable
    reference for later implementation work

## Decision: Require explicit field-level contracts for candidate display, review capture, and promotion handoff

**Rationale**: `archive-graph-data#70` and `archive-graph-data#71` cannot
implement UI display or override handoff safely if the lifecycle contract only
describes generic inputs and outputs. Naming the required fields keeps the
first workflow bounded and auditable.

**Alternatives considered**:
- Leave downstream payloads as generic input/output descriptions
  - rejected because downstream teams would still invent local field rules
- Define full API or table schemas in this repo
  - rejected because this feature should stop at a technology-agnostic
    contract, not implementation-specific interfaces
