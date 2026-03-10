"""Helpers for staging typed Spark temp views from local row payloads."""

from __future__ import annotations

from .contracts import TABLE_CONTRACTS


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
generated_at STRING,
reviewed_effect_counts MAP<STRING, BIGINT>
""".strip(),
    "reviewed_effects": """
run_id STRING,
candidate_assertion_id STRING,
assertion_type STRING,
subject_canonical_id STRING,
result STRING,
reason_code STRING,
details STRING
""".strip(),
    "person_person_edges": """
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
""".strip(),
    "person_person_edge_evidence": """
pair_evidence_id STRING,
pair_id STRING,
evidence_family STRING,
source_ref STRING,
contribution_score DOUBLE,
rank_within_pair INT,
message_ref STRING,
theme_refs ARRAY<STRING>,
provenance STRING
""".strip(),
    "phases": """
phase_id STRING,
run_id STRING,
generation_scope STRING,
phase_index INT,
start_at STRING,
end_at STRING,
interaction_count BIGINT,
representative_interaction_ref STRING,
boundary_reason STRING,
is_current BOOLEAN
""".strip(),
    "phase_central_people": """
phase_id STRING,
run_id STRING,
person_id STRING,
rank INT,
centrality_score DOUBLE,
interaction_count BIGINT,
evidence_ref STRING,
is_current BOOLEAN
""".strip(),
    "phase_theme_summaries": """
phase_id STRING,
run_id STRING,
theme STRING,
rank INT,
theme_score DOUBLE,
message_count BIGINT,
evidence_ref STRING,
is_current BOOLEAN
""".strip(),
    "phase_pair_summaries": """
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
""".strip(),
    "phase_pair_evidence": """
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
""".strip(),
    "phase_representative_interactions": """
phase_id STRING,
run_id STRING,
interaction_ref STRING,
rank INT,
selection_reason STRING,
is_current BOOLEAN
""".strip(),
    "phase_diagnostics": """
run_id STRING,
phase_id STRING,
diagnostic_type STRING,
result STRING,
reason_code STRING,
sample_ref STRING,
details STRING
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


def ordered_rows_for_table(table_name: str, rows: list[dict[str, object]]) -> list[tuple[object, ...]]:
    columns = TABLE_CONTRACTS[table_name]
    return [tuple(row.get(column) for column in columns) for row in rows]


def create_temp_view_from_rows(
    spark: object,
    *,
    table_name: str,
    rows: list[dict[str, object]],
    temp_view: str,
) -> None:
    schema = spark_schema_for_table(table_name)
    ordered_rows = ordered_rows_for_table(table_name, rows)
    spark.createDataFrame(ordered_rows, schema=schema).createOrReplaceTempView(temp_view)
