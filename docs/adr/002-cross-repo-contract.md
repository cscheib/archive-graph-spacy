# ADR 002: Cross-Repo Contract

## Status

Accepted

## Context

The roadmap depends on a stable boundary between `archive-graph-data` and
`archive-graph-spacy` before reviewed assertions, curation workflows, and
person-centric discovery features expand. Existing work already separates
canonical records from derived enrichment, but it does not yet define where
candidate assertions end, where reviewed assertions begin, how cross-repo joins
remain stable, or which assertion types may be promoted upstream.

## Decision

Publish the shared cross-repo contract in `archive-graph-spacy` and treat it as
the authoritative boundary definition for:

- canonical records and promoted overrides owned by `archive-graph-data`
- derived enrichment and candidate assertions owned by `archive-graph-spacy`
- reviewed assertions owned by `archive-graph-data` once human review begins
- immutable canonical IDs as the only authoritative cross-repo join keys
- provenance and confidence as first-class requirements for derived and
  reviewed states
- explicit assertion classifications of `derived_only`, `reviewable`, and
  `promotion_eligible`

## Consequences

Positive:

- one authoritative contract can unblock roadmap items without repeating
  boundary rules in each issue
- review history and promotion decisions stay in one durable curation boundary
- cross-repo joins remain stable through renames, alias changes, and override
  corrections
- downstream features can inherit consistent provenance and confidence
  semantics

Negative:

- the contract must now be maintained deliberately as a cross-repo planning
  artifact
- downstream repos must reference the published contract instead of inventing
  local variants
- future assertion classes may require explicit contract updates before
  implementation

## Alternatives Considered

- Keep reviewed assertions in `archive-graph-spacy` and only send promoted
  overrides upstream
  - rejected because it splits durable review history from the curation system
    that owns canonical override decisions
- Allow natural identifiers such as names or emails as primary cross-repo join
  keys
  - rejected because those identifiers can drift or collide over time
- Document the boundary only inside issue bodies or the roadmap
  - rejected because issue-local definitions would drift and fail to provide a
    durable architectural reference

## Deferred Questions

- Which first-wave assertion types beyond relay-sender identity and
  disambiguation should be marked `promotion_eligible`?
- What concrete review metadata fields should the curation UI require before a
  reviewed assertion can move to `accepted` or `promoted`?
- What validation process should downstream repos use to prove they still point
  at the shared contract after future refactors?
