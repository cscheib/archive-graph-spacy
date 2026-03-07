from pathlib import Path

from archive_graph_spacy.nlpdata.deploy import (
    DEFAULT_CATALOG,
    DEFAULT_SCHEMA,
    cleanup_staged_directory,
    deploy_staged_payload,
    stage_payload_directory,
)


class FakeSqlClient:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement: str) -> dict[str, object]:
        self.statements.append(statement)
        return {"status": {"state": "SUCCEEDED"}}


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
    for table_name in (
        "nlp_runs",
        "message_mentions",
        "message_person_links",
        "message_theme_tags",
        "message_search_docs",
    ):
        (tmp_path / f"{table_name}.jsonl").write_text("{}\n", encoding="utf-8")

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
    assert any("CREATE SCHEMA IF NOT EXISTS personal_archive_dev.nlpdata" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS personal_archive_dev.nlpdata.message_search_docs" in stmt for stmt in sql_client.statements)
    assert any("UPDATE personal_archive_dev.nlpdata.message_person_links" in stmt for stmt in sql_client.statements)
    assert any("UPDATE personal_archive_dev.nlpdata.message_theme_tags" in stmt for stmt in sql_client.statements)
    assert any("UPDATE personal_archive_dev.nlpdata.message_search_docs" in stmt for stmt in sql_client.statements)
    assert any("INSERT INTO personal_archive_dev.nlpdata.nlp_runs" in stmt for stmt in sql_client.statements)
