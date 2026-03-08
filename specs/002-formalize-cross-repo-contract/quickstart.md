# Quickstart: Cross-Repo Contract

## Goal

Validate and adopt the shared contract between `archive-graph-data` and
`archive-graph-spacy` before dependent reviewed-assertion and UI roadmap work
begins.

## 1. Prepare Local Context

```bash
uv sync --dev
uv run pytest
```

Use the full local test suite as the release gate for any implementation work
that follows from this contract. This planning feature itself is documentation
first, but downstream code changes must still satisfy the local test gate.

Record the exact local test command sequence used for the active change and any
follow-up notes before treating the contract as implementation-ready.

## 2. Review The Contract Artifacts

Confirm the feature artifacts are internally consistent:

- [spec.md](spec.md)
- [plan.md](plan.md)
- [research.md](research.md)
- [data-model.md](data-model.md)
- [cross-repo-boundary.md](contracts/cross-repo-boundary.md)

Verify that all five decisions remain true:

- canonical records and promoted overrides live in `archive-graph-data`
- derived enrichment and candidate assertions live in `archive-graph-spacy`
- reviewed assertions live in `archive-graph-data`
- immutable canonical IDs are the only authoritative cross-repo join keys
- provenance and confidence requirements remain explicit across the handoff

Document intentionally deferred questions in:

- `docs/adr/002-cross-repo-contract.md`
- `specs/002-formalize-cross-repo-contract/contracts/cross-repo-boundary.md`

## 3. Confirm ADR And Roadmap Alignment

Before implementation, confirm the architectural decision record path and
roadmap references are aligned:

- ADR path: `docs/adr/002-cross-repo-contract.md`
- Roadmap pointer: [docs/ROADMAP.md](../../docs/ROADMAP.md)
- Active feature spec: [spec.md](spec.md)

Dependent issues should reference this contract rather than redefining
ownership or join semantics locally.

Run a five-flow review exercise and confirm the contract can classify at least
five representative cross-repo data flows without inventing new ownership,
join-key, or provenance rules during the exercise.

Recommended five-flow review set:

1. canonical person record referenced by derived search enrichment
2. candidate assertion handed off into reviewed assertion storage
3. accepted reviewed assertion promoted into a canonical override
4. accepted-but-not-promoted reviewed assertion retained as durable review
   history
5. natural identifier present as evidence but not used as a cross-repo join key

## 4. Apply The Contract To Downstream Work

Any implementation that follows from this feature should:

- preserve `archive-graph-data` ownership of canonical records, reviewed
  assertions, and promoted overrides
- preserve `archive-graph-spacy` ownership of derived enrichment and candidate
  assertions
- require immutable canonical IDs for cross-repo joins
- preserve evidence lineage and confidence semantics through candidate,
  reviewed, and promoted states
- update the ADR and relevant repo documentation in the same change as any
  contract-shaping implementation

Run a five-assertion classification exercise and confirm the contract can
classify at least five representative assertion examples as `derived_only`,
`reviewable`, or `promotion_eligible`.

Recommended five-assertion review set:

1. relay-sender identity candidate
2. person disambiguation candidate
3. low-confidence candidate with evidence but no promotion eligibility
4. accepted reviewed assertion that remains derived-only
5. accepted reviewed assertion that qualifies for promotion

## 5. Release Gate

Do not start downstream implementation unless:

- the active spec and plan are current
- the contract document is agreed and referenced by dependent issues
- the ADR path is created or scheduled in the same change
- documentation updates are identified in both affected repositories
- local automated tests are identified and run for any code changes that follow
- the exact local test command sequence is recorded, at minimum:

```bash
uv sync --dev
uv run pytest
```
