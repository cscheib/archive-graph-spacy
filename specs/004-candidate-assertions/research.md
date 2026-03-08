# Phase 0 Research: Candidate Assertions

## Decision: Extend the existing `nlpdata` pipeline instead of creating a separate candidate-generation subsystem

**Rationale**: The current repository already has a run-scoped derivation flow
that loads a source bundle, derives enrichment rows, validates payload
contracts, and writes JSONL outputs. Candidate assertions fit naturally into
that existing shape and do not require a new orchestration layer.

**Alternatives considered**:
- Create a standalone candidate-generation CLI and output format
  - rejected because it would duplicate the existing run/payload/write flow
- Defer candidate generation entirely to a downstream review repo
  - rejected because `archive-graph-spacy` owns candidate assertion generation
    under ADR 002 and ADR 003

## Decision: Persist candidate assertions as a first-class derived output surface alongside existing `nlpdata` artifacts

**Rationale**: The clarified spec requires a persisted candidate output surface
plus a human-readable diagnostics summary. Writing candidate assertions as a
run-scoped derived output keeps downstream consumption explicit and consistent
with the rest of the repository’s local bundle artifacts.

**Alternatives considered**:
- Emit only console diagnostics
  - rejected because downstream workflows need a durable handoff surface
- Embed candidate assertions only inside existing person-link rows
  - rejected because that would blur reviewable candidates with canonical or
    derived link artifacts

## Decision: Publish a separate diagnostics summary artifact for candidate counts and suppression reasons

**Rationale**: The persisted candidate output solves downstream consumption, but
local validation still benefits from a small human-readable summary that
explains how many candidates were emitted, which assertion types appeared, and
which cases were suppressed.

**Alternatives considered**:
- Rely on raw JSONL inspection only
  - rejected because it slows local review and hides suppression reasons
- Store diagnostics only inside run metrics
  - rejected because a human-readable artifact is easier to inspect during
    quickstart validation

## Decision: Bound `person_link_disambiguation` candidates to multi-candidate/no-clear-winner mention-link cases

**Rationale**: This is the narrowest useful rule that matches the clarified
spec and the reviewed-assertions contract. It prevents the first implementation
from turning every low-confidence mention into a review candidate.

In the implemented v1 rule, the ambiguous mention must also be a single-token
leading-name token for each plausible candidate. This suppresses low-value
surname collisions like `Example` while still surfacing high-value first-name
ambiguities like `Alex`, `Jamie`, and `Sam`.

**Alternatives considered**:
- Emit candidates for every low-confidence person link
  - rejected because it would flood the review surface with weak-value cases
- Emit candidates for any heuristic ambiguity signal
  - rejected because the rule set would be too broad and unstable for v1

## Decision: Use stable run-scoped candidate identity based on assertion type, subject, claim, and generation scope

**Rationale**: The clarified spec requires deterministic rerun behavior without
prematurely solving global historical deduplication. A run-scoped identity rule
provides that stability while keeping the implementation small.

**Alternatives considered**:
- Always emit fresh candidate IDs on every run
  - rejected because reruns would produce unnecessary duplicate review records
- Deduplicate globally across all runs
  - rejected because that adds cross-run history management not required for
    the current issue

## Decision: Treat relay sender candidates as a bounded relay-address workflow, not generic unresolved-sender inference

**Rationale**: The implemented v1 rule requires the sender address to look
relay-like before candidate generation runs. That keeps `relay_sender_identity`
focused on the roadmap target instead of surfacing every unresolved sender with
one inferred mention link.

**Alternatives considered**:
- Emit relay candidates for any unresolved sender with one strong inferred link
  - rejected because it would overproduce candidates for ordinary unresolved
    email addresses and blur the v1 issue scope

## Decision: Amend ADR 003 rather than creating a new ADR

**Rationale**: Candidate generation is the first concrete implementation of the
reviewed-assertions promotion model, not a separate architecture. The decision
record should therefore extend the accepted reviewed-assertions ADR rather than
split the model across multiple ADRs.

**Alternatives considered**:
- Create ADR 004 for candidate generation
  - rejected because the change extends the same architectural boundary already
    established in ADR 003
