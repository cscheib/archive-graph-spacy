"""Databricks helpers backed by the official SDK."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from databricks.sdk import WorkspaceClient
else:
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        WorkspaceClient = None  # type: ignore[misc, assignment]


class DatabricksSqlError(RuntimeError):
    """Raised when Databricks SQL statement execution fails."""


def get_workspace_client(profile: str | None = None) -> "WorkspaceClient":
    if WorkspaceClient is None:
        raise ImportError("databricks-sdk is required. Run `uv sync --dev` after updating dependencies.")
    if profile is None:
        profile = os.environ.get("DATABRICKS_PROFILE")
    if profile:
        return WorkspaceClient(profile=profile)
    return WorkspaceClient()


class DatabricksSqlClient:
    def __init__(self, workspace_client: "WorkspaceClient", warehouse_id: str) -> None:
        self.workspace_client = workspace_client
        self.warehouse_id = warehouse_id

    def execute(self, statement: str) -> Any:
        result = self.workspace_client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=statement,
            wait_timeout="30s",
        )
        try:
            setattr(result, "_client", self.workspace_client)
        except Exception:
            pass
        status = getattr(result, "status", None)
        state = getattr(getattr(status, "state", None), "value", None)
        if state == "FAILED":
            error = getattr(status, "error", None)
            message = getattr(error, "message", None) or "Databricks SQL execution failed"
            raise DatabricksSqlError(message)
        return result

    def fetch_all(self, statement: str) -> list[dict[str, Any]]:
        return rows_from_result(self.execute(statement))


def rows_from_result(result: Any) -> list[dict[str, Any]]:
    manifest = getattr(result, "manifest", None)
    schema = getattr(manifest, "schema", None)
    columns = [getattr(column, "name", None) for column in getattr(schema, "columns", [])]
    payload = getattr(result, "result", None)
    rows = [dict(zip(columns, row, strict=False)) for row in getattr(payload, "data_array", [])]

    next_link = getattr(payload, "next_chunk_internal_link", None)
    while next_link:
        chunk = result._client.statement_execution.get_statement_result_chunk_n(  # type: ignore[attr-defined]
            statement_id=result.statement_id,
            chunk_index=int(next_link.rstrip("/").split("/")[-1]),
        )
        rows.extend(
            dict(zip(columns, row, strict=False))
            for row in getattr(getattr(chunk, "result", None), "data_array", [])
        )
        next_link = getattr(getattr(chunk, "result", None), "next_chunk_internal_link", None)
    return rows
