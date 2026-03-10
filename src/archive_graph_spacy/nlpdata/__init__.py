"""Derived NLP search-workspace helpers."""

from __future__ import annotations

from pathlib import Path

from .models import PipelineResult, SourceBundle

__all__ = ["build_pipeline_payload", "run_pipeline", "write_pipeline_payload"]


def run_pipeline(
    bundle: SourceBundle,
    *,
    run_scope: str,
    source_catalog: str = "personal_archive_dev",
) -> PipelineResult:
    from .pipeline import run_pipeline as _run_pipeline

    return _run_pipeline(bundle, run_scope=run_scope, source_catalog=source_catalog)


def build_pipeline_payload(export_dir: str | Path) -> dict[str, object]:
    from .pipeline import build_pipeline_payload as _build_pipeline_payload

    return _build_pipeline_payload(export_dir)


def write_pipeline_payload(export_dir: str | Path, payload: dict[str, object]) -> Path:
    from .pipeline import write_pipeline_payload as _write_pipeline_payload

    return _write_pipeline_payload(export_dir, payload)
