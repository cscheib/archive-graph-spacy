# Contract: `personal_archive_dev.nlpdata` Tables

## Purpose

Define the v1 table-level contract for the derived NLP search workspace. These
contracts describe what each table guarantees to downstream search consumers and
quality reviewers.

If this schema is promoted into the managed Databricks contract system, these
tables should be represented as registry-backed logical schemas rather than
one-off DDL.

## Source Inputs

- `personal_archive_dev.gold.interactions`
- `personal_archive_dev.gold.persons`
- `personal_archive_dev.gold.entity_classification`
- `personal_archive_dev.memory.entity_overrides`

## Output Tables

### `nlpdata.nlp_runs`

- **Role**: Audit and refresh metadata
- **Required columns**:
  - `run_id`
  - `run_scope`
  - `status`
  - `started_at`
  - `completed_at`
  - `input_interaction_count`
  - `output_row_counts`
  - `quality_metrics`
- **Guarantees**:
  - One row per refresh run
  - Every downstream row can be tied back to one `run_id`

### `nlpdata.message_mentions`

- **Role**: Extracted message-level spans with provenance
- **Required columns**:
  - `mention_id`
  - `run_id`
  - `message_id`
  - `span_text`
  - `label`
  - `start_char`
  - `end_char`
  - `source_type`
  - `confidence`
- **Guarantees**:
  - Character offsets are valid within the analyzed message text for that run
  - Mentions remain evidence-bearing and are not the only search surface

### `nlpdata.message_person_links`

- **Role**: Canonical person-to-message relationships
- **Required columns**:
  - `link_id`
  - `run_id`
  - `message_id`
  - `person_id`
  - `role`
  - `link_origin`
  - `confidence`
  - `evidence_type`
  - `is_current`
- **Guarantees**:
  - `role` differentiates sender, recipient, and mentioned relationships
  - `link_origin` differentiates explicit vs inferred links
  - No duplicate current rows for the same `(message_id, person_id, role)`

### `nlpdata.message_theme_tags`

- **Role**: Searchable message-level themes
- **Required columns**:
  - `theme_tag_id`
  - `run_id`
  - `message_id`
  - `theme`
  - `confidence`
  - `evidence`
  - `source_method`
  - `is_current`
- **Guarantees**:
  - Themes are message-level in v1
  - Every current theme tag includes confidence and evidence

### `nlpdata.message_search_docs`

- **Role**: Denormalized retrieval surface
- **Required columns**:
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
- **Guarantees**:
  - One current search document per message
  - Search documents do not duplicate full source interaction text
  - Person and theme arrays are derived from current normalized tables

## Scope Rules

- All v1 contracts are message-level only.
- The workspace is dev-catalog only for the first rollout.
- Thread-level search documents are explicitly out of scope for this contract.

## Rerun Rules

- Bounded reruns must replace prior current-state records for the same logical
  keys within the processed scope.
- Historical run metadata may be retained, but current-state tables must not
  expose conflicting active rows for the same message.
- Refresh implementation should follow the existing managed derived-table
  conventions: overwrite for full rebuilds and explicit stale-state cleanup or
  temp-table swap when bounded reruns would otherwise leave conflicting current
  rows.
