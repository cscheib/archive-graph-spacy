# Data Model: NLP Search Workspace

## Overview

The `personal_archive_dev.nlpdata` schema stores derived, message-level search
artifacts sourced from canonical archive data. Tables are split between
normalized evidence-bearing datasets and a denormalized search surface.

## Entities

### Refresh Run

- **Purpose**: Tracks one derivation execution for auditability and rerun safety.
- **Primary fields**:
  - `run_id`
  - `run_scope`
  - `source_catalog`
  - `started_at`
  - `completed_at`
  - `status`
  - `input_interaction_count`
  - `output_row_counts`
  - `quality_metrics`
- **Validation rules**:
  - `run_id` is unique.
  - `status` is one of `started`, `completed`, `failed`.
  - `completed_at` is required when `status = completed`.
- **State transitions**:
  - `started` -> `completed`
  - `started` -> `failed`

### Interaction Mention

- **Purpose**: Stores extracted spans from a source interaction for people,
  identifiers, or themes.
- **Primary fields**:
  - `mention_id`
  - `run_id`
  - `message_id`
  - `source_interaction_id`
  - `span_text`
  - `label`
  - `start_char`
  - `end_char`
  - `source_type`
  - `confidence`
- **Validation rules**:
  - `message_id` and `run_id` are required.
  - `start_char < end_char`.
  - Character offsets are scoped to the analyzed interaction text for that run.

### Person Message Link

- **Purpose**: Represents one canonical person’s relationship to a message.
- **Primary fields**:
  - `link_id`
  - `run_id`
  - `message_id`
  - `person_id`
  - `role`
  - `link_origin`
  - `confidence`
  - `evidence_type`
  - `source_interaction_id`
  - `is_current`
- **Validation rules**:
  - `role` distinguishes `sender`, `recipient`, or `mentioned`.
  - `link_origin` distinguishes `explicit` from `inferred`.
  - Only one current row per `(message_id, person_id, role)` for a given scope.
- **Relationships**:
  - Many links belong to one `Refresh Run`.
  - Many links can reference one canonical person.
  - Many links can reference one message.

### Theme Tag

- **Purpose**: Attaches a searchable topic label to a message.
- **Primary fields**:
  - `theme_tag_id`
  - `run_id`
  - `message_id`
  - `theme`
  - `confidence`
  - `evidence`
  - `source_method`
  - `is_current`
- **Validation rules**:
  - `theme` is required.
  - `confidence` is required for all current rows.
  - Only one current row per `(message_id, theme)` for a given scope.

### Search Document

- **Purpose**: Denormalized search-ready record for one message.
- **Primary fields**:
  - `message_id`
  - `run_id`
  - `source_interaction_id`
  - `source_type`
  - `timestamp`
  - `subject_terms`
  - `body_terms`
  - `linked_person_ids`
  - `linked_person_names`
  - `explicit_person_ids`
  - `inferred_person_ids`
  - `theme_labels`
  - `time_facets`
  - `is_current`
- **Validation rules**:
  - `message_id` is unique among current search documents for a processed scope.
  - Full source interaction text is not duplicated into this entity.
  - `linked_person_ids` and `theme_labels` are derived from current normalized
    link/tag rows for the same run or scope.

## Relationships

- A `Refresh Run` produces many `Interaction Mention`, `Person Message Link`,
  `Theme Tag`, and `Search Document` rows.
- A `Search Document` is derived from one source message and summarizes many
  `Person Message Link` and `Theme Tag` rows.
- `Person Message Link` and `Theme Tag` rows remain the source of truth for
  evidence and quality review; `Search Document` is the retrieval surface.

## Identity And Uniqueness

- `run_id` uniquely identifies one derivation execution.
- `message_id` remains the stable source interaction key for all message-level
  records.
- Current-state uniqueness is enforced at:
  - one current search document per `message_id`
  - one current person link per `(message_id, person_id, role)`
  - one current theme tag per `(message_id, theme)`

## Lifecycle Notes

- Rerunning a processed scope supersedes prior current-state rows for the same
  logical keys.
- Failed runs may retain audit metadata, but they do not leave multiple current
  search records active for the same message.
