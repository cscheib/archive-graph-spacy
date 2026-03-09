import json
from pathlib import Path

import pytest

from archive_graph_spacy.nlpdata.deploy import (
    DEFAULT_CATALOG,
    DEFAULT_SCHEMA,
    cleanup_staged_directory,
    deploy_staged_payload,
    stage_payload_directory,
)


class FakeSqlClient:
    def __init__(
        self,
        *,
        fail_on_statement: str | None = None,
        show_columns: dict[str, list[dict[str, object]]] | None = None,
    ) -> None:
        self.statements: list[str] = []
        self.fail_on_statement = fail_on_statement
        self.show_columns = show_columns or {}

    def execute(self, statement: str) -> dict[str, object]:
        if self.fail_on_statement and self.fail_on_statement in statement:
            raise RuntimeError("simulated statement failure")
        self.statements.append(statement)
        return {"status": {"state": "SUCCEEDED"}}

    def fetch_all(self, statement: str) -> list[dict[str, object]]:
        self.statements.append(statement)
        return self.show_columns.get(statement, [])


def _write_payload_fixture(tmp_path: Path, run_id: str = "run-123") -> None:
    (tmp_path / "nlp_runs.jsonl").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "run_scope": "sample-scope",
                "source_catalog": "personal_archive_dev",
                "started_at": "2026-03-08T00:00:00+00:00",
                "completed_at": "2026-03-08T00:00:10+00:00",
                "status": "completed",
                "input_interaction_count": 1,
                "output_row_counts": {},
                "quality_metrics": {},
                "publish_diagnostics": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "message_mentions.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "message_person_links.jsonl").write_text(
        json.dumps(
            {
                "link_id": "link-1",
                "run_id": run_id,
                "message_id": "m-001",
                "person_id": "p-001",
                "person_name": "Alice Example",
                "role": "sender",
                "link_origin": "explicit",
                "confidence": 0.9,
                "evidence_type": "email",
                "evidence_value": "alice@example.com",
                "source_interaction_id": "m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "message_theme_tags.jsonl").write_text(
        json.dumps(
            {
                "theme_tag_id": "theme-1",
                "run_id": run_id,
                "message_id": "m-001",
                "theme": "travel",
                "confidence": 0.8,
                "evidence": "trip",
                "source_method": "keyword",
                "source_interaction_id": "m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "message_search_docs.jsonl").write_text(
        json.dumps(
            {
                "message_id": "m-001",
                "run_id": run_id,
                "source_interaction_id": "m-001",
                "source_type": "email",
                "timestamp": None,
                "subject_terms": [],
                "body_terms": ["trip"],
                "linked_person_ids": ["p-001"],
                "linked_person_names": ["Alice Example"],
                "explicit_person_ids": ["p-001"],
                "inferred_person_ids": [],
                "theme_labels": ["travel"],
                "time_facets": {},
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_stage_payload_directory_uses_databricks_fs_cp(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(command, check, capture_output, text):
        commands.append(command)
        class Result:
            stdout = ""
        return Result()

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.subprocess.run", fake_run)

    remote = stage_payload_directory(tmp_path, "run-123", profile="dev-profile")

    assert remote.endswith("/run-123")
    assert commands[0][:5] == ["databricks", "fs", "cp", "-r", str(tmp_path)]
    assert "--profile" in commands[0]


def test_cleanup_staged_directory_uses_databricks_fs_rm(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(command, check, capture_output, text):
        commands.append(command)
        class Result:
            stdout = ""
        return Result()

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.subprocess.run", fake_run)

    cleanup_staged_directory("dbfs:/tmp/archive_graph_spacy/nlpdata/run-123", profile="dev-profile")

    assert commands[0][:5] == ["databricks", "fs", "rm", "-r", "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123"]


def test_deploy_staged_payload_creates_schema_and_merges_current_tables(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient()

    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.get_workspace_client",
        lambda profile=None: object(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: sql_client,
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory",
        lambda remote_dir, profile=None: None,
    )

    result = deploy_staged_payload(tmp_path, run_id="run-123")

    assert result["catalog"] == DEFAULT_CATALOG
    assert result["schema"] == DEFAULT_SCHEMA
    assert result["publish_diagnostics"]["publish_outcome"] == "finalized"
    assert any("CREATE SCHEMA IF NOT EXISTS `personal_archive_dev`.`nlpdata`" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.message_search_docs" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`message_person_links`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`message_theme_tags`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`message_search_docs`" in stmt for stmt in sql_client.statements)
    assert any("INSERT INTO `personal_archive_dev`.`nlpdata`.nlp_runs" in stmt for stmt in sql_client.statements)
    insert_index = next(i for i, stmt in enumerate(sql_client.statements) if "INSERT INTO `personal_archive_dev`.`nlpdata`.message_person_links" in stmt)
    deactivate_index = next(i for i, stmt in enumerate(sql_client.statements) if "UPDATE `personal_archive_dev`.`nlpdata`.`message_person_links`" in stmt)
    activate_index = max(i for i, stmt in enumerate(sql_client.statements) if "SET is_current = true" in stmt and "`message_person_links`" in stmt)
    assert insert_index < deactivate_index < activate_index
    assert "false" in sql_client.statements[insert_index]


def test_deploy_staged_payload_adds_missing_contract_columns(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient(
        show_columns={
            "SHOW COLUMNS IN `personal_archive_dev`.`nlpdata`.`nlp_runs`": [
                {"col_name": "run_id"},
                {"col_name": "run_scope"},
                {"col_name": "source_catalog"},
                {"col_name": "started_at"},
                {"col_name": "completed_at"},
            ]
        }
    )

    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.get_workspace_client",
        lambda profile=None: object(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: sql_client,
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory",
        lambda remote_dir, profile=None: None,
    )

    deploy_staged_payload(tmp_path, run_id="run-123")

    assert any(
        "ALTER TABLE `personal_archive_dev`.`nlpdata`.`nlp_runs` ADD COLUMNS" in stmt
        and "`publish_diagnostics` STRING" in stmt
        for stmt in sql_client.statements
    )


def test_deploy_staged_payload_marks_partial_failure_as_rerunnable(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient(
        fail_on_statement="UPDATE `personal_archive_dev`.`nlpdata`.`message_theme_tags`\nSET is_current = true"
    )

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.get_workspace_client", lambda profile=None: object())
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: sql_client,
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory", lambda remote_dir, profile=None: None)

    result = deploy_staged_payload(tmp_path, run_id="run-123")

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["publish_outcome"] == "partial"
    assert diagnostics["recovery_action"] == "rerun_same_scope"
    assert diagnostics["manual_intervention_required"] is False
    assert diagnostics["error_detail"] == "simulated statement failure"
    assert "message_person_links" in diagnostics["finalized_tables"]
    assert "message_theme_tags" in diagnostics["failed_tables"]


def test_deploy_staged_payload_returns_diagnostics_when_persist_update_fails(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient(
        fail_on_statement="UPDATE `personal_archive_dev`.`nlpdata`.`nlp_runs`\nSET publish_diagnostics ="
    )

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.get_workspace_client", lambda profile=None: object())
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: sql_client,
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory", lambda remote_dir, profile=None: None)

    result = deploy_staged_payload(tmp_path, run_id="run-123")

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["publish_outcome"] == "finalized"
    assert "diagnostics_persist_error" in diagnostics


def test_deploy_staged_payload_rejects_overlapping_active_scope(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.get_workspace_client", lambda profile=None: object())
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory", lambda remote_dir, profile=None: None)

    result = deploy_staged_payload(
        tmp_path,
        run_id="run-123",
        active_scope_message_ids=(("m-001", "m-999"),),
    )

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["publish_outcome"] == "failed"
    assert diagnostics["recovery_action"] == "serialize_overlapping_scope"
    assert diagnostics["manual_intervention_required"] is True
    assert diagnostics["overlap_policy"] == "overlapping_scope"


def test_staged_insert_sql_raises_if_current_state_pattern_is_missing(monkeypatch) -> None:
    monkeypatch.setitem(
        __import__("archive_graph_spacy.nlpdata.deploy", fromlist=["INSERT_SELECTS"]).INSERT_SELECTS,
        "message_person_links",
        "INSERT INTO {catalog}.{schema}.message_person_links SELECT 1",
    )

    from archive_graph_spacy.nlpdata.deploy import _staged_insert_sql

    with pytest.raises(RuntimeError, match="Expected to replace 'CAST\\(is_current AS BOOLEAN\\)'"):
        _staged_insert_sql(
            "message_person_links",
            catalog="`personal_archive_dev`",
            schema="`nlpdata`",
            remote_path="dbfs:/tmp/archive_graph_spacy/nlpdata/run-123/message_person_links.jsonl",
        )


def test_deploy_staged_payload_rejects_invalid_catalog_identifier(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.get_workspace_client",
        lambda profile=None: object(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )

    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        deploy_staged_payload(tmp_path, run_id="run-123", catalog="personal_archive_dev;DROP SCHEMA x")


def test_deploy_staged_payload_rejects_invalid_run_id(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.get_workspace_client",
        lambda profile=None: object(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient(),
    )

    with pytest.raises(ValueError, match="Invalid run_id"):
        deploy_staged_payload(tmp_path, run_id="../run-123")
