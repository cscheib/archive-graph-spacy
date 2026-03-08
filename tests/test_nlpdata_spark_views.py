import os
from pathlib import Path

import pytest
from archive_graph_spacy.nlpdata.spark_views import (
    create_temp_view_from_rows,
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
            "rows": rows,
            "schema": spark_schema_for_table("message_search_docs"),
        }
    ]
    assert spark.dataframe.temp_view == "tmp_message_search_docs"


def test_refresh_notebook_uses_typed_temp_view_helper() -> None:
    notebook = Path("notebooks/01_nlpdata_refresh.py").read_text(encoding="utf-8")

    assert "from archive_graph_spacy.nlpdata.spark_views import create_temp_view_from_rows" in notebook
    assert "create_temp_view_from_rows(" in notebook
    assert "spark.createDataFrame(rows).createOrReplaceTempView(temp_view)" not in notebook


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
