# Databricks notebook source
# MAGIC %md
# MAGIC # Refresh Global `nlpdata` Phases

# COMMAND ----------

dbutils.widgets.text("catalog", "personal_archive_dev", "Catalog")
dbutils.widgets.text("schema", "nlpdata", "Schema")
dbutils.widgets.text("wheel_path", "", "Wheel Path")
dbutils.widgets.text("warehouse_id", "4b799682f2bfd311", "Warehouse ID")
dbutils.widgets.text("message_limit", "", "Message Limit")

# COMMAND ----------

import json
import subprocess
from datetime import datetime

wheel_path = dbutils.widgets.get("wheel_path")
if not wheel_path:
    raise ValueError("wheel_path parameter is required.")

print(f"Installing wheel from: {wheel_path}")
subprocess.check_call(["pip", "install", wheel_path])

# COMMAND ----------

from archive_graph_spacy.models import Message
from archive_graph_spacy.nlpdata.contracts import TABLE_CONTRACTS
from archive_graph_spacy.nlpdata.databricks import quote_sql_identifier, quote_sql_string_literal
from archive_graph_spacy.nlpdata.deploy import PHASE_SCOPE_TABLES, TABLE_DDLS
from archive_graph_spacy.nlpdata.deploy import (
    _add_missing_columns_sql,
    _deactivate_phase_scope_rows_sql,
    _show_columns_sql,
)
from archive_graph_spacy.nlpdata.models import (
    PersonMessageLink,
    PersonPersonEdgeEvidenceRecord,
    PersonPersonEdgeRecord,
    ThemeTag,
)
from archive_graph_spacy.nlpdata.pipeline import run_phase_refresh
from archive_graph_spacy.nlpdata.spark_views import create_temp_view_from_rows
from archive_graph_spacy.nlpdata.source_loader import source_bundle_from_rows

catalog = dbutils.widgets.get("catalog") or "personal_archive_dev"
schema = dbutils.widgets.get("schema") or "nlpdata"
message_limit = dbutils.widgets.get("message_limit").strip()

quoted_catalog = quote_sql_identifier(catalog)
quoted_schema = quote_sql_identifier(schema)


def _coerce_list(value):
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value if str(item).strip())
    if isinstance(value, list):
        return tuple(str(item) for item in value if str(item).strip())
    return (str(value),)


interaction_types = (
    "email",
    "chat",
    "fb_message",
    "dating_notification",
    "linkedin_notification",
    "payment_notification",
)
quoted_types = ", ".join(f"'{value}'" for value in interaction_types)
message_limit_sql = f"LIMIT {int(message_limit)}" if message_limit else ""

message_rows = [
    row.asDict(recursive=True)
    for row in spark.sql(
        f"""
        SELECT
          i.global_interaction_id AS message_id,
          COALESCE(i.source, i.interaction_type) AS source,
          i.from_email AS sender,
          i.to_email AS recipients,
          i.subject,
          COALESCE(i.preview, i.subject, '') AS body,
          CAST(i.timestamp AS STRING) AS timestamp,
          i.interaction_type
        FROM {quoted_catalog}.gold.interactions i
        WHERE i.interaction_type IN ({quoted_types})
          AND COALESCE(i.preview, i.subject) IS NOT NULL
        ORDER BY i.timestamp DESC NULLS LAST, i.global_interaction_id
        {message_limit_sql}
        """
    ).collect()
]

person_link_rows = [
    row.asDict(recursive=True)
    for row in spark.sql(
        f"""
        SELECT *
        FROM {quoted_catalog}.{quoted_schema}.message_person_links
        WHERE is_current = true
        """
    ).collect()
]

theme_rows = [
    row.asDict(recursive=True)
    for row in spark.sql(
        f"""
        SELECT *
        FROM {quoted_catalog}.{quoted_schema}.message_theme_tags
        WHERE is_current = true
        """
    ).collect()
]

edge_rows = [
    row.asDict(recursive=True)
    for row in spark.sql(
        f"""
        SELECT *
        FROM {quoted_catalog}.{quoted_schema}.person_person_edges
        WHERE is_current = true
        """
    ).collect()
]

edge_evidence_rows = [
    row.asDict(recursive=True)
    for row in spark.sql(
        f"""
        WITH current_pairs AS (
          SELECT DISTINCT pair_id
          FROM {quoted_catalog}.{quoted_schema}.person_person_edges
          WHERE is_current = true
        )
        SELECT DISTINCT
          e.pair_evidence_id,
          e.pair_id,
          e.evidence_family,
          e.source_ref,
          e.contribution_score,
          e.rank_within_pair,
          e.message_ref,
          e.theme_refs,
          e.provenance
        FROM {quoted_catalog}.{quoted_schema}.person_person_edge_evidence e
        INNER JOIN current_pairs p
          ON e.pair_id = p.pair_id
        """
    ).collect()
]

messages = source_bundle_from_rows([], message_rows).messages
person_links = tuple(
    PersonMessageLink(
        link_id=str(row["link_id"]),
        run_id=str(row["run_id"]),
        message_id=str(row["message_id"]),
        person_id=str(row["person_id"]),
        person_name=str(row["person_name"]),
        role=str(row["role"]),
        link_origin=str(row["link_origin"]),
        confidence=float(row["confidence"]),
        evidence_type=str(row["evidence_type"]),
        evidence_value=str(row["evidence_value"]),
        source_interaction_id=str(row["source_interaction_id"]),
        is_current=bool(row.get("is_current", True)),
    )
    for row in person_link_rows
)
theme_tags = tuple(
    ThemeTag(
        theme_tag_id=str(row["theme_tag_id"]),
        run_id=str(row["run_id"]),
        message_id=str(row["message_id"]),
        theme=str(row["theme"]),
        confidence=float(row["confidence"]),
        evidence=str(row["evidence"]),
        source_method=str(row["source_method"]),
        source_interaction_id=str(row["source_interaction_id"]),
        is_current=bool(row.get("is_current", True)),
    )
    for row in theme_rows
)
person_person_edges = tuple(
    PersonPersonEdgeRecord(
        pair_id=str(row["pair_id"]),
        person_a_id=str(row["person_a_id"]),
        person_b_id=str(row["person_b_id"]),
        run_id=str(row["run_id"]),
        generation_scope=str(row["generation_scope"]),
        strength_score=float(row["strength_score"]),
        relationship_signal=str(row["relationship_signal"]),
        direct_evidence_count=int(row["direct_evidence_count"]),
        indirect_evidence_count=int(row["indirect_evidence_count"]),
        strongest_evidence_ref=str(row["strongest_evidence_ref"]),
        is_current=bool(row.get("is_current", True)),
    )
    for row in edge_rows
)
person_person_edge_evidence = tuple(
    PersonPersonEdgeEvidenceRecord(
        pair_evidence_id=str(row["pair_evidence_id"]),
        pair_id=str(row["pair_id"]),
        evidence_family=str(row["evidence_family"]),
        source_ref=str(row["source_ref"]),
        contribution_score=float(row["contribution_score"]),
        rank_within_pair=int(row["rank_within_pair"]),
        message_ref=str(row["message_ref"]),
        theme_refs=_coerce_list(row.get("theme_refs")),
        provenance=str(row.get("provenance") or ""),
    )
    for row in edge_evidence_rows
)

phase_result = run_phase_refresh(
    messages=messages,
    person_links=person_links,
    theme_tags=theme_tags,
    person_person_edges=person_person_edges,
    person_person_edge_evidence=person_person_edge_evidence,
    run_scope=f"{catalog}.{schema}.phases",
    source_catalog=catalog,
)

payload = {
    "nlp_runs": [
        {
            **phase_result.run.to_record(),
            "output_row_counts": json.dumps(phase_result.run.output_row_counts),
            "quality_metrics": json.dumps(phase_result.run.quality_metrics),
            "publish_diagnostics": json.dumps(phase_result.run.publish_diagnostics),
        }
    ],
    "phases": [row.to_record() for row in phase_result.phases],
    "phase_central_people": [row.to_record() for row in phase_result.phase_central_people],
    "phase_theme_summaries": [row.to_record() for row in phase_result.phase_theme_summaries],
    "phase_pair_summaries": [row.to_record() for row in phase_result.phase_pair_summaries],
    "phase_pair_evidence": [row.to_record() for row in phase_result.phase_pair_evidence],
    "phase_representative_interactions": [
        row.to_record() for row in phase_result.phase_representative_interactions
    ],
    "phase_diagnostics": [row.to_record() for row in phase_result.phase_diagnostics],
}

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {quoted_catalog}.{quoted_schema}")

for table_name in payload:
    spark.sql(TABLE_DDLS[table_name].format(catalog=quoted_catalog, schema=quoted_schema))
    existing_column_rows = spark.sql(_show_columns_sql(catalog, schema, table_name)).collect()
    existing_columns = {str(row["col_name"]) for row in existing_column_rows}
    alter_sql = _add_missing_columns_sql(catalog, schema, table_name, existing_columns)
    if alter_sql is not None:
        spark.sql(alter_sql)

for table_name in (
    "phase_central_people",
    "phase_theme_summaries",
    "phase_pair_summaries",
    "phase_pair_evidence",
    "phase_representative_interactions",
    "phases",
):
    spark.sql(_deactivate_phase_scope_rows_sql(catalog, schema, table_name, phase_result.run.run_scope))

for table_name, rows in payload.items():
    if table_name != "nlp_runs" and not rows:
        continue
    temp_view = f"tmp_{table_name}"
    if table_name == "nlp_runs":
        select_list = ",\n          ".join(
            f"{quote_sql_string_literal(str(rows[0][column]))} AS {quote_sql_identifier(column)}"
            if column in {"run_id", "run_scope", "source_catalog", "started_at", "completed_at", "status", "output_row_counts", "quality_metrics", "publish_diagnostics"}
            else f"{rows[0][column]} AS {quote_sql_identifier(column)}"
            for column in TABLE_CONTRACTS[table_name]
        )
        spark.sql(
            f"""
            CREATE OR REPLACE TEMP VIEW {quote_sql_identifier(temp_view)} AS
            SELECT
              {select_list}
            """
        )
    else:
        create_temp_view_from_rows(
            spark,
            table_name=table_name,
            rows=rows,
            temp_view=temp_view,
        )
    columns = TABLE_CONTRACTS[table_name]
    column_list = ", ".join(columns)
    spark.sql(
        f"""
        INSERT INTO {quoted_catalog}.{quoted_schema}.{quote_sql_identifier(table_name)} ({column_list})
        SELECT {column_list}
        FROM {temp_view}
        """
    )

summary = {
    "run_id": phase_result.run.run_id,
    "input_interaction_count": phase_result.run.input_interaction_count,
    "output_row_counts": phase_result.run.output_row_counts,
    "quality_metrics": phase_result.run.quality_metrics,
}
print(summary)
dbutils.notebook.exit(json.dumps(summary))
