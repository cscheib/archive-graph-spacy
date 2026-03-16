"""Run and publish metadata helpers."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Mapping

from .models import BoundedPublishScope, PublishDiagnosticsRecord, RefreshRun

RUNTIME_TARGET_INTERACTIONS = 10_000
RUNTIME_TARGET_SECONDS = 15 * 60
MENTION_ID_TOKEN = re.compile(r"\b(?:mm|im)-[0-9a-f]{6,16}\b", re.IGNORECASE)


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


def build_phase_quality_metrics(
    *,
    suppressed_phase_count: int,
    phase_subdivision_count: int,
    phase_boundary_merged_count: int,
    phase_boundary_retained_count: int,
    phase_representative_interaction_cap: int,
    phase_pair_evidence_cap: int,
    phase_pair_evidence_phase_cap: int,
    phase_boundary_diagnostic_cap: int,
    phase_diagnostics_count: int,
) -> dict[str, int]:
    return {
        "suppressed_phase_count": suppressed_phase_count,
        "phase_subdivision_count": phase_subdivision_count,
        "phase_boundary_merged_count": phase_boundary_merged_count,
        "phase_boundary_retained_count": phase_boundary_retained_count,
        "phase_representative_interaction_cap": phase_representative_interaction_cap,
        "phase_pair_evidence_cap": phase_pair_evidence_cap,
        "phase_pair_evidence_phase_cap": phase_pair_evidence_phase_cap,
        "phase_boundary_diagnostic_cap": phase_boundary_diagnostic_cap,
        "phase_diagnostics_count": phase_diagnostics_count,
    }


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
    runtime_metadata: Mapping[str, object] | None = None,
) -> PublishDiagnosticsRecord:
    merged_runtime_metadata = merge_publish_diagnostics(runtime_metadata)
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
        job_id=_coerce_optional_str(merged_runtime_metadata.get("job_id")),
        job_run_id=_coerce_optional_str(merged_runtime_metadata.get("job_run_id")),
        parent_job_run_id=_coerce_optional_str(
            merged_runtime_metadata.get("parent_job_run_id")
        ),
        task_run_id=_coerce_optional_str(merged_runtime_metadata.get("task_run_id")),
        task_key=_coerce_optional_str(merged_runtime_metadata.get("task_key")),
        task_name=_coerce_optional_str(merged_runtime_metadata.get("task_name")),
    )


def _coerce_optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_databricks_runtime_metadata(
    *,
    job_id: str | None = None,
    job_run_id: str | None = None,
    task_run_id: str | None = None,
    task_key: str | None = None,
    task_name: str | None = None,
) -> dict[str, object]:
    """Build a normalized Databricks job hierarchy payload for run diagnostics."""
    resolved_job_id = _coerce_optional_str(job_id) or _coerce_optional_str(
        os.environ.get("DATABRICKS_JOB_ID")
    )
    resolved_job_run_id = _coerce_optional_str(job_run_id) or _coerce_optional_str(
        os.environ.get("DATABRICKS_JOB_RUN_ID")
    ) or _coerce_optional_str(os.environ.get("DATABRICKS_RUN_ID"))
    resolved_task_run_id = _coerce_optional_str(task_run_id) or _coerce_optional_str(
        os.environ.get("DATABRICKS_TASK_RUN_ID")
    )
    resolved_task_key = _coerce_optional_str(task_key) or _coerce_optional_str(
        os.environ.get("DATABRICKS_TASK_KEY")
    )
    resolved_task_name = _coerce_optional_str(task_name) or _coerce_optional_str(
        os.environ.get("DATABRICKS_TASK_NAME")
    ) or resolved_task_key
    if resolved_task_key is None:
        resolved_task_key = resolved_task_name

    runtime_metadata: dict[str, object] = {}
    if resolved_job_id is not None:
        runtime_metadata["job_id"] = resolved_job_id
    if resolved_job_run_id is not None:
        runtime_metadata["job_run_id"] = resolved_job_run_id
        runtime_metadata["parent_job_run_id"] = resolved_job_run_id
    if resolved_task_run_id is not None:
        runtime_metadata["task_run_id"] = resolved_task_run_id
    if resolved_task_key is not None:
        runtime_metadata["task_key"] = resolved_task_key
    if resolved_task_name is not None:
        runtime_metadata["task_name"] = resolved_task_name
    return runtime_metadata


def merge_publish_diagnostics(
    *payloads: Mapping[str, object] | None,
) -> dict[str, object]:
    """Merge publish-diagnostics payloads, ignoring empty values."""
    merged: dict[str, object] = {}
    for payload in payloads:
        if not payload:
            continue
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            merged[key] = value
    return merged


def semantic_replay_key(
    *,
    assertion_type: str,
    subject_canonical_id: str,
    proposed_claim: str,
    generation_scope: str | None = None,
) -> str:
    normalized_claim = " ".join(proposed_claim.strip().split()).casefold()
    normalized_claim = MENTION_ID_TOKEN.sub("<mention>", normalized_claim)
    digest = hashlib.sha1(
        f"{assertion_type}|{subject_canonical_id}|{normalized_claim}|{generation_scope or ''}".encode("utf-8")
    ).hexdigest()[:16]
    return f"srk-{digest}"
