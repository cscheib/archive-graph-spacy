import json

from archive_graph_spacy.nlpdata.models import BoundedPublishScope
from archive_graph_spacy.nlpdata.runs import (
    build_databricks_runtime_metadata,
    build_phase_quality_metrics,
    build_publish_diagnostics,
    classify_scope_overlap,
    merge_publish_diagnostics,
)
from archive_graph_spacy.scripts.build_nlpdata import build_nlpdata


def test_build_nlpdata_is_safe_to_rerun(tmp_path) -> None:
    export_dir = tmp_path / "sample"
    export_dir.mkdir()
    (export_dir / "contacts.jsonl").write_text(
        '{"person_id":"p-alice","display_name":"Alice Example","emails":["alice@example.com"],"entity_type":"person"}\n',
        encoding="utf-8",
    )
    (export_dir / "messages.jsonl").write_text(
        '{"message_id":"m-001","source":"email","sender":"alice@example.com","recipients":[],"subject":"Trip hotel","body":"Flight hotel trip"}\n',
        encoding="utf-8",
    )

    first = build_nlpdata(export_dir)
    second = build_nlpdata(export_dir)

    docs_path = export_dir / "derived" / "nlpdata" / "message_search_docs.jsonl"
    rows = [json.loads(line) for line in docs_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert len(rows) == 1
    assert rows[0]["message_id"] == "m-001"


def test_classify_scope_overlap_distinguishes_same_overlap_and_independent() -> None:
    assert classify_scope_overlap(("m-001",), (("m-001",),)) == "same_scope_rerun"
    assert classify_scope_overlap(("m-001", "m-002"), (("m-002", "m-003"),)) == "overlapping_scope"
    assert classify_scope_overlap(("m-001",), (("m-010",),)) == "non_overlapping_scope"


def test_build_phase_quality_metrics_reports_bounded_phase_outputs() -> None:
    metrics = build_phase_quality_metrics(
        suppressed_phase_count=1,
        phase_subdivision_count=0,
        phase_boundary_merged_count=1,
        phase_boundary_retained_count=2,
        phase_boundary_diagnostic_cap=4,
        phase_representative_interaction_cap=3,
        phase_pair_evidence_cap=5,
        phase_pair_evidence_phase_cap=5,
        phase_diagnostics_count=9,
    )

    assert metrics == {
        "suppressed_phase_count": 1,
        "phase_subdivision_count": 0,
        "phase_boundary_merged_count": 1,
        "phase_boundary_retained_count": 2,
        "phase_boundary_diagnostic_cap": 4,
        "phase_representative_interaction_cap": 3,
        "phase_pair_evidence_cap": 5,
        "phase_pair_evidence_phase_cap": 5,
        "phase_diagnostics_count": 9,
    }


def test_build_databricks_runtime_metadata_adds_job_hierarchy_aliases(monkeypatch) -> None:
    monkeypatch.setenv("DATABRICKS_JOB_ID", "586330214826449")
    monkeypatch.setenv("DATABRICKS_JOB_RUN_ID", "187120647835483")
    monkeypatch.setenv("DATABRICKS_TASK_RUN_ID", "756240538904937")

    metadata = build_databricks_runtime_metadata(task_name="refresh_global_phases")

    assert metadata == {
        "job_id": "586330214826449",
        "job_run_id": "187120647835483",
        "parent_job_run_id": "187120647835483",
        "task_run_id": "756240538904937",
        "task_key": "refresh_global_phases",
        "task_name": "refresh_global_phases",
    }


def test_build_publish_diagnostics_carries_runtime_metadata() -> None:
    scope = BoundedPublishScope(
        run_id="run-123",
        run_scope="sample-scope",
        affected_message_ids=("m-001",),
        overlap_class="same_scope_rerun",
    )

    diagnostics = build_publish_diagnostics(
        scope=scope,
        publish_stage="finalized",
        publish_outcome="finalized",
        recovery_action="none",
        staged_path="dbfs:/tmp/run-123",
        finalized_tables=("nlp_runs",),
        failed_tables=(),
        manual_intervention_required=False,
        runtime_metadata={
            "job_id": "586330214826449",
            "job_run_id": "187120647835483",
            "parent_job_run_id": "187120647835483",
            "task_run_id": "756240538904937",
            "task_key": "backfill_01_1974_2012",
            "task_name": "backfill_01_1974_2012",
        },
    ).to_record()

    assert diagnostics["job_id"] == "586330214826449"
    assert diagnostics["job_run_id"] == "187120647835483"
    assert diagnostics["task_run_id"] == "756240538904937"
    assert diagnostics["task_key"] == "backfill_01_1974_2012"


def test_merge_publish_diagnostics_ignores_empty_values() -> None:
    merged = merge_publish_diagnostics(
        {"publish_outcome": "finalized", "job_id": "586330214826449"},
        {"task_name": "refresh_global_phases", "task_key": ""},
        {"job_run_id": None, "task_run_id": "756240538904937"},
    )

    assert merged == {
        "publish_outcome": "finalized",
        "job_id": "586330214826449",
        "task_name": "refresh_global_phases",
        "task_run_id": "756240538904937",
    }
