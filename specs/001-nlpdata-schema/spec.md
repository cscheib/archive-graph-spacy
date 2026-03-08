# Feature Specification: NLP Search Workspace

**Feature Branch**: `001-nlpdata-schema`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Create a plan to implement this in a new schema in
the dev catalog named nlpdata"

**Implementation Readiness**: This spec MUST be complete before implementation
begins. If behavior changes later, update this spec in the same commit as the
code change.

## Clarifications

### Session 2026-03-06

- Q: Should the search-ready workspace duplicate full interaction text or store
  derived search fields plus source references only? → A: Store derived search
  fields and source interaction references, but not duplicated full text.
- Q: Should the first rollout create message-level records, thread-level
  records, or both? → A: Message-level records only in the first rollout.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Searchable Person Involvement (Priority: P1)

As an archive operator, I want a dedicated derived workspace that links
interactions to canonical people so I can answer "show me all messages
involving this person" without altering the source archive tables.

**Why this priority**: Person-centric retrieval is the primary value of the NLP
workspace and unlocks the search use case the project is pursuing.

**Independent Test**: Can be fully tested by loading a bounded interaction slice
into the workspace and verifying that a reviewer can retrieve all explicit and
inferred person-linked interactions for a chosen person from the derived data
alone.

**Acceptance Scenarios**:

1. **Given** the development catalog contains canonical people and interactions,
   **When** the workspace is refreshed, **Then** derived person-message links are
   created in `nlpdata` without modifying source records.
2. **Given** a reviewer selects a canonical person, **When** they query the
   derived workspace, **Then** they can retrieve interactions where that person
   was an explicit participant and interactions where that person was only
   referenced in the content.

---

### User Story 2 - Searchable Conversation Themes (Priority: P2)

As a search analyst, I want interactions in the workspace to carry searchable
theme tags so I can narrow results by topics such as family, work, travel, or
support issues in addition to people.

**Why this priority**: Theme-aware search expands the workspace from identity
linking into practical archive retrieval and makes the derived data more useful
than metadata-only search.

**Independent Test**: Can be fully tested by running the workspace on a sample
set, querying for a theme, and confirming that the returned interactions include
the expected topical evidence.

**Acceptance Scenarios**:

1. **Given** interactions with recognizable conversational topics, **When** the
   workspace is refreshed, **Then** each tagged interaction includes one or more
   searchable themes with provenance and confidence.
2. **Given** a reviewer filters by both person and theme, **When** they query
   the workspace, **Then** the results include only interactions that satisfy
   both conditions.

---

### User Story 3 - Repeatable Refreshes And Auditability (Priority: P3)

As a maintainer, I want each workspace refresh to be traceable and safe to rerun
so I can backfill, compare, and troubleshoot derived data over time.

**Why this priority**: Search results will only be trusted if the derivation
process is observable, reproducible, and separable from the source archive.

**Independent Test**: Can be fully tested by executing two refreshes over the
same bounded slice and confirming that the resulting workspace rows, run
metadata, and quality metrics remain internally consistent.

**Acceptance Scenarios**:

1. **Given** a completed refresh, **When** a maintainer inspects run metadata,
   **Then** they can identify the source scope, refresh time, and quality counts
   for the derived data.
2. **Given** a failed or partial refresh, **When** the maintainer reruns the
   same scope, **Then** the workspace does not retain ambiguous duplicate
   current-state records from the failed attempt.

### Edge Cases

- How does the workspace handle interactions that have no body text, no subject,
  or only system-generated content?
- How does the workspace handle low-confidence person mentions when multiple
  canonical people share the same name or alias?
- What happens when an interaction references people or themes that cannot be
  resolved confidently enough for search use?
- What happens when a rerun covers a previously processed time range with
  corrected entity overrides or updated source records?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create and maintain a dedicated derived workspace
  in the development catalog under the `nlpdata` schema.
- **FR-002**: The system MUST keep `nlpdata` logically separate from source
  archive tables so derived NLP outputs can be refreshed without mutating the
  canonical interaction or person records.
- **FR-003**: The system MUST produce a person-message linkage dataset that
  identifies which canonical people are connected to each interaction.
- **FR-004**: The person-message linkage dataset MUST distinguish direct
  participation from inferred textual references.
- **FR-005**: The system MUST preserve provenance for each derived linkage,
  including the source interaction and the refresh run that created it.
- **FR-006**: The system MUST produce a searchable theme-tag dataset for
  interactions, including confidence and evidence sufficient for reviewer
  inspection.
- **FR-007**: The system MUST provide a search-ready interaction dataset that
  combines derived search fields, person links, theme tags, time facets, and
  source interaction references in one queryable surface without duplicating the
  full source interaction text into `nlpdata`.
- **FR-007a**: The first rollout MUST define the search-ready interaction
  dataset at the message level; thread-level search documents are out of scope
  for this feature.
- **FR-008**: The system MUST record refresh run metadata, including scope,
  timing, row counts, and quality metrics, for every workspace refresh.
- **FR-009**: The system MUST support rerunning a previously processed scope
  without leaving multiple conflicting current-state records for the same
  interaction in the search workspace.
- **FR-010**: The system MUST reuse canonical people and their effective
  classifications from the source archive when deriving person-linked search
  data.
- **FR-011**: The system MUST exclude incomplete or below-threshold derived
  records from publication to `message_person_links`, `message_theme_tags`, and
  `message_search_docs`, while retaining enough run metadata to explain why they
  were suppressed.
- **FR-011a**: The system MUST either suppress or explicitly flag
  system-generated interactions and unresolved person or theme derivations so
  they do not silently appear as trusted search results.
- **FR-012**: The system MUST document the workspace contents, refresh contract,
  and validation expectations before the first deployment to the development
  catalog.

### Key Entities *(include if feature involves data)*

- **Interaction Mention**: A text span extracted from an interaction that may
  represent a person, contact identifier, or conversational topic and carries
  provenance back to the source interaction.
- **Person Message Link**: A derived relationship between a canonical person and
  an interaction, including role, confidence, and whether the link is explicit
  or inferred.
- **Theme Tag**: A derived topical label attached to an interaction or grouped
  conversation, including evidence and confidence for search and review.
- **Search Document**: A denormalized interaction record that combines message
  search fields, linked people, theme tags, time facets, and a source
  interaction reference for retrieval without duplicating the full source text.
- **Refresh Run**: A record of one workspace derivation execution, including the
  scope processed, counts produced, and validation metrics.

## Assumptions

- The development catalog remains the only in-scope target for the first rollout;
  production rollout is out of scope for this feature.
- Canonical people, interaction records, entity overrides, and effective entity
  classifications remain owned by the existing archive datasets and are consumed
  by `nlpdata` as inputs rather than redefined here.
- `graph-data` is a read-only upstream source; this repository owns `nlpdata`
  implementation and deployment.
- The search-ready workspace stores derived retrieval fields and source
  references rather than a second full-text copy of each interaction.
- The first implementation focuses on searchable derived data, not large-scale
  visualization.
- The first implementation defines search records at the message level only;
  thread-level rollups may be planned later.
- Search users need both explicit participant links and inferred textual links,
  but they also need provenance and confidence to judge weak matches.

## Documentation Impact *(mandatory)*

- **Docs to Update**: `README.md`, `AGENTS.md`, the feature spec at
  `specs/001-nlpdata-schema/spec.md`, and an ADR describing the workspace
  boundary and refresh model.
- **Behavior Change Summary**: Document the purpose of the `nlpdata` schema, the
  datasets it will contain, the expected refresh lifecycle, and how search users
  should interpret explicit links, inferred links, themes, and run metadata.
- **Local Test Plan**: Add or update local automated tests for derivation
  schemas, person-link confidence handling, theme tagging behavior, rerun safety,
  and search-document composition; run the relevant local test suite before any
  deployment.

## Decision Record Impact *(mandatory)*

- **ADR Required**: Yes
- **ADR Path**: `docs/adr/001-nlpdata-search-workspace.md`
- **Architectural Scope**: Introduces a new derived data boundary in the
  development catalog for NLP and search outputs, plus the refresh and
  provenance contract that governs how source archive data flows into it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can retrieve all interactions involving a chosen
  canonical person from the derived workspace for a 200-message validation slice
  without joining back to source tables manually.
- **SC-002**: For a curated validation set, at least 99% of explicit participant
  links and at least 85% of inferred person links are judged correct by manual
  review.
- **SC-003**: For a curated validation set of topical conversations, at least
  80% of returned theme tags are judged useful for narrowing search results.
- **SC-004**: A bounded refresh over 10,000 interactions completes in under 15
  minutes with run metadata, row counts, and validation metrics recorded for
  100% of produced derived datasets.
- **SC-005**: A rerun of the same bounded scope produces no duplicate
  current-state search records for the same interaction.
