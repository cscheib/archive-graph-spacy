# Phase 0 Research: Feedback Consumption and Relationship Outputs

## Decision: Consume reviewed feedback directly from `graph-data` tables at derivation time, but record the reviewed-input read boundary in run diagnostics

**Rationale**: `archive-graph-data` already owns reviewed assertions and review
decisions, so `archive-graph-spacy` should read `memory.reviewed_assertions`
as the semantic source and `memory.review_assertion_decisions` as audit or
supporting state rather than materializing a second durable reviewed store.
Each `build_nlpdata` run should record the source catalog and reviewed-input
read boundary it used so reruns and diagnostics remain interpretable.

**Alternatives considered**:
- Materialize local snapshot tables in `archive-graph-spacy`
  - rejected because it duplicates durable reviewed state and introduces
    synchronization drift
- Read live tables without recording any read boundary
  - rejected because reruns would be harder to interpret once reviewed inputs
    change
- Depend only on exported JSON snapshots
  - rejected because it creates a parallel ingestion path and weakens bounded
    rerun behavior

## Decision: Use a strict semantic replay key with bounded evidence-window tolerance

**Rationale**: Candidate IDs are not the durable replay surface across reruns,
so replay must key on semantics. The stable key should be
`assertion_type + normalized subject identity + normalized claim payload +
scope discriminator + evidence-window anchor`. Tolerance should be limited to
small evidence-window drift, while subject identity, claim meaning, pair scope,
and candidate family must still match exactly.

**Alternatives considered**:
- Match only on prior `candidate_assertion_id`
  - rejected because regenerated candidate IDs may differ across reruns
- Require an exact full evidence hash
  - rejected because minor bounded rerun drift would break replay for the same
    semantic case
- Use broad fuzzy matching
  - rejected because it is harder to reason about, test, and operate safely

## Decision: Treat materially conflicting accepted reviewed outcomes as `conflicted`, not self-healing

**Rationale**: Accepted human review should remain durable, but it should not
silently override materially changed derived evidence. When a replay-matched
accepted reviewed outcome materially conflicts with new derivation, the system
should mark it `conflicted`, avoid auto-applying it, and surface the case in
diagnostics for renewed human review.

**Alternatives considered**:
- Always prefer the accepted reviewed outcome
  - rejected because stale review could silently override changed evidence
- Always prefer fresh derivation
  - rejected because that would erase durable human review value
- Auto-create a new accepted state on conflict
  - rejected because ADR 003 requires explicit human review and promotion
    boundaries

## Decision: Keep reviewed-effect diagnostics to a small explicit result model

**Rationale**: The result categories `applied`, `suppressed`, `skipped`,
`conflicted`, and `ignored` are enough for local tests, run diagnostics, and
downstream consumers. They distinguish replay failure, semantic conflict, and
intentional non-application without turning diagnostics into a second event
ledger.

**Alternatives considered**:
- Record only applied/not-applied counts
  - rejected because operators could not distinguish replay failure from
    semantic conflict
- Emit free-form logs only
  - rejected because tests and downstream consumers need stable categories
- Add an exhaustive event-sourcing model
  - rejected because Phase 3 needs bounded operational clarity, not a new
    history subsystem

## Decision: Publish relationship outputs as two contract-bearing tables: `person_person_edges` and `person_person_edge_evidence`

**Rationale**: The summary table should carry one deterministic canonical row
per unordered person pair, while the evidence table carries bounded supporting
records that explain that row. This keeps the summary contract easy to consume
and avoids forcing downstream code to rebuild pair semantics from evidence.

**Alternatives considered**:
- Publish only evidence rows and force downstream aggregation
  - rejected because each consumer would reinvent pair semantics
- Publish only one summary row with embedded evidence arrays
  - rejected because bounded evidence is harder to query and review that way
- Publish one row per relationship facet per pair
  - rejected because the clarified contract is one canonical row per pair in
    the first pass

## Decision: Keep pair evidence bounded, representative, and deterministic

**Rationale**: `person_person_edge_evidence` should keep a small deterministic
set of representative evidence rows per pair and per evidence family, enough to
explain the pair without copying full relationship history. Selection should be
rule-based rather than random or first-N.

**Alternatives considered**:
- Publish exhaustive evidence for every supporting message
  - rejected because it breaks bounded-output discipline and increases rerun
    noise
- Publish a random or first-N sample
  - rejected because replay determinism and reviewer trust require stable
    evidence selection
- Omit weak or indirect evidence entirely
  - rejected because downstream consumers still need to distinguish strong
    direct pairs from weak inferred pairs

## Decision: Treat `relationship_evidence_review` as a normal candidate assertion family marked `derived_only`

**Rationale**: This family should use the same candidate schema, diagnostics,
replay matching, reviewed-input consumption, and conflict handling as existing
families. It should remain reviewable but `derived_only`, so relationship
interpretation can affect derived outputs without implying canonical promotion.

**Alternatives considered**:
- Create a special relationship review queue outside candidate assertions
  - rejected because it fractures the reviewed lifecycle
- Mark relationship review as promotion-eligible
  - rejected because Phase 3 needs derived relationship curation, not canonical
    override writes
- Store only pair-level reviewed flags
  - rejected because that loses evidence provenance and replayability

## Decision: Keep downstream contract fields minimal but explanation-complete

**Rationale**: `person_person_edges` should carry a stable `pair_id`, canonical
person IDs, scope or run linkage, strength signals, evidence-family counts, a
strongest relationship signal, a strongest evidence pointer, and `is_current`.
`person_person_edge_evidence` should carry `pair_evidence_id`, `pair_id`,
source reference, evidence family, contribution score, bounded rank, and
provenance. Diagnostics should report emitted row counts, evidence-family
counts, truncation counts, and reviewed-effect counts per candidate family.

**Alternatives considered**:
- Add narrative summary fields to the base pair row
  - rejected because those can be derived later from summary plus evidence
- Publish only raw counts with no strongest-evidence pointers
  - rejected because consumers still need a basic explanation hook
- Make diagnostics pair-level and exhaustive
  - rejected because bounded run-level diagnostics are enough for current
    requirements
