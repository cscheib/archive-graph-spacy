"""Deploy local nlpdata artifacts into Databricks Delta tables."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .databricks import DatabricksSqlClient, get_workspace_client, quote_sql_identifier

DEFAULT_WAREHOUSE_ID = "4b799682f2bfd311"
DEFAULT_CATALOG = "personal_archive_dev"
DEFAULT_SCHEMA = "nlpdata"

CURRENT_STATE_TABLES = {
    "message_person_links",
    "message_theme_tags",
    "message_search_docs",
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
  quality_metrics STRING
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
  to_json(quality_metrics)
FROM read_files('{remote_path}', format => 'json')
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
FROM read_files('{remote_path}', format => 'json')
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
FROM read_files('{remote_path}', format => 'json')
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
FROM read_files('{remote_path}', format => 'json')
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
FROM read_files('{remote_path}', format => 'json')
""".strip(),
}


def _run_databricks_fs(profile: str | None, args: list[str]) -> None:
    command = ["databricks", "fs", *args]
    if profile:
        command.extend(["--profile", profile])
    subprocess.run(command, check=True, capture_output=True, text=True)


def stage_payload_directory(local_dir: Path, run_id: str, profile: str | None = None) -> str:
    remote_dir = f"dbfs:/tmp/archive_graph_spacy/nlpdata/{run_id}"
    _run_databricks_fs(profile, ["cp", "-r", str(local_dir), remote_dir, "--overwrite"])
    return remote_dir


def cleanup_staged_directory(remote_dir: str, profile: str | None = None) -> None:
    _run_databricks_fs(profile, ["rm", "-r", remote_dir])


def _schema_sql(catalog: str, schema: str) -> str:
    return f"CREATE SCHEMA IF NOT EXISTS {quote_sql_identifier(catalog)}.{quote_sql_identifier(schema)}"


def _deactivate_current_rows_sql(catalog: str, schema: str, table_name: str, remote_path: str) -> str:
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
  AND message_id IN (
    SELECT DISTINCT message_id
    FROM read_files('{remote_path}', format => 'json')
  )
""".strip()


def deploy_staged_payload(
    local_dir: Path,
    *,
    run_id: str,
    profile: str | None = None,
    catalog: str = DEFAULT_CATALOG,
    schema: str = DEFAULT_SCHEMA,
    warehouse_id: str = DEFAULT_WAREHOUSE_ID,
    cleanup_remote: bool = True,
) -> dict[str, object]:
    workspace_client = get_workspace_client(profile)
    client = DatabricksSqlClient(workspace_client, warehouse_id=warehouse_id)
    remote_dir = stage_payload_directory(local_dir, run_id, profile=profile)
    quoted_catalog = quote_sql_identifier(catalog)
    quoted_schema = quote_sql_identifier(schema)
    client.execute(_schema_sql(catalog, schema))
    for table_name, ddl in TABLE_DDLS.items():
        client.execute(ddl.format(catalog=quoted_catalog, schema=quoted_schema))
        remote_path = f"{remote_dir}/{table_name}.jsonl"
        if table_name in CURRENT_STATE_TABLES:
            client.execute(_deactivate_current_rows_sql(catalog, schema, table_name, remote_path))
        client.execute(
            INSERT_SELECTS[table_name].format(
                catalog=quoted_catalog,
                schema=quoted_schema,
                remote_path=remote_path,
            )
        )
    if cleanup_remote:
        cleanup_staged_directory(remote_dir, profile=profile)
    return {
        "catalog": catalog,
        "schema": schema,
        "remote_dir": remote_dir,
        "warehouse_id": warehouse_id,
    }
