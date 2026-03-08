"""Run and publish metadata helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .models import BoundedPublishScope, PublishDiagnosticsRecord, RefreshRun

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
    publish_diagnostics: dict[str, object] | None = None,
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
        publish_diagnostics=publish_diagnostics or {},
    )


def classify_scope_overlap(
    scope_message_ids: tuple[str, ...],
    active_scope_message_ids: tuple[tuple[str, ...], ...],
) -> str:
    if not scope_message_ids:
        return "unknown"
    scope_set = set(scope_message_ids)
    for other_scope in active_scope_message_ids:
        other_set = set(other_scope)
        if scope_set == other_set:
            return "same_scope_rerun"
        if scope_set & other_set:
            return "overlapping_scope"
    return "non_overlapping_scope"


def build_publish_diagnostics(
    *,
    scope: BoundedPublishScope,
    publish_stage: str,
    publish_outcome: str,
    recovery_action: str,
    staged_path: str,
    finalized_tables: tuple[str, ...],
    failed_tables: tuple[str, ...],
    manual_intervention_required: bool,
) -> PublishDiagnosticsRecord:
    return PublishDiagnosticsRecord(
        run_id=scope.run_id,
        publish_scope=scope.to_record(),
        publish_stage=publish_stage,
        publish_outcome=publish_outcome,
        overlap_policy=scope.overlap_class,
        recovery_action=recovery_action,
        staged_path=staged_path,
        finalized_tables=finalized_tables,
        failed_tables=failed_tables,
        manual_intervention_required=manual_intervention_required,
    )
