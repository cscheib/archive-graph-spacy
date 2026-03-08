"""Run metadata helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .models import RefreshRun

RUNTIME_TARGET_INTERACTIONS = 10_000
RUNTIME_TARGET_SECONDS = 15 * 60


def new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:12]}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def meets_runtime_goal(interaction_count: int, duration_seconds: float) -> bool:
    if duration_seconds <= 0:
        return True
    required_rate = RUNTIME_TARGET_INTERACTIONS / RUNTIME_TARGET_SECONDS
    observed_rate = interaction_count / duration_seconds
    return observed_rate >= required_rate


def build_refresh_run(
    *,
    run_id: str,
    run_scope: str,
    source_catalog: str,
    started_at: datetime,
    completed_at: datetime,
    input_interaction_count: int,
    output_row_counts: dict[str, int],
    quality_metrics: dict[str, int | float | bool],
    status: str = "completed",
) -> RefreshRun:
    return RefreshRun(
        run_id=run_id,
        run_scope=run_scope,
        source_catalog=source_catalog,
        started_at=started_at,
        completed_at=completed_at,
        status=status,
        input_interaction_count=input_interaction_count,
        output_row_counts=output_row_counts,
        quality_metrics=quality_metrics,
    )
