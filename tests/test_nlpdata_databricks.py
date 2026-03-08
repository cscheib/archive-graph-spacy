from types import SimpleNamespace

import pytest

from archive_graph_spacy.nlpdata.databricks import (
    DatabricksSqlClient,
    DatabricksSqlError,
    get_workspace_client,
    quote_sql_string_literal,
    rows_from_result,
    validate_iso_date,
    validate_run_id,
)


def test_get_workspace_client_uses_profile(monkeypatch) -> None:
    created = []

    class FakeWorkspaceClient:
        def __init__(self, profile=None):
            created.append(profile)

    monkeypatch.setattr("archive_graph_spacy.nlpdata.databricks.WorkspaceClient", FakeWorkspaceClient)

    client = get_workspace_client("dev-profile")

    assert isinstance(client, FakeWorkspaceClient)
    assert created == ["dev-profile"]


def test_rows_from_result_maps_manifest_columns() -> None:
    result = SimpleNamespace(
        manifest=SimpleNamespace(
            schema=SimpleNamespace(columns=[SimpleNamespace(name="person_id"), SimpleNamespace(name="display_name")])
        ),
        result=SimpleNamespace(data_array=[["p-1", "Alice"], ["p-2", "Bob"]], next_chunk_internal_link=None),
    )

    rows = rows_from_result(result)

    assert rows == [
        {"person_id": "p-1", "display_name": "Alice"},
        {"person_id": "p-2", "display_name": "Bob"},
    ]


def test_sql_client_raises_on_failed_statement() -> None:
    failed = SimpleNamespace(
        status=SimpleNamespace(
            state=SimpleNamespace(value="FAILED"),
            error=SimpleNamespace(message="boom"),
        )
    )
    workspace_client = SimpleNamespace(
        statement_execution=SimpleNamespace(execute_statement=lambda **kwargs: failed)
    )

    client = DatabricksSqlClient(workspace_client, warehouse_id="warehouse-1")

    with pytest.raises(DatabricksSqlError, match="boom"):
        client.execute("SELECT 1")


def test_sql_client_polls_pending_statement_until_success() -> None:
    pending = SimpleNamespace(
        statement_id="stmt-1",
        status=SimpleNamespace(state=SimpleNamespace(value="PENDING")),
    )
    succeeded = SimpleNamespace(
        statement_id="stmt-1",
        status=SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED")),
        manifest=SimpleNamespace(schema=SimpleNamespace(columns=[])),
        result=SimpleNamespace(data_array=[], next_chunk_internal_link=None),
    )
    calls = {"count": 0}

    def execute_statement(**kwargs):
        return pending

    def get_statement(statement_id):
        calls["count"] += 1
        return succeeded

    workspace_client = SimpleNamespace(
        statement_execution=SimpleNamespace(
            execute_statement=execute_statement,
            get_statement=get_statement,
        )
    )

    client = DatabricksSqlClient(
        workspace_client,
        warehouse_id="warehouse-1",
        poll_interval_seconds=0.0,
        timeout_seconds=1.0,
    )

    result = client.execute("SELECT 1")

    assert result is succeeded
    assert calls["count"] == 1


def test_validate_run_id_rejects_path_like_values() -> None:
    with pytest.raises(ValueError, match="Invalid run_id"):
        validate_run_id("../run-123")


def test_validate_iso_date_rejects_invalid_dates() -> None:
    with pytest.raises(ValueError, match="Invalid ISO date"):
        validate_iso_date("2026-02-30")


def test_quote_sql_string_literal_escapes_single_quotes() -> None:
    assert quote_sql_string_literal("O'Brien") == "'O''Brien'"
