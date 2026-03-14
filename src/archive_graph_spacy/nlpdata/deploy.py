"""Deploy local nlpdata artifacts into Databricks Delta tables."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .databricks import (
    DatabricksSqlClient,
    get_workspace_client,
    quote_sql_identifier,
    quote_sql_string_literal,
    validate_run_id,
)
from .models import BoundedPublishScope
from .runs import build_publish_diagnostics, classify_scope_overlap

DEFAULT_WAREHOUSE_ID = "4b799682f2bfd311"
DEFAULT_CATALOG = "personal_archive_dev"
DEFAULT_SCHEMA = "nlpdata"

CURRENT_STATE_TABLES = {
    "message_person_links",
    "person_person_edges",
    "phases",
    "phase_central_people",
    "phase_theme_summaries",
    "phase_pair_summaries",
    "phase_pair_evidence",
    "phase_representative_interactions",
    "message_theme_tags",
    "message_search_docs",
}

CURRENT_STATE_IDENTITY_COLUMNS = {
    "message_person_links": "message_id",
    "person_person_edges": "pair_id",
    "phases": "phase_id",
    "phase_central_people": "phase_id",
    "phase_theme_summaries": "phase_id",
    "phase_pair_summaries": "phase_id",
    "phase_pair_evidence": "phase_id",
    "phase_representative_interactions": "phase_id",
    "message_theme_tags": "message_id",
    "message_search_docs": "message_id",
}

PHASE_SCOPE_TABLES = {
    "phases",
    "phase_central_people",
    "phase_theme_summaries",
    "phase_pair_summaries",
    "phase_pair_evidence",
    "phase_representative_interactions",
}

FINALIZATION_REFERENCE_TABLES = {
    "phase_central_people": "phases",
    "phase_theme_summaries": "phases",
    "phase_pair_summaries": "phases",
    "phase_pair_evidence": "phases",
    "phase_representative_interactions": "phases",
}

TABLE_DDLS: dict[str, str] = {
    "nlp_runs": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.nlp_runs (
  run_id STRING,
  run_scope STRING,
  source_catalog STRING,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status STRING,
  input_interaction_count BIGINT,
  output_row_counts STRING,
  quality_metrics STRING,
  publish_diagnostics STRING
) USING DELTA
""".strip(),
    "message_mentions": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.message_mentions (
  mention_id STRING,
  run_id STRING,
  message_id STRING,
  source_interaction_id STRING,
  span_text STRING,
  label STRING,
  start_char INT,
  end_char INT,
  source_type STRING,
  confidence DOUBLE
) USING DELTA
""".strip(),
    "message_person_links": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.message_person_links (
  link_id STRING,
  run_id STRING,
  message_id STRING,
  person_id STRING,
  person_name STRING,
  role STRING,
  link_origin STRING,
  confidence DOUBLE,
  evidence_type STRING,
  evidence_value STRING,
  source_interaction_id STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "candidate_assertions": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.candidate_assertions (
  candidate_assertion_id STRING,
  run_id STRING,
  assertion_type STRING,
  subject_canonical_id STRING,
  proposed_claim STRING,
  evidence_refs ARRAY<STRING>,
  provenance_summary STRING,
  confidence_level DOUBLE,
  generation_scope STRING,
  generated_at TIMESTAMP,
  review_class STRING,
  promotion_class STRING
) USING DELTA
""".strip(),
    "candidate_assertions_summary": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.candidate_assertions_summary (
  run_id STRING,
  generation_scope STRING,
  emitted_candidate_count BIGINT,
  candidate_counts_by_type MAP<STRING, BIGINT>,
  suppressed_counts MAP<STRING, BIGINT>,
  example_candidate_ids ARRAY<STRING>,
  generated_at TIMESTAMP,
  reviewed_effect_counts MAP<STRING, BIGINT>
) USING DELTA
""".strip(),
    "reviewed_effects": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.reviewed_effects (
  run_id STRING,
  candidate_assertion_id STRING,
  assertion_type STRING,
  subject_canonical_id STRING,
  result STRING,
  reason_code STRING,
  details STRING
) USING DELTA
""".strip(),
    "person_person_edges": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.person_person_edges (
  pair_id STRING,
  person_a_id STRING,
  person_b_id STRING,
  run_id STRING,
  generation_scope STRING,
  strength_score DOUBLE,
  relationship_signal STRING,
  direct_evidence_count BIGINT,
  indirect_evidence_count BIGINT,
  strongest_evidence_ref STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "person_person_edge_evidence": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.person_person_edge_evidence (
  pair_evidence_id STRING,
  pair_id STRING,
  evidence_family STRING,
  source_ref STRING,
  contribution_score DOUBLE,
  rank_within_pair INT,
  message_ref STRING,
  theme_refs ARRAY<STRING>,
  provenance STRING
) USING DELTA
""".strip(),
    "phases": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phases (
  phase_id STRING,
  run_id STRING,
  generation_scope STRING,
  phase_index INT,
  start_at TIMESTAMP,
  end_at TIMESTAMP,
  interaction_count BIGINT,
  representative_interaction_ref STRING,
  boundary_reason STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "phase_central_people": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phase_central_people (
  phase_id STRING,
  run_id STRING,
  person_id STRING,
  rank INT,
  centrality_score DOUBLE,
  interaction_count BIGINT,
  evidence_ref STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "phase_theme_summaries": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phase_theme_summaries (
  phase_id STRING,
  run_id STRING,
  theme STRING,
  rank INT,
  theme_score DOUBLE,
  message_count BIGINT,
  evidence_ref STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "phase_pair_summaries": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phase_pair_summaries (
  phase_pair_id STRING,
  phase_id STRING,
  pair_id STRING,
  run_id STRING,
  pair_rank INT,
  activity_score DOUBLE,
  relationship_signal STRING,
  evidence_count BIGINT,
  strongest_evidence_ref STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "phase_pair_evidence": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phase_pair_evidence (
  phase_pair_evidence_id STRING,
  phase_pair_id STRING,
  phase_id STRING,
  pair_id STRING,
  run_id STRING,
  source_ref STRING,
  message_ref STRING,
  evidence_family STRING,
  rank_within_phase_pair INT,
  contribution_score DOUBLE,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "phase_representative_interactions": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phase_representative_interactions (
  phase_id STRING,
  run_id STRING,
  interaction_ref STRING,
  rank INT,
  selection_reason STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "phase_diagnostics": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.phase_diagnostics (
  run_id STRING,
  phase_id STRING,
  diagnostic_type STRING,
  result STRING,
  reason_code STRING,
  sample_ref STRING,
  details STRING
) USING DELTA
""".strip(),
    "message_theme_tags": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.message_theme_tags (
  theme_tag_id STRING,
  run_id STRING,
  message_id STRING,
  theme STRING,
  confidence DOUBLE,
  evidence STRING,
  source_method STRING,
  source_interaction_id STRING,
  is_current BOOLEAN
) USING DELTA
""".strip(),
    "message_search_docs": """
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.message_search_docs (
  message_id STRING,
  run_id STRING,
  source_interaction_id STRING,
  source_type STRING,
  timestamp TIMESTAMP,
  subject_terms ARRAY<STRING>,
  body_terms ARRAY<STRING>,
  linked_person_ids ARRAY<STRING>,
  linked_person_names ARRAY<STRING>,
  explicit_person_ids ARRAY<STRING>,
  inferred_person_ids ARRAY<STRING>,
  theme_labels ARRAY<STRING>,
  time_facets MAP<STRING, STRING>,
  is_current BOOLEAN
) USING DELTA
""".strip(),
}

TABLE_COLUMN_TYPES: dict[str, dict[str, str]] = {
    "nlp_runs": {
        "run_id": "STRING",
        "run_scope": "STRING",
        "source_catalog": "STRING",
        "started_at": "TIMESTAMP",
        "completed_at": "TIMESTAMP",
        "status": "STRING",
        "input_interaction_count": "BIGINT",
        "output_row_counts": "STRING",
        "quality_metrics": "STRING",
        "publish_diagnostics": "STRING",
    },
    "message_mentions": {
        "mention_id": "STRING",
        "run_id": "STRING",
        "message_id": "STRING",
        "source_interaction_id": "STRING",
        "span_text": "STRING",
        "label": "STRING",
        "start_char": "INT",
        "end_char": "INT",
        "source_type": "STRING",
        "confidence": "DOUBLE",
    },
    "message_person_links": {
        "link_id": "STRING",
        "run_id": "STRING",
        "message_id": "STRING",
        "person_id": "STRING",
        "person_name": "STRING",
        "role": "STRING",
        "link_origin": "STRING",
        "confidence": "DOUBLE",
        "evidence_type": "STRING",
        "evidence_value": "STRING",
        "source_interaction_id": "STRING",
        "is_current": "BOOLEAN",
    },
    "candidate_assertions": {
        "candidate_assertion_id": "STRING",
        "run_id": "STRING",
        "assertion_type": "STRING",
        "subject_canonical_id": "STRING",
        "proposed_claim": "STRING",
        "evidence_refs": "ARRAY<STRING>",
        "provenance_summary": "STRING",
        "confidence_level": "DOUBLE",
        "generation_scope": "STRING",
        "generated_at": "TIMESTAMP",
        "review_class": "STRING",
        "promotion_class": "STRING",
    },
    "candidate_assertions_summary": {
        "run_id": "STRING",
        "generation_scope": "STRING",
        "emitted_candidate_count": "BIGINT",
        "candidate_counts_by_type": "MAP<STRING, BIGINT>",
        "suppressed_counts": "MAP<STRING, BIGINT>",
        "example_candidate_ids": "ARRAY<STRING>",
        "generated_at": "TIMESTAMP",
        "reviewed_effect_counts": "MAP<STRING, BIGINT>",
    },
    "reviewed_effects": {
        "run_id": "STRING",
        "candidate_assertion_id": "STRING",
        "assertion_type": "STRING",
        "subject_canonical_id": "STRING",
        "result": "STRING",
        "reason_code": "STRING",
        "details": "STRING",
    },
    "person_person_edges": {
        "pair_id": "STRING",
        "person_a_id": "STRING",
        "person_b_id": "STRING",
        "run_id": "STRING",
        "generation_scope": "STRING",
        "strength_score": "DOUBLE",
        "relationship_signal": "STRING",
        "direct_evidence_count": "BIGINT",
        "indirect_evidence_count": "BIGINT",
        "strongest_evidence_ref": "STRING",
        "is_current": "BOOLEAN",
    },
    "person_person_edge_evidence": {
        "pair_evidence_id": "STRING",
        "pair_id": "STRING",
        "evidence_family": "STRING",
        "source_ref": "STRING",
        "contribution_score": "DOUBLE",
        "rank_within_pair": "INT",
        "message_ref": "STRING",
        "theme_refs": "ARRAY<STRING>",
        "provenance": "STRING",
    },
    "phases": {
        "phase_id": "STRING",
        "run_id": "STRING",
        "generation_scope": "STRING",
        "phase_index": "INT",
        "start_at": "TIMESTAMP",
        "end_at": "TIMESTAMP",
        "interaction_count": "BIGINT",
        "representative_interaction_ref": "STRING",
        "boundary_reason": "STRING",
        "is_current": "BOOLEAN",
    },
    "phase_central_people": {
        "phase_id": "STRING",
        "run_id": "STRING",
        "person_id": "STRING",
        "rank": "INT",
        "centrality_score": "DOUBLE",
        "interaction_count": "BIGINT",
        "evidence_ref": "STRING",
        "is_current": "BOOLEAN",
    },
    "phase_theme_summaries": {
        "phase_id": "STRING",
        "run_id": "STRING",
        "theme": "STRING",
        "rank": "INT",
        "theme_score": "DOUBLE",
        "message_count": "BIGINT",
        "evidence_ref": "STRING",
        "is_current": "BOOLEAN",
    },
    "phase_pair_summaries": {
        "phase_pair_id": "STRING",
        "phase_id": "STRING",
        "pair_id": "STRING",
        "run_id": "STRING",
        "pair_rank": "INT",
        "activity_score": "DOUBLE",
        "relationship_signal": "STRING",
        "evidence_count": "BIGINT",
        "strongest_evidence_ref": "STRING",
        "is_current": "BOOLEAN",
    },
    "phase_pair_evidence": {
        "phase_pair_evidence_id": "STRING",
        "phase_pair_id": "STRING",
        "phase_id": "STRING",
        "pair_id": "STRING",
        "run_id": "STRING",
        "source_ref": "STRING",
        "message_ref": "STRING",
        "evidence_family": "STRING",
        "rank_within_phase_pair": "INT",
        "contribution_score": "DOUBLE",
        "is_current": "BOOLEAN",
    },
    "phase_representative_interactions": {
        "phase_id": "STRING",
        "run_id": "STRING",
        "interaction_ref": "STRING",
        "rank": "INT",
        "selection_reason": "STRING",
        "is_current": "BOOLEAN",
    },
    "phase_diagnostics": {
        "run_id": "STRING",
        "phase_id": "STRING",
        "diagnostic_type": "STRING",
        "result": "STRING",
        "reason_code": "STRING",
        "sample_ref": "STRING",
        "details": "STRING",
    },
    "message_theme_tags": {
        "theme_tag_id": "STRING",
        "run_id": "STRING",
        "message_id": "STRING",
        "theme": "STRING",
        "confidence": "DOUBLE",
        "evidence": "STRING",
        "source_method": "STRING",
        "source_interaction_id": "STRING",
        "is_current": "BOOLEAN",
    },
    "message_search_docs": {
        "message_id": "STRING",
        "run_id": "STRING",
        "source_interaction_id": "STRING",
        "source_type": "STRING",
        "timestamp": "TIMESTAMP",
        "subject_terms": "ARRAY<STRING>",
        "body_terms": "ARRAY<STRING>",
        "linked_person_ids": "ARRAY<STRING>",
        "linked_person_names": "ARRAY<STRING>",
        "explicit_person_ids": "ARRAY<STRING>",
        "inferred_person_ids": "ARRAY<STRING>",
        "theme_labels": "ARRAY<STRING>",
        "time_facets": "MAP<STRING, STRING>",
        "is_current": "BOOLEAN",
    },
}

INSERT_SELECTS: dict[str, str] = {
    "nlp_runs": """
INSERT INTO {catalog}.{schema}.nlp_runs
SELECT
  run_id,
  run_scope,
  source_catalog,
  CAST(started_at AS TIMESTAMP),
  CAST(completed_at AS TIMESTAMP),
  status,
  CAST(input_interaction_count AS BIGINT),
  to_json(output_row_counts),
  to_json(quality_metrics),
  to_json(publish_diagnostics)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "message_mentions": """
INSERT INTO {catalog}.{schema}.message_mentions
SELECT
  mention_id,
  run_id,
  message_id,
  source_interaction_id,
  span_text,
  label,
  CAST(start_char AS INT),
  CAST(end_char AS INT),
  source_type,
  CAST(confidence AS DOUBLE)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "message_person_links": """
INSERT INTO {catalog}.{schema}.message_person_links
SELECT
  link_id,
  run_id,
  message_id,
  person_id,
  person_name,
  role,
  link_origin,
  CAST(confidence AS DOUBLE),
  evidence_type,
  evidence_value,
  source_interaction_id,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "candidate_assertions": """
INSERT INTO {catalog}.{schema}.candidate_assertions
SELECT
  candidate_assertion_id,
  run_id,
  assertion_type,
  subject_canonical_id,
  proposed_claim,
  from_json(to_json(evidence_refs), 'array<string>'),
  provenance_summary,
  CAST(confidence_level AS DOUBLE),
  generation_scope,
  CAST(generated_at AS TIMESTAMP),
  review_class,
  promotion_class
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "candidate_assertions_summary": """
INSERT INTO {catalog}.{schema}.candidate_assertions_summary
SELECT
  run_id,
  generation_scope,
  CAST(emitted_candidate_count AS BIGINT),
  from_json(to_json(candidate_counts_by_type), 'map<string,bigint>'),
  from_json(to_json(suppressed_counts), 'map<string,bigint>'),
  from_json(to_json(example_candidate_ids), 'array<string>'),
  CAST(generated_at AS TIMESTAMP),
  from_json(to_json(reviewed_effect_counts), 'map<string,bigint>')
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "reviewed_effects": """
INSERT INTO {catalog}.{schema}.reviewed_effects
SELECT
  run_id,
  candidate_assertion_id,
  assertion_type,
  subject_canonical_id,
  result,
  reason_code,
  details
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "person_person_edges": """
INSERT INTO {catalog}.{schema}.person_person_edges
SELECT
  pair_id,
  person_a_id,
  person_b_id,
  run_id,
  generation_scope,
  CAST(strength_score AS DOUBLE),
  relationship_signal,
  CAST(direct_evidence_count AS BIGINT),
  CAST(indirect_evidence_count AS BIGINT),
  strongest_evidence_ref,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "person_person_edge_evidence": """
INSERT INTO {catalog}.{schema}.person_person_edge_evidence
SELECT
  pair_evidence_id,
  pair_id,
  evidence_family,
  source_ref,
  CAST(contribution_score AS DOUBLE),
  CAST(rank_within_pair AS INT),
  message_ref,
  from_json(to_json(theme_refs), 'array<string>'),
  provenance
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phases": """
INSERT INTO {catalog}.{schema}.phases
SELECT
  phase_id,
  run_id,
  generation_scope,
  CAST(phase_index AS INT),
  CAST(start_at AS TIMESTAMP),
  CAST(end_at AS TIMESTAMP),
  CAST(interaction_count AS BIGINT),
  representative_interaction_ref,
  boundary_reason,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phase_central_people": """
INSERT INTO {catalog}.{schema}.phase_central_people
SELECT
  phase_id,
  run_id,
  person_id,
  CAST(rank AS INT),
  CAST(centrality_score AS DOUBLE),
  CAST(interaction_count AS BIGINT),
  evidence_ref,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phase_theme_summaries": """
INSERT INTO {catalog}.{schema}.phase_theme_summaries
SELECT
  phase_id,
  run_id,
  theme,
  CAST(rank AS INT),
  CAST(theme_score AS DOUBLE),
  CAST(message_count AS BIGINT),
  evidence_ref,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phase_pair_summaries": """
INSERT INTO {catalog}.{schema}.phase_pair_summaries
SELECT
  phase_pair_id,
  phase_id,
  pair_id,
  run_id,
  CAST(pair_rank AS INT),
  CAST(activity_score AS DOUBLE),
  relationship_signal,
  CAST(evidence_count AS BIGINT),
  strongest_evidence_ref,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phase_pair_evidence": """
INSERT INTO {catalog}.{schema}.phase_pair_evidence
SELECT
  phase_pair_evidence_id,
  phase_pair_id,
  phase_id,
  pair_id,
  run_id,
  source_ref,
  message_ref,
  evidence_family,
  CAST(rank_within_phase_pair AS INT),
  CAST(contribution_score AS DOUBLE),
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phase_representative_interactions": """
INSERT INTO {catalog}.{schema}.phase_representative_interactions
SELECT
  phase_id,
  run_id,
  interaction_ref,
  CAST(rank AS INT),
  selection_reason,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "phase_diagnostics": """
INSERT INTO {catalog}.{schema}.phase_diagnostics
SELECT
  run_id,
  phase_id,
  diagnostic_type,
  result,
  reason_code,
  sample_ref,
  details
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "message_theme_tags": """
INSERT INTO {catalog}.{schema}.message_theme_tags
SELECT
  theme_tag_id,
  run_id,
  message_id,
  theme,
  CAST(confidence AS DOUBLE),
  evidence,
  source_method,
  source_interaction_id,
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
    "message_search_docs": """
INSERT INTO {catalog}.{schema}.message_search_docs
SELECT
  message_id,
  run_id,
  source_interaction_id,
  source_type,
  CAST(timestamp AS TIMESTAMP),
  from_json(to_json(subject_terms), 'array<string>'),
  from_json(to_json(body_terms), 'array<string>'),
  from_json(to_json(linked_person_ids), 'array<string>'),
  from_json(to_json(linked_person_names), 'array<string>'),
  from_json(to_json(explicit_person_ids), 'array<string>'),
  from_json(to_json(inferred_person_ids), 'array<string>'),
  from_json(to_json(theme_labels), 'array<string>'),
  from_json(to_json(time_facets), 'map<string,string>'),
  CAST(is_current AS BOOLEAN)
FROM read_files({remote_path}, format => 'json')
""".strip(),
}


def _run_databricks_fs(profile: str | None, args: list[str]) -> None:
    command = ["databricks", "fs", *args]
    if profile:
        command.extend(["--profile", profile])
    subprocess.run(command, check=True, capture_output=True, text=True)


def stage_payload_directory(local_dir: Path, run_id: str, profile: str | None = None) -> str:
    run_id = validate_run_id(run_id)
    remote_dir = f"dbfs:/tmp/archive_graph_spacy/nlpdata/{run_id}"
    _run_databricks_fs(profile, ["cp", "-r", str(local_dir), remote_dir, "--overwrite"])
    return remote_dir


def cleanup_staged_directory(remote_dir: str, profile: str | None = None) -> None:
    _run_databricks_fs(profile, ["rm", "-r", remote_dir])


def _schema_sql(catalog: str, schema: str) -> str:
    return f"CREATE SCHEMA IF NOT EXISTS {quote_sql_identifier(catalog)}.{quote_sql_identifier(schema)}"


def missing_contract_columns(
    table_name: str,
    existing_columns: set[str],
) -> list[tuple[str, str]]:
    return [
        (column_name, column_type)
        for column_name, column_type in TABLE_COLUMN_TYPES[table_name].items()
        if column_name not in existing_columns
    ]


def _add_missing_columns_sql(
    catalog: str,
    schema: str,
    table_name: str,
    existing_columns: set[str],
) -> str | None:
    missing_columns = missing_contract_columns(table_name, existing_columns)
    if not missing_columns:
        return None
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier(table_name),
        )
    )
    add_columns_sql = ", ".join(
        f"{quote_sql_identifier(column_name)} {column_type}"
        for column_name, column_type in missing_columns
    )
    return f"ALTER TABLE {qualified_table} ADD COLUMNS ({add_columns_sql})"


def _show_columns_sql(catalog: str, schema: str, table_name: str) -> str:
    return (
        f"SHOW COLUMNS IN "
        f"{quote_sql_identifier(catalog)}.{quote_sql_identifier(schema)}.{quote_sql_identifier(table_name)}"
    )


def _deactivate_current_rows_sql(
    catalog: str,
    schema: str,
    table_name: str,
    remote_path: str,
    *,
    run_scope: str | None = None,
) -> str:
    if table_name in PHASE_SCOPE_TABLES:
        if not run_scope:
            raise ValueError("run_scope is required for phase-scope finalization")
        return _deactivate_phase_scope_rows_sql(catalog, schema, table_name, run_scope)
    identity_column = CURRENT_STATE_IDENTITY_COLUMNS[table_name]
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier(table_name),
        )
    )
    return f"""
UPDATE {qualified_table}
SET is_current = false
WHERE is_current = true
  AND {quote_sql_identifier(identity_column)} IN (
    SELECT DISTINCT {quote_sql_identifier(identity_column)}
    FROM read_files({quote_sql_string_literal(remote_path)}, format => 'json')
  )
""".strip()


def _deactivate_phase_scope_rows_sql(catalog: str, schema: str, table_name: str, run_scope: str) -> str:
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier(table_name),
        )
    )
    qualified_phases = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier("phases"),
        )
    )
    if table_name == "phases":
        return f"""
UPDATE {qualified_table}
SET is_current = false
WHERE is_current = true
  AND generation_scope = {quote_sql_string_literal(run_scope)}
""".strip()
    return f"""
UPDATE {qualified_table}
SET is_current = false
WHERE is_current = true
  AND phase_id IN (
    SELECT DISTINCT phase_id
    FROM {qualified_phases}
    WHERE is_current = true
      AND generation_scope = {quote_sql_string_literal(run_scope)}
  )
""".strip()


def _deactivate_all_current_phase_rows_sql(catalog: str, schema: str, table_name: str) -> str:
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier(table_name),
        )
    )
    qualified_phases = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier("phases"),
        )
    )
    if table_name == "phases":
        return f"""
UPDATE {qualified_table}
SET is_current = false
WHERE is_current = true
""".strip()
    return f"""
UPDATE {qualified_table}
SET is_current = false
WHERE is_current = true
  AND phase_id IN (
    SELECT DISTINCT phase_id
    FROM {qualified_phases}
    WHERE is_current = true
  )
""".strip()


def _activate_staged_rows_sql(catalog: str, schema: str, table_name: str, run_id: str, remote_path: str) -> str:
    identity_column = CURRENT_STATE_IDENTITY_COLUMNS[table_name]
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier(table_name),
        )
    )
    return f"""
UPDATE {qualified_table}
SET is_current = true
WHERE run_id = {quote_sql_string_literal(run_id)}
  AND {quote_sql_identifier(identity_column)} IN (
    SELECT DISTINCT {quote_sql_identifier(identity_column)}
    FROM read_files({quote_sql_string_literal(remote_path)}, format => 'json')
  )
""".strip()


def _finalization_remote_path(remote_dir: str, table_name: str) -> str:
    reference_table = FINALIZATION_REFERENCE_TABLES.get(table_name, table_name)
    return f"{remote_dir}/{reference_table}.jsonl"


def _artifact_filename(table_name: str) -> str:
    if table_name == "candidate_assertions_summary":
        return f"{table_name}.json"
    return f"{table_name}.jsonl"


def _artifact_remote_path(remote_dir: str, table_name: str) -> str:
    return f"{remote_dir}/{_artifact_filename(table_name)}"


def _delete_matching_candidate_assertions_sql(
    catalog: str,
    schema: str,
    *,
    source_relation_sql: str,
) -> str:
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier("candidate_assertions"),
        )
    )
    return f"""
DELETE FROM {qualified_table}
WHERE candidate_assertion_id IN (
  SELECT DISTINCT candidate_assertion_id
  FROM {source_relation_sql}
)
""".strip()


def _update_run_diagnostics_sql(catalog: str, schema: str, run_id: str, diagnostics: dict[str, object]) -> str:
    qualified_table = ".".join(
        (
            quote_sql_identifier(catalog),
            quote_sql_identifier(schema),
            quote_sql_identifier("nlp_runs"),
        )
    )
    return f"""
UPDATE {qualified_table}
SET publish_diagnostics = {quote_sql_string_literal(json.dumps(diagnostics, sort_keys=True))}
WHERE run_id = {quote_sql_string_literal(run_id)}
""".strip()


def _staged_insert_sql(table_name: str, *, catalog: str, schema: str, remote_path: str) -> str:
    statement = INSERT_SELECTS[table_name].format(
        catalog=catalog,
        schema=schema,
        remote_path=quote_sql_string_literal(remote_path),
    )
    if table_name not in CURRENT_STATE_TABLES:
        return statement
    replaced = statement.replace("CAST(is_current AS BOOLEAN)", "false")
    if replaced == statement:
        raise RuntimeError(
            "Expected to replace 'CAST(is_current AS BOOLEAN)' when staging inserts "
            f"for current-state table '{table_name}', but the pattern was not found. "
            "The INSERT_SELECTS template may have changed."
        )
    return replaced


def _try_persist_publish_diagnostics(
    client: DatabricksSqlClient,
    *,
    catalog: str,
    schema: str,
    run_id: str,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    try:
        client.execute(_update_run_diagnostics_sql(catalog, schema, run_id, diagnostics))
        return diagnostics
    except Exception as exc:
        enriched = dict(diagnostics)
        enriched["diagnostics_persist_error"] = str(exc)
        return enriched


def _finalize_deploy_result(
    *,
    client: DatabricksSqlClient,
    catalog: str,
    schema: str,
    run_id: str,
    remote_dir: str,
    warehouse_id: str,
    profile: str | None,
    cleanup_remote: bool,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diagnostics = _try_persist_publish_diagnostics(
        client,
        catalog=catalog,
        schema=schema,
        run_id=run_id,
        diagnostics=diagnostics,
    )
    if cleanup_remote:
        cleanup_staged_directory(remote_dir, profile=profile)
    return {
        "catalog": catalog,
        "schema": schema,
        "remote_dir": remote_dir,
        "warehouse_id": warehouse_id,
        "publish_diagnostics": diagnostics,
    }


def _load_jsonl_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _load_run_scope(local_dir: Path, run_id: str) -> str:
    run_rows = _load_jsonl_rows(local_dir / "nlp_runs.jsonl")
    for row in run_rows:
        if row.get("run_id") == run_id and isinstance(row.get("run_scope"), str):
            return str(row["run_scope"])
    return str(local_dir)


def _collect_bounded_publish_scope(
    local_dir: Path,
    *,
    run_id: str,
    active_scope_message_ids: tuple[tuple[str, ...], ...],
) -> BoundedPublishScope:
    message_ids: set[str] = set()
    identity_values: set[str] = set()
    affected_tables: list[str] = []
    cached_rows: dict[str, list[dict[str, object]]] = {}
    run_scope = _load_run_scope(local_dir, run_id)

    def _rows_for(table_name: str) -> list[dict[str, object]]:
        rows = cached_rows.get(table_name)
        if rows is None:
            rows = _load_jsonl_rows(local_dir / f"{table_name}.jsonl")
            cached_rows[table_name] = rows
        return rows

    for table_name in CURRENT_STATE_TABLES:
        rows = _rows_for(table_name)
        identity_column = CURRENT_STATE_IDENTITY_COLUMNS[table_name]
        table_identity_values = {
            str(row[identity_column])
            for row in rows
            if row.get("run_id") == run_id and row.get(identity_column)
        }
        if not table_identity_values and table_name in FINALIZATION_REFERENCE_TABLES:
            reference_rows = _rows_for(FINALIZATION_REFERENCE_TABLES[table_name])
            table_identity_values = {
                str(row[identity_column])
                for row in reference_rows
                if row.get("run_id") == run_id and row.get(identity_column)
            }
        if table_identity_values:
            affected_tables.append(table_name)
            identity_values.update(f"{table_name}:{value}" for value in table_identity_values)
            if identity_column == "message_id":
                message_ids.update(table_identity_values)
        elif table_name in PHASE_SCOPE_TABLES and run_scope:
            affected_tables.append(table_name)
    affected_message_ids = tuple(sorted(message_ids))
    affected_identity_values = tuple(sorted(identity_values))
    overlap_scope_ids = tuple(sorted(set(affected_message_ids) | set(affected_identity_values)))
    return BoundedPublishScope(
        run_id=run_id,
        run_scope=run_scope,
        affected_message_ids=affected_message_ids,
        affected_identity_values=affected_identity_values,
        affected_tables=tuple(sorted(affected_tables)),
        overlap_class=classify_scope_overlap(overlap_scope_ids, active_scope_message_ids),
    )


def deploy_staged_payload(
    local_dir: Path,
    *,
    run_id: str,
    profile: str | None = None,
    catalog: str = DEFAULT_CATALOG,
    schema: str = DEFAULT_SCHEMA,
    warehouse_id: str = DEFAULT_WAREHOUSE_ID,
    cleanup_remote: bool = True,
    active_scope_message_ids: tuple[tuple[str, ...], ...] = (),
) -> dict[str, object]:
    run_id = validate_run_id(run_id)
    workspace_client = get_workspace_client(profile)
    client = DatabricksSqlClient(workspace_client, warehouse_id=warehouse_id)
    remote_dir = stage_payload_directory(local_dir, run_id, profile=profile)
    publish_scope = _collect_bounded_publish_scope(
        local_dir,
        run_id=run_id,
        active_scope_message_ids=active_scope_message_ids,
    )
    if publish_scope.overlap_class == "overlapping_scope":
        diagnostics = build_publish_diagnostics(
            scope=publish_scope,
            publish_stage="staged",
            publish_outcome="failed",
            recovery_action="serialize_overlapping_scope",
            staged_path=remote_dir,
            finalized_tables=(),
            failed_tables=tuple(publish_scope.affected_tables),
            manual_intervention_required=True,
        ).to_record()
        if cleanup_remote:
            cleanup_staged_directory(remote_dir, profile=profile)
        return _finalize_deploy_result(
            client=client,
            catalog=catalog,
            schema=schema,
            run_id=run_id,
            diagnostics=diagnostics,
            remote_dir=remote_dir,
            warehouse_id=warehouse_id,
            profile=profile,
            cleanup_remote=False,
        )
    quoted_catalog = quote_sql_identifier(catalog)
    quoted_schema = quote_sql_identifier(schema)
    publish_stage = "staged"
    finalized_tables: list[str] = []
    failed_tables: list[str] = []
    recovery_action = "rerun_same_scope"
    manual_intervention_required = False
    error_detail = ""
    try:
        client.execute(_schema_sql(catalog, schema))
        for table_name, ddl in TABLE_DDLS.items():
            client.execute(ddl.format(catalog=quoted_catalog, schema=quoted_schema))
            existing_column_rows = client.fetch_all(_show_columns_sql(catalog, schema, table_name))
            existing_columns = {
                str(row.get("col_name") or next(iter(row.values()), ""))
                for row in existing_column_rows
            }
            alter_sql = _add_missing_columns_sql(catalog, schema, table_name, existing_columns)
            if alter_sql is not None:
                client.execute(alter_sql)
            remote_path = _artifact_remote_path(remote_dir, table_name)
            if table_name == "candidate_assertions":
                client.execute(
                    _delete_matching_candidate_assertions_sql(
                        catalog,
                        schema,
                        source_relation_sql=f"read_files({quote_sql_string_literal(remote_path)}, format => 'json')",
                    )
                )
            client.execute(
                _staged_insert_sql(
                    table_name,
                    catalog=quoted_catalog,
                    schema=quoted_schema,
                    remote_path=remote_path,
                )
            )
        for table_name in publish_scope.affected_tables:
            deactivate_remote_path = _finalization_remote_path(remote_dir, table_name)
            activate_remote_path = f"{remote_dir}/{table_name}.jsonl"
            publish_stage = "finalizing"
            client.execute(
                _deactivate_current_rows_sql(
                    catalog,
                    schema,
                    table_name,
                    deactivate_remote_path,
                    run_scope=publish_scope.run_scope,
                )
            )
            client.execute(
                _activate_staged_rows_sql(
                    catalog,
                    schema,
                    table_name,
                    run_id,
                    activate_remote_path,
                )
            )
            finalized_tables.append(table_name)
        publish_stage = "finalized"
        publish_outcome = "finalized"
        recovery_action = "none"
    except Exception as exc:
        failed_tables = [table for table in publish_scope.affected_tables if table not in finalized_tables]
        manual_intervention_required = (
            not (publish_scope.affected_identity_values or publish_scope.affected_message_ids)
            or publish_stage != "finalizing"
        )
        publish_outcome = "partial" if finalized_tables else "failed"
        recovery_action = "manual_intervention" if manual_intervention_required else "rerun_same_scope"
        error_detail = str(exc)
    diagnostics = build_publish_diagnostics(
        scope=publish_scope,
        publish_stage=publish_stage,
        publish_outcome=publish_outcome,
        recovery_action=recovery_action,
        staged_path=remote_dir,
        finalized_tables=tuple(finalized_tables),
        failed_tables=tuple(failed_tables),
        manual_intervention_required=manual_intervention_required,
    ).to_record()
    if error_detail:
        diagnostics["error_detail"] = error_detail
    return _finalize_deploy_result(
        client=client,
        catalog=catalog,
        schema=schema,
        run_id=run_id,
        diagnostics=diagnostics,
        remote_dir=remote_dir,
        warehouse_id=warehouse_id,
        profile=profile,
        cleanup_remote=cleanup_remote,
    )
