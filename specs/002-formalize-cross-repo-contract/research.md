# Phase 0 Research: Cross-Repo Contract

## Decision: Keep `archive-graph-data` as the source of truth for canonical records and promoted overrides

- **Rationale**: Existing repo docs already position `graph-data` as the owner
  of canonical records and override decisions. The new contract should extend
  that boundary rather than create a second durable home for canonical facts.
- **Alternatives considered**:
  - Move canonical override ownership into `archive-graph-spacy`: rejected
    because it would blur the established split between canonical and derived
    concerns.
  - Share override ownership across both repos: rejected because it would
    create competing durable stores for the same facts.

## Decision: Keep `archive-graph-spacy` focused on derived enrichment and candidate assertion generation

- **Rationale**: This repository already owns derived NLP outputs and
  experimentation. Candidate assertions fit that boundary because they are
  evidence-backed proposals rather than reviewed source-of-truth facts.
- **Alternatives considered**:
  - Generate candidates directly inside `archive-graph-data`: rejected because
    it would mix derivation experimentation with curation ownership.
  - Keep candidate generation undefined until later: rejected because reviewed
    assertion planning depends on a clear pre-review boundary now.

## Decision: Hand off reviewed assertions to `archive-graph-data` at the start of human review

- **Rationale**: Human review, accepted decisions, rejected decisions,
  supersession, and canonical override promotion all belong in one durable
  curation boundary. That keeps review history auditable and prevents state
  drift across repositories.
- **Alternatives considered**:
  - Keep reviewed assertions in `archive-graph-spacy` and only send promoted
    overrides upstream: rejected because it splits the durable review lifecycle
    from the curation system that owns final override decisions.
  - Store reviewed assertions in both repos: rejected because it creates
    synchronization and conflict risk with little benefit.

## Decision: Require immutable canonical IDs as the only authoritative cross-repo join keys

- **Rationale**: Names, emails, aliases, and handles can change as curation
  improves. Immutable canonical IDs keep joins stable through renames, merges,
  and override changes.
- **Alternatives considered**:
  - Allow natural identifiers as primary joins: rejected because they can drift
    or collide over time.
  - Let each data class pick its own join key: rejected because the contract
    would no longer provide stable cross-repo semantics.

## Decision: Make provenance and confidence first-class guarantees for derived and reviewed records

- **Rationale**: The current `nlpdata` work already requires provenance for
  derived outputs. The reviewed-assertion contract should preserve the same
  traceability standard so every candidate and decision can be inspected and
  defended.
- **Alternatives considered**:
  - Require provenance only for derived rows: rejected because review and
    promotion decisions would become less auditable than their source evidence.
  - Treat confidence as informal metadata: rejected because downstream review
    workflows need consistent interpretation.

## Decision: Use separate planning artifacts for model, guarantees, and adoption workflow

- **Rationale**: The existing `001-nlpdata-schema` feature already uses a clean
  split between `data-model.md`, `contracts/`, `quickstart.md`, and an ADR. The
  same shape fits this feature and keeps long-lived architecture rationale
  separate from contract guarantees and operator workflow.
- **Alternatives considered**:
  - Put everything into the spec only: rejected because it would overload the
    feature spec and blur planning concerns.
  - Put everything into the ADR only: rejected because the ADR should explain
    structural choices, not serve as the operational contract.
