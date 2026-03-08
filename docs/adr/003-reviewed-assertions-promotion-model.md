# ADR 003: Reviewed Assertions Promotion Model

## Status

Accepted

## Context

ADR 002 established the cross-repo ownership boundary between
`archive-graph-spacy` and `archive-graph-data`, but it left one model gap
open: how candidate assertions move from derived enrichment into durable review
history and, in limited cases, into canonical override promotion. Roadmap
issue `archive-graph-spacy#4` requires that lifecycle to be explicit before
candidate assertion generation (`archive-graph-spacy#2`) and downstream review
workflow issues (`archive-graph-data#70` and `archive-graph-data#71`) can be
implemented safely.

## Decision

Publish the first reviewed-assertions promotion model in `archive-graph-spacy`
and treat it as the authoritative workflow definition for:

- first-wave assertion types `relay_sender_identity` and
  `person_link_disambiguation`
- review decision states `queued`, `accepted`, `rejected`, and `superseded`
- durable accepted reviewed assertions as a state distinct from canonical
  overrides
- explicit promotion eligibility classes `promotion_eligible` and
  `derived_only`
- explicit human action as a requirement for every promotion to canonical
  override
- exact field-level contracts for candidate review display, review decision
  capture, and promotion handoff

## Consequences

Positive:

- `archive-graph-spacy#4` can close with one auditable model and lifecycle
  contract
- `archive-graph-spacy#2` can generate candidate assertions without inventing
  its own review-state model
- `archive-graph-spacy#2` can publish one persisted candidate surface
  (`candidate_assertions.jsonl`) plus one diagnostics summary
  (`candidate_assertions_summary.json`) without conflating candidate outputs
  with reviewed storage
- downstream review and override workflows have one contract to reference for
  ownership, state transitions, and required fields
- reviewed history remains durable without silently rewriting canonical truth

Negative:

- future assertion types must update the contract before they can be reviewed
  or promoted
- this repo must maintain both ADR 002 and ADR 003 as linked cross-repo
  planning artifacts
- downstream implementations still need their own concrete UI and storage
  designs after this model is accepted

## Alternatives Considered

- Treat acceptance as immediate promotion
  - rejected because it collapses reviewed history into canonical mutation and
    removes the explicit audit boundary the roadmap requires
- Allow background or rule-only promotion in v1
  - rejected because the initial workflow must be human-reviewed and explicit
- Keep downstream payload requirements generic
  - rejected because `archive-graph-data` would still have to invent local
    candidate, decision, and promotion field contracts

## Deferred Questions

- Which future assertion types beyond the first wave should become
  `promotion_eligible`?
- Should future relay sender candidate rules expand beyond explicitly
  relay-like sender addresses?
- Should future disambiguation candidate rules expand beyond leading-token,
  multi-candidate ambiguity cases?
- What concrete UI affordances should `archive-graph-data` require for
  reviewer rationale, conflict handling, and supersession history?
- What validation workflow should downstream repos use to prove they still
  conform to ADR 002 and ADR 003 after later refactors?
