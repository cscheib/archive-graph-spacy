"""Databricks helpers backed by the official SDK."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from datetime import date
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


@dataclass(frozen=True)
class _StatementResultWithClient:
    result: Any
    client: Any

    @property
    def _client(self) -> Any:
        return self.client

    def __getattr__(self, name: str) -> Any:
        return getattr(self.result, name)


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_RUN_ID_RE = re.compile(r"^run-[A-Za-z0-9_-]{1,64}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def quote_sql_identifier(value: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return f"`{value}`"


def validate_run_id(value: str) -> str:
    if not _RUN_ID_RE.fullmatch(value):
        raise ValueError(f"Invalid run_id: {value!r}")
    return value


def validate_iso_date(value: str) -> str:
    if not _ISO_DATE_RE.fullmatch(value):
        raise ValueError(f"Invalid ISO date: {value!r}")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date: {value!r}") from exc
    return value


def quote_sql_string_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def get_workspace_client(profile: str | None = None) -> "WorkspaceClient":
    if WorkspaceClient is None:
        raise ImportError("databricks-sdk is required. Run `uv sync` after updating dependencies.")
    if profile is None:
        profile = os.environ.get("DATABRICKS_PROFILE")
    if profile:
        return WorkspaceClient(profile=profile)
    return WorkspaceClient()


class DatabricksSqlClient:
    def __init__(
        self,
        workspace_client: "WorkspaceClient",
        warehouse_id: str,
        *,
        poll_interval_seconds: float = 1.0,
        timeout_seconds: float = 300.0,
    ) -> None:
        self.workspace_client = workspace_client
        self.warehouse_id = warehouse_id
        self.poll_interval_seconds = poll_interval_seconds
        self.timeout_seconds = timeout_seconds

    def execute(self, statement: str) -> Any:
        result = self.workspace_client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=statement,
            wait_timeout="30s",
        )
        wrapped_result = _StatementResultWithClient(result=result, client=self.workspace_client)
        status = getattr(result, "status", None)
        state = getattr(getattr(status, "state", None), "value", None)
        if state == "FAILED":
            error = getattr(status, "error", None)
            message = getattr(error, "message", None) or "Databricks SQL execution failed"
            raise DatabricksSqlError(message)
        if state == "SUCCEEDED":
            return wrapped_result

        statement_id = getattr(result, "statement_id", None)
        if not statement_id:
            raise DatabricksSqlError("Databricks SQL statement did not return a statement_id")

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            result = self.workspace_client.statement_execution.get_statement(statement_id)
            wrapped_result = _StatementResultWithClient(result=result, client=self.workspace_client)
            status = getattr(result, "status", None)
            state = getattr(getattr(status, "state", None), "value", None)
            if state == "SUCCEEDED":
                return wrapped_result
            if state == "FAILED":
                error = getattr(status, "error", None)
                message = getattr(error, "message", None) or "Databricks SQL execution failed"
                raise DatabricksSqlError(message)
            if state in {"CANCELED", "CLOSED"}:
                raise DatabricksSqlError(f"Databricks SQL statement ended in state {state}")
            time.sleep(self.poll_interval_seconds)
        raise DatabricksSqlError("Timed out waiting for Databricks SQL statement completion")

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
