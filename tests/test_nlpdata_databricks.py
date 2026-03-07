from types import SimpleNamespace

import pytest

from archive_graph_spacy.nlpdata.databricks import (
    DatabricksSqlClient,
    DatabricksSqlError,
    get_workspace_client,
    rows_from_result,
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
