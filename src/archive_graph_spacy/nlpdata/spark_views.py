"""Helpers for staging typed Spark temp views from local row payloads."""

from __future__ import annotations

SPARK_TABLE_SCHEMAS: dict[str, str] = {
    "nlp_runs": """
run_id STRING,
run_scope STRING,
source_catalog STRING,
started_at STRING,
completed_at STRING,
status STRING,
input_interaction_count BIGINT,
output_row_counts STRING,
quality_metrics STRING,
publish_diagnostics STRING
""".strip(),
    "message_mentions": """
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
""".strip(),
    "message_person_links": """
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
""".strip(),
    "candidate_assertions": """
candidate_assertion_id STRING,
run_id STRING,
assertion_type STRING,
subject_canonical_id STRING,
proposed_claim STRING,
evidence_refs ARRAY<STRING>,
provenance_summary STRING,
confidence_level DOUBLE,
generation_scope STRING,
generated_at STRING,
review_class STRING,
promotion_class STRING
""".strip(),
    "candidate_assertions_summary": """
run_id STRING,
generation_scope STRING,
emitted_candidate_count BIGINT,
candidate_counts_by_type MAP<STRING, BIGINT>,
suppressed_counts MAP<STRING, BIGINT>,
example_candidate_ids ARRAY<STRING>,
generated_at STRING
""".strip(),
    "message_theme_tags": """
theme_tag_id STRING,
run_id STRING,
message_id STRING,
theme STRING,
confidence DOUBLE,
evidence STRING,
source_method STRING,
source_interaction_id STRING,
is_current BOOLEAN
""".strip(),
    "message_search_docs": """
message_id STRING,
run_id STRING,
source_interaction_id STRING,
source_type STRING,
timestamp STRING,
subject_terms ARRAY<STRING>,
body_terms ARRAY<STRING>,
linked_person_ids ARRAY<STRING>,
linked_person_names ARRAY<STRING>,
explicit_person_ids ARRAY<STRING>,
inferred_person_ids ARRAY<STRING>,
theme_labels ARRAY<STRING>,
time_facets MAP<STRING, STRING>,
is_current BOOLEAN
""".strip(),
}


def spark_schema_for_table(table_name: str) -> str:
    try:
        return SPARK_TABLE_SCHEMAS[table_name]
    except KeyError as exc:
        raise KeyError(f"Unsupported Spark temp-view table: {table_name}") from exc


def create_temp_view_from_rows(
    spark: object,
    *,
    table_name: str,
    rows: list[dict[str, object]],
    temp_view: str,
) -> None:
    schema = spark_schema_for_table(table_name)
    spark.createDataFrame(rows, schema=schema).createOrReplaceTempView(temp_view)
