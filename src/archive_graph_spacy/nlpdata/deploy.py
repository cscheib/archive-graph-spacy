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
    FROM read_files({quote_sql_string_literal(remote_path)}, format => 'json')
  )
""".strip()


def _activate_staged_rows_sql(catalog: str, schema: str, table_name: str, run_id: str, remote_path: str) -> str:
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
  AND message_id IN (
    SELECT DISTINCT message_id
    FROM read_files({quote_sql_string_literal(remote_path)}, format => 'json')
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
    affected_tables: list[str] = []
    for table_name in CURRENT_STATE_TABLES:
        rows = _load_jsonl_rows(local_dir / f"{table_name}.jsonl")
        table_message_ids = {
            str(row["message_id"])
            for row in rows
            if row.get("run_id") == run_id and row.get("message_id")
        }
        if table_message_ids:
            affected_tables.append(table_name)
            message_ids.update(table_message_ids)
    affected_message_ids = tuple(sorted(message_ids))
    return BoundedPublishScope(
        run_id=run_id,
        run_scope=_load_run_scope(local_dir, run_id),
        affected_message_ids=affected_message_ids,
        affected_tables=tuple(sorted(affected_tables)),
        overlap_class=classify_scope_overlap(affected_message_ids, active_scope_message_ids),
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
        return {
            "catalog": catalog,
            "schema": schema,
            "remote_dir": remote_dir,
            "warehouse_id": warehouse_id,
            "publish_diagnostics": diagnostics,
        }
    quoted_catalog = quote_sql_identifier(catalog)
    quoted_schema = quote_sql_identifier(schema)
    client.execute(_schema_sql(catalog, schema))
    publish_stage = "staged"
    finalized_tables: list[str] = []
    failed_tables: list[str] = []
    recovery_action = "rerun_same_scope"
    manual_intervention_required = False
    for table_name, ddl in TABLE_DDLS.items():
        client.execute(ddl.format(catalog=quoted_catalog, schema=quoted_schema))
        remote_path = f"{remote_dir}/{table_name}.jsonl"
        client.execute(
            _staged_insert_sql(
                table_name,
                catalog=quoted_catalog,
                schema=quoted_schema,
                remote_path=remote_path,
            )
        )
    try:
        for table_name in publish_scope.affected_tables:
            remote_path = f"{remote_dir}/{table_name}.jsonl"
            publish_stage = "finalizing"
            client.execute(_deactivate_current_rows_sql(catalog, schema, table_name, remote_path))
            client.execute(_activate_staged_rows_sql(catalog, schema, table_name, run_id, remote_path))
            finalized_tables.append(table_name)
        publish_stage = "finalized"
        publish_outcome = "finalized"
        recovery_action = "none"
    except Exception:
        failed_tables = [table for table in publish_scope.affected_tables if table not in finalized_tables]
        manual_intervention_required = not publish_scope.affected_message_ids or publish_stage != "finalizing"
        publish_outcome = "partial" if finalized_tables else "failed"
        recovery_action = "manual_intervention" if manual_intervention_required else "rerun_same_scope"
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
