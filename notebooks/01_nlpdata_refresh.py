# Databricks notebook source
# MAGIC %md
# MAGIC # Refresh `nlpdata`

# COMMAND ----------

dbutils.widgets.text("catalog", "personal_archive_dev", "Catalog")
dbutils.widgets.text("schema", "nlpdata", "Schema")
dbutils.widgets.text("wheel_path", "", "Wheel Path")
dbutils.widgets.text("warehouse_id", "4b799682f2bfd311", "Warehouse ID")
dbutils.widgets.text("message_limit", "", "Message Limit")
dbutils.widgets.text("people_limit", "", "People Limit")
dbutils.widgets.text("start_date", "", "Start Date")
dbutils.widgets.text("end_date", "", "End Date")

# COMMAND ----------

import json
import subprocess

wheel_path = dbutils.widgets.get("wheel_path")
if not wheel_path:
    raise ValueError("wheel_path parameter is required.")

print(f"Installing wheel from: {wheel_path}")
subprocess.check_call(["pip", "install", wheel_path])

# COMMAND ----------

from archive_graph_spacy.nlpdata.contracts import TABLE_CONTRACTS
from archive_graph_spacy.nlpdata.databricks import (
    quote_sql_identifier,
    quote_sql_string_literal,
    validate_iso_date,
)
from archive_graph_spacy.nlpdata.deploy import CURRENT_STATE_IDENTITY_COLUMNS, CURRENT_STATE_TABLES, TABLE_DDLS
from archive_graph_spacy.nlpdata.deploy import (
    _add_missing_columns_sql,
    _delete_matching_candidate_assertions_sql,
    _show_columns_sql,
)
from archive_graph_spacy.nlpdata.pipeline import run_pipeline
from archive_graph_spacy.nlpdata.spark_views import create_temp_view_from_rows
from archive_graph_spacy.nlpdata.source_loader import source_bundle_from_rows

catalog = dbutils.widgets.get("catalog") or "personal_archive_dev"
schema = dbutils.widgets.get("schema") or "nlpdata"
message_limit = dbutils.widgets.get("message_limit").strip()
people_limit = dbutils.widgets.get("people_limit").strip()
start_date = dbutils.widgets.get("start_date").strip() or None
end_date = dbutils.widgets.get("end_date").strip() or None

quoted_catalog = quote_sql_identifier(catalog)
quoted_schema = quote_sql_identifier(schema)
if start_date is not None:
    start_date = validate_iso_date(start_date)
if end_date is not None:
    end_date = validate_iso_date(end_date)


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return quote_sql_string_literal(str(value))

interaction_types = (
    "email",
    "chat",
    "fb_message",
    "dating_notification",
    "linkedin_notification",
    "payment_notification",
)
quoted_types = ", ".join(f"'{value}'" for value in interaction_types)

message_predicates = [
    f"i.interaction_type IN ({quoted_types})",
    "COALESCE(i.preview, i.subject) IS NOT NULL",
]
if start_date:
    message_predicates.append(f"i.timestamp >= {quote_sql_string_literal(start_date)}")
if end_date:
    message_predicates.append(f"i.timestamp < {quote_sql_string_literal(end_date)}")
message_where = " AND ".join(message_predicates)
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
        WHERE {message_where}
        ORDER BY i.timestamp DESC NULLS LAST, i.global_interaction_id
        {message_limit_sql}
        """
    ).collect()
]

people_limit_sql = f"LIMIT {int(people_limit)}" if people_limit else ""
contact_rows = [
    row.asDict(recursive=True)
    for row in spark.sql(
        f"""
        SELECT
          p.person_id,
          p.canonical_name AS display_name,
          p.emails,
          p.phones,
          p.photo_url,
          COALESCE(o.entity_type_override, c.entity_type, 'unknown') AS entity_type
        FROM {quoted_catalog}.gold.persons p
        LEFT JOIN {quoted_catalog}.memory.entity_overrides o ON p.person_id = o.person_id
        LEFT JOIN {quoted_catalog}.gold.entity_classification c ON p.person_id = c.person_id
        WHERE COALESCE(p.canonical_person_id, p.person_id) = p.person_id
        ORDER BY COALESCE(p.interaction_count, 0) DESC, p.person_id
        {people_limit_sql}
        """
    ).collect()
]

bundle = source_bundle_from_rows(
    contact_rows,
    message_rows,
)
refresh_phases = start_date is None and end_date is None
result = run_pipeline(
    bundle,
    run_scope=f"{catalog}.gold",
    source_catalog=catalog,
    include_phases=False,
)

payload = {
    "nlp_runs": [
        {
            **result.run.to_record(),
            "output_row_counts": json.dumps(result.run.output_row_counts),
            "quality_metrics": json.dumps(result.run.quality_metrics),
            "publish_diagnostics": json.dumps(result.run.publish_diagnostics),
        }
    ],
    "message_mentions": [row.to_record() for row in result.mentions],
    "message_person_links": [row.to_record() for row in result.person_links],
    "candidate_assertions": [row.to_record() for row in result.candidate_assertions],
    "candidate_assertions_summary": [result.candidate_summary.to_record()],
    "reviewed_effects": [row.to_record() for row in result.reviewed_effects],
    "person_person_edges": [row.to_record() for row in result.person_person_edges],
    "person_person_edge_evidence": [row.to_record() for row in result.person_person_edge_evidence],
    "message_theme_tags": [row.to_record() for row in result.theme_tags],
    "message_search_docs": [row.to_record() for row in result.search_docs],
}

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {quoted_catalog}.{quoted_schema}")

for table_name, ddl in TABLE_DDLS.items():
    spark.sql(ddl.format(catalog=quoted_catalog, schema=quoted_schema))
    existing_column_rows = spark.sql(_show_columns_sql(catalog, schema, table_name)).collect()
    existing_columns = {str(row["col_name"]) for row in existing_column_rows}
    alter_sql = _add_missing_columns_sql(catalog, schema, table_name, existing_columns)
    if alter_sql is not None:
        spark.sql(alter_sql)
    rows = payload[table_name]
    if not rows:
        continue
    temp_view = f"tmp_{table_name}"
    if table_name == "nlp_runs":
        select_list = ",\n          ".join(
            f"{sql_literal(rows[0][column])} AS {quote_sql_identifier(column)}"
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
    if table_name == "candidate_assertions":
        spark.sql(
            _delete_matching_candidate_assertions_sql(
                catalog,
                schema,
                source_relation_sql=temp_view,
            )
        )
    if table_name in CURRENT_STATE_TABLES:
        identity_column = CURRENT_STATE_IDENTITY_COLUMNS[table_name]
        spark.sql(
            f"""
            UPDATE {quoted_catalog}.{quoted_schema}.{quote_sql_identifier(table_name)}
            SET is_current = false
            WHERE is_current = true
              AND {quote_sql_identifier(identity_column)} IN (
                SELECT DISTINCT {quote_sql_identifier(identity_column)} FROM {temp_view}
              )
            """
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
    "run_id": result.run.run_id,
    "input_interaction_count": result.run.input_interaction_count,
    "output_row_counts": result.run.output_row_counts,
    "quality_metrics": result.run.quality_metrics,
}
if refresh_phases:
    phase_refresh_payload = json.loads(
        dbutils.notebook.run(
            "./02_nlpdata_phase_refresh",
            0,
            {
                "catalog": catalog,
                "schema": schema,
                "wheel_path": wheel_path,
                "warehouse_id": dbutils.widgets.get("warehouse_id"),
                "message_limit": message_limit,
            },
        )
    )
    summary["phase_refresh"] = phase_refresh_payload

print(summary)
dbutils.notebook.exit(json.dumps(summary))
