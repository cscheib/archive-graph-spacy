import os
from pathlib import Path

import pytest
from archive_graph_spacy.nlpdata.spark_views import (
    create_temp_view_from_rows,
    ordered_rows_for_table,
    spark_schema_for_table,
)


class FakeDataFrame:
    def __init__(self) -> None:
        self.temp_view: str | None = None

    def createOrReplaceTempView(self, temp_view: str) -> None:
        self.temp_view = temp_view


class FakeSparkSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.dataframe = FakeDataFrame()

    def createDataFrame(self, rows, schema=None):
        if schema is None:
            raise AssertionError("schema inference would be used")
        self.calls.append({"rows": rows, "schema": schema})
        return self.dataframe


def test_spark_schema_for_message_search_docs_covers_ambiguous_columns() -> None:
    schema = spark_schema_for_table("message_search_docs")

    assert "timestamp STRING" in schema
    assert "subject_terms ARRAY<STRING>" in schema
    assert "time_facets MAP<STRING, STRING>" in schema


def test_spark_schema_for_phase_pair_summaries_covers_phase_outputs() -> None:
    schema = spark_schema_for_table("phase_pair_summaries")

    assert "phase_pair_id STRING" in schema
    assert "phase_id STRING" in schema
    assert "activity_score DOUBLE" in schema
    assert "is_current BOOLEAN" in schema


def test_spark_schema_for_phase_pair_evidence_includes_run_id() -> None:
    schema = spark_schema_for_table("phase_pair_evidence")

    assert "phase_pair_evidence_id STRING" in schema
    assert "phase_id STRING" in schema
    assert "run_id STRING" in schema
    assert "contribution_score DOUBLE" in schema


def test_create_temp_view_from_rows_supplies_explicit_schema() -> None:
    spark = FakeSparkSession()
    rows = [
        {
            "message_id": "m-001",
            "run_id": "run-123",
            "source_interaction_id": "src-001",
            "source_type": "email",
            "timestamp": None,
            "subject_terms": None,
            "body_terms": None,
            "linked_person_ids": None,
            "linked_person_names": None,
            "explicit_person_ids": None,
            "inferred_person_ids": None,
            "theme_labels": None,
            "time_facets": None,
            "is_current": True,
        }
    ]

    create_temp_view_from_rows(
        spark,
        table_name="message_search_docs",
        rows=rows,
        temp_view="tmp_message_search_docs",
    )

    assert spark.calls == [
        {
            "rows": [
                (
                    "m-001",
                    "run-123",
                    "src-001",
                    "email",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    True,
                )
            ],
            "schema": spark_schema_for_table("message_search_docs"),
        }
    ]
    assert spark.dataframe.temp_view == "tmp_message_search_docs"


def test_ordered_rows_for_nlp_runs_preserves_publish_diagnostics_column() -> None:
    rows = [
        {
            "run_id": "run-123",
            "run_scope": "scope",
            "source_catalog": "personal_archive_dev",
            "started_at": "2026-03-08T00:00:00+00:00",
            "completed_at": "2026-03-08T00:01:00+00:00",
            "status": "completed",
            "input_interaction_count": 100,
            "output_row_counts": "{\"message_mentions\": 1}",
            "quality_metrics": "{\"runtime_seconds\": 1.0}",
            "publish_diagnostics": "{\"publish_outcome\": \"staged\"}",
        }
    ]

    assert ordered_rows_for_table("nlp_runs", rows) == [
        (
            "run-123",
            "scope",
            "personal_archive_dev",
            "2026-03-08T00:00:00+00:00",
            "2026-03-08T00:01:00+00:00",
            "completed",
            100,
            "{\"message_mentions\": 1}",
            "{\"runtime_seconds\": 1.0}",
            "{\"publish_outcome\": \"staged\"}",
        )
    ]


def test_ordered_rows_for_phase_diagnostics_preserves_phase_details() -> None:
    rows = [
        {
            "run_id": "run-123",
            "phase_id": "phase-001",
            "diagnostic_type": "boundary",
            "result": "retained",
            "reason_code": "gap_retained",
            "sample_ref": "message:m-001",
            "details": "retained boundary after 45 day gap",
        }
    ]

    assert ordered_rows_for_table("phase_diagnostics", rows) == [
        (
            "run-123",
            "phase-001",
            "boundary",
            "retained",
            "gap_retained",
            "message:m-001",
            "retained boundary after 45 day gap",
        )
    ]


def test_refresh_notebook_uses_typed_temp_view_helper() -> None:
    notebook = Path("notebooks/01_nlpdata_refresh.py").read_text(encoding="utf-8")

    assert 'dbutils.widgets.text("job_id", "", "Databricks Job ID")' in notebook
    assert 'dbutils.widgets.text("job_run_id", "", "Databricks Job Run ID")' in notebook
    assert 'dbutils.widgets.text("task_run_id", "", "Databricks Task Run ID")' in notebook
    assert 'dbutils.widgets.text("task_name", "", "Databricks Task Name")' in notebook
    assert "from archive_graph_spacy.nlpdata.spark_views import create_temp_view_from_rows" in notebook
    assert "from archive_graph_spacy.nlpdata.deploy import (" in notebook
    assert "from archive_graph_spacy.nlpdata.runs import (" in notebook
    assert "build_databricks_runtime_metadata" in notebook
    assert "merge_publish_diagnostics" in notebook
    assert "_delete_matching_candidate_assertions_sql" in notebook
    assert (
        "from archive_graph_spacy.nlpdata.deploy import CURRENT_STATE_IDENTITY_COLUMNS, CURRENT_STATE_TABLES, TABLE_DDLS"
        in notebook
    )
    assert "create_temp_view_from_rows(" in notebook
    assert "spark.createDataFrame(rows).createOrReplaceTempView(temp_view)" not in notebook
    assert '"publish_diagnostics": json.dumps(run_publish_diagnostics)' in notebook
    assert 'subprocess.check_call(["pip", "install", wheel_path])' in notebook
    assert "os.path.exists(wheel_path)" not in notebook
    assert "spark.sql(_show_columns_sql(catalog, schema, table_name)).collect()" in notebook
    assert "alter_sql = _add_missing_columns_sql(catalog, schema, table_name, existing_columns)" in notebook
    assert "if alter_sql is not None:" in notebook
    assert "spark.sql(alter_sql)" in notebook
    assert "for table_name, rows in payload.items():" in notebook
    assert "rows = payload[table_name]" not in notebook
    assert 'if table_name == "nlp_runs":' in notebook
    assert "run_publish_diagnostics = merge_publish_diagnostics(result.run.publish_diagnostics, runtime_metadata)" in notebook
    assert '"candidate_assertions_summary": [result.candidate_summary.to_record()]' in notebook
    assert '"reviewed_effects": [row.to_record() for row in result.reviewed_effects]' in notebook
    assert 'if table_name == "candidate_assertions":' in notebook
    assert "identity_column = CURRENT_STATE_IDENTITY_COLUMNS[table_name]" in notebook
    assert "SELECT DISTINCT {quote_sql_identifier(identity_column)} FROM {temp_view}" in notebook
    assert "CREATE OR REPLACE TEMP VIEW" in notebook


def test_phase_refresh_notebook_uses_preview_subject_message_text() -> None:
    notebook = Path("notebooks/02_nlpdata_phase_refresh.py").read_text(encoding="utf-8")

    assert 'dbutils.widgets.text("job_id", "", "Databricks Job ID")' in notebook
    assert 'dbutils.widgets.text("job_run_id", "", "Databricks Job Run ID")' in notebook
    assert 'dbutils.widgets.text("task_run_id", "", "Databricks Task Run ID")' in notebook
    assert 'dbutils.widgets.text("task_name", "", "Databricks Task Name")' in notebook
    assert "build_databricks_runtime_metadata" in notebook
    assert "merge_publish_diagnostics" in notebook
    assert "COALESCE(i.preview, i.subject) IS NOT NULL" in notebook
    assert "COALESCE(i.preview, i.subject, '') AS body" in notebook
    assert "COALESCE(i.body, i.preview, i.subject)" not in notebook
    assert "_deactivate_all_current_phase_rows_sql" in notebook
    assert "_deactivate_phase_scope_rows_sql(catalog, schema, table_name, phase_result.run.run_scope)" not in notebook


def test_jobs_bundle_passes_job_hierarchy_metadata_to_nlpdata_notebooks() -> None:
    bundle = Path("resources/nlpdata_jobs.yml").read_text(encoding="utf-8")

    assert 'job_id: "{{job.id}}"' in bundle
    assert 'job_run_id: "{{job.run_id}}"' in bundle
    assert 'task_run_id: "{{task.run_id}}"' in bundle
    assert 'task_name: "{{task.name}}"' in bundle


@pytest.mark.skipif(
    not Path("/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home").exists(),
    reason="Homebrew OpenJDK 17 not available",
)
def test_real_pyspark_handles_all_null_ambiguous_columns_with_explicit_schema(monkeypatch) -> None:
    pyspark = pytest.importorskip("pyspark")
    monkeypatch.setenv("JAVA_HOME", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home")
    monkeypatch.setenv(
        "PATH",
        f"{os.environ['JAVA_HOME']}/bin:{os.environ['PATH']}",
    )
    monkeypatch.setenv("SPARK_LOCAL_IP", "127.0.0.1")

    spark = (
        pyspark.sql.SparkSession.builder.master("local[1]")
        .appName("archive-graph-spacy-tests")
        .getOrCreate()
    )
    rows = [
        {
            "message_id": "m-001",
            "run_id": "run-123",
            "source_interaction_id": "src-001",
            "source_type": "email",
            "timestamp": None,
            "subject_terms": None,
            "body_terms": None,
            "linked_person_ids": None,
            "linked_person_names": None,
            "explicit_person_ids": None,
            "inferred_person_ids": None,
            "theme_labels": None,
            "time_facets": None,
            "is_current": True,
        }
    ]

    try:
        with pytest.raises(pyspark.errors.PySparkValueError, match="CANNOT_DETERMINE_TYPE"):
            spark.createDataFrame(rows)

        create_temp_view_from_rows(
            spark,
            table_name="message_search_docs",
            rows=rows,
            temp_view="tmp_message_search_docs",
        )

        schema = spark.table("tmp_message_search_docs").schema
        row = spark.table("tmp_message_search_docs").collect()[0]
        assert row["message_id"] == "m-001"
        assert row["subject_terms"] is None
        assert row["time_facets"] is None
        assert schema["subject_terms"].dataType.simpleString() == "array<string>"
        assert schema["time_facets"].dataType.simpleString() == "map<string,string>"
    finally:
        spark.stop()
