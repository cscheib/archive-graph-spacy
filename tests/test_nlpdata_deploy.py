import json
from pathlib import Path

import pytest

from archive_graph_spacy.nlpdata.deploy import (
    DEFAULT_CATALOG,
    DEFAULT_SCHEMA,
    cleanup_staged_directory,
    deploy_staged_payload,
    stage_payload_directory,
)


class FakeSqlClient:
    def __init__(
        self,
        *,
        fail_on_statement: str | None = None,
        show_columns: dict[str, list[dict[str, object]]] | None = None,
    ) -> None:
        self.statements: list[str] = []
        self.fail_on_statement = fail_on_statement
        self.show_columns = show_columns or {}

    def execute(self, statement: str) -> dict[str, object]:
        if self.fail_on_statement and self.fail_on_statement in statement:
            raise RuntimeError("simulated statement failure")
        self.statements.append(statement)
        return {"status": {"state": "SUCCEEDED"}}

    def fetch_all(self, statement: str) -> list[dict[str, object]]:
        self.statements.append(statement)
        return self.show_columns.get(statement, [])


def _write_payload_fixture(tmp_path: Path, run_id: str = "run-123") -> None:
    (tmp_path / "nlp_runs.jsonl").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "run_scope": "sample-scope",
                "source_catalog": "personal_archive_dev",
                "started_at": "2026-03-08T00:00:00+00:00",
                "completed_at": "2026-03-08T00:00:10+00:00",
                "status": "completed",
                "input_interaction_count": 1,
                "output_row_counts": {},
                "quality_metrics": {},
                "publish_diagnostics": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "message_mentions.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "message_person_links.jsonl").write_text(
        json.dumps(
            {
                "link_id": "link-1",
                "run_id": run_id,
                "message_id": "m-001",
                "person_id": "p-001",
                "person_name": "Alice Example",
                "role": "sender",
                "link_origin": "explicit",
                "confidence": 0.9,
                "evidence_type": "email",
                "evidence_value": "alice@example.com",
                "source_interaction_id": "m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "candidate_assertions.jsonl").write_text(
        json.dumps(
            {
                "candidate_assertion_id": "ca-001",
                "run_id": run_id,
                "assertion_type": "relay_sender_identity",
                "subject_canonical_id": "m-001",
                "proposed_claim": "relay sender relay+alice@example.com maps to p-001",
                "evidence_refs": ["message:m-001", "sender:relay+alice@example.com"],
                "provenance_summary": "Derived from unresolved sender plus inferred link from message m-001",
                "confidence_level": 0.95,
                "generation_scope": "sample-scope",
                "generated_at": "2026-03-08T00:00:05+00:00",
                "review_class": "reviewable",
                "promotion_class": "promotion_eligible",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "candidate_assertions_summary.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "generation_scope": "sample-scope",
                "emitted_candidate_count": 1,
                "candidate_counts_by_type": {"relay_sender_identity": 1},
                "suppressed_counts": {},
                "example_candidate_ids": ["ca-001"],
                "generated_at": "2026-03-08T00:00:05+00:00",
                "reviewed_effect_counts": {"applied": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "reviewed_effects.jsonl").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "candidate_assertion_id": "ca-001",
                "assertion_type": "relay_sender_identity",
                "subject_canonical_id": "m-001",
                "result": "applied",
                "reason_code": "accepted_review",
                "details": "accepted reviewed input applied downstream effect",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "person_person_edges.jsonl").write_text(
        json.dumps(
            {
                "pair_id": "pair-001",
                "person_a_id": "p-001",
                "person_b_id": "p-002",
                "run_id": run_id,
                "generation_scope": "sample-scope",
                "strength_score": 1.0,
                "relationship_signal": "direct_participation",
                "direct_evidence_count": 1,
                "indirect_evidence_count": 0,
                "strongest_evidence_ref": "message:m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "person_person_edge_evidence.jsonl").write_text(
        json.dumps(
            {
                "pair_evidence_id": "ppe-001",
                "pair_id": "pair-001",
                "evidence_family": "direct_participation",
                "source_ref": "message:m-001",
                "contribution_score": 1.0,
                "rank_within_pair": 1,
                "message_ref": "m-001",
                "theme_refs": [],
                "provenance": "explicit participants on m-001",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phases.jsonl").write_text(
        json.dumps(
            {
                "phase_id": "phase-001",
                "run_id": run_id,
                "generation_scope": "sample-scope",
                "phase_index": 1,
                "start_at": "2026-03-08T00:00:00+00:00",
                "end_at": "2026-03-08T00:01:00+00:00",
                "interaction_count": 1,
                "representative_interaction_ref": "message:m-001",
                "boundary_reason": "time_gap_segmentation",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phase_central_people.jsonl").write_text(
        json.dumps(
            {
                "phase_id": "phase-001",
                "run_id": run_id,
                "person_id": "p-001",
                "rank": 1,
                "centrality_score": 2.0,
                "interaction_count": 1,
                "evidence_ref": "message:m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phase_theme_summaries.jsonl").write_text(
        json.dumps(
            {
                "phase_id": "phase-001",
                "run_id": run_id,
                "theme": "travel",
                "rank": 1,
                "theme_score": 0.8,
                "message_count": 1,
                "evidence_ref": "message:m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phase_pair_summaries.jsonl").write_text(
        json.dumps(
            {
                "phase_pair_id": "phase-pair-001",
                "phase_id": "phase-001",
                "pair_id": "pair-001",
                "run_id": run_id,
                "pair_rank": 1,
                "activity_score": 1.0,
                "relationship_signal": "direct_participation",
                "evidence_count": 1,
                "strongest_evidence_ref": "message:m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phase_pair_evidence.jsonl").write_text(
        json.dumps(
            {
                "phase_pair_evidence_id": "phase-ppe-001",
                "phase_pair_id": "phase-pair-001",
                "phase_id": "phase-001",
                "pair_id": "pair-001",
                "run_id": run_id,
                "source_ref": "message:m-001",
                "message_ref": "m-001",
                "evidence_family": "direct_participation",
                "rank_within_phase_pair": 1,
                "contribution_score": 1.0,
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phase_representative_interactions.jsonl").write_text(
        json.dumps(
            {
                "phase_id": "phase-001",
                "run_id": run_id,
                "interaction_ref": "message:m-001",
                "rank": 1,
                "selection_reason": "top_phase_activity",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "phase_diagnostics.jsonl").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "phase_id": "phase-001",
                "diagnostic_type": "boundary",
                "result": "retained",
                "reason_code": "gap_retained",
                "sample_ref": "message:m-001",
                "details": "retained boundary after 45 day gap",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "message_theme_tags.jsonl").write_text(
        json.dumps(
            {
                "theme_tag_id": "theme-1",
                "run_id": run_id,
                "message_id": "m-001",
                "theme": "travel",
                "confidence": 0.8,
                "evidence": "trip",
                "source_method": "keyword",
                "source_interaction_id": "m-001",
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "message_search_docs.jsonl").write_text(
        json.dumps(
            {
                "message_id": "m-001",
                "run_id": run_id,
                "source_interaction_id": "m-001",
                "source_type": "email",
                "timestamp": None,
                "subject_terms": [],
                "body_terms": ["trip"],
                "linked_person_ids": ["p-001"],
                "linked_person_names": ["Alice Example"],
                "explicit_person_ids": ["p-001"],
                "inferred_person_ids": [],
                "theme_labels": ["travel"],
                "time_facets": {},
                "is_current": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )


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
    _write_payload_fixture(tmp_path)

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
    assert result["publish_diagnostics"]["publish_outcome"] == "finalized"
    assert any("CREATE SCHEMA IF NOT EXISTS `personal_archive_dev`.`nlpdata`" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.candidate_assertions" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.candidate_assertions_summary" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.message_search_docs" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.person_person_edges" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.phases" in stmt for stmt in sql_client.statements)
    assert any("CREATE TABLE IF NOT EXISTS `personal_archive_dev`.`nlpdata`.phase_pair_summaries" in stmt for stmt in sql_client.statements)
    assert any("DELETE FROM `personal_archive_dev`.`nlpdata`.`candidate_assertions`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`message_person_links`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`person_person_edges`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`phases`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`phase_pair_summaries`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`phase_pair_evidence`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`message_theme_tags`" in stmt for stmt in sql_client.statements)
    assert any("UPDATE `personal_archive_dev`.`nlpdata`.`message_search_docs`" in stmt for stmt in sql_client.statements)
    assert any("INSERT INTO `personal_archive_dev`.`nlpdata`.nlp_runs" in stmt for stmt in sql_client.statements)
    assert any("INSERT INTO `personal_archive_dev`.`nlpdata`.candidate_assertions" in stmt for stmt in sql_client.statements)
    assert any("INSERT INTO `personal_archive_dev`.`nlpdata`.candidate_assertions_summary" in stmt for stmt in sql_client.statements)
    assert any("candidate_assertions_summary.json" in stmt for stmt in sql_client.statements)
    insert_index = next(i for i, stmt in enumerate(sql_client.statements) if "INSERT INTO `personal_archive_dev`.`nlpdata`.message_person_links" in stmt)
    deactivate_index = next(i for i, stmt in enumerate(sql_client.statements) if "UPDATE `personal_archive_dev`.`nlpdata`.`message_person_links`" in stmt)
    activate_index = max(i for i, stmt in enumerate(sql_client.statements) if "SET is_current = true" in stmt and "`message_person_links`" in stmt)
    assert insert_index < deactivate_index < activate_index
    assert "false" in sql_client.statements[insert_index]
    assert any(
        "UPDATE `personal_archive_dev`.`nlpdata`.`phases`" in stmt
        and "generation_scope = 'sample-scope'" in stmt
        for stmt in sql_client.statements
    )
    assert any(
        "UPDATE `personal_archive_dev`.`nlpdata`.`phase_pair_summaries`" in stmt
        and "FROM `personal_archive_dev`.`nlpdata`.`phases`" in stmt
        and "generation_scope = 'sample-scope'" in stmt
        for stmt in sql_client.statements
    )
    assert any(
        "INSERT INTO `personal_archive_dev`.`nlpdata`.phase_pair_evidence" in stmt
        and "\n  run_id,\n" in stmt
        for stmt in sql_client.statements
    )


def test_collect_bounded_publish_scope_tracks_non_message_identity_values(tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    from archive_graph_spacy.nlpdata.deploy import _collect_bounded_publish_scope

    scope = _collect_bounded_publish_scope(
        tmp_path,
        run_id="run-123",
        active_scope_message_ids=(),
    )

    assert "person_person_edges:pair-001" in scope.affected_identity_values
    assert "m-001" in scope.affected_message_ids


def test_phase_child_tables_finalize_against_phases_when_child_payload_is_empty(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)
    (tmp_path / "phase_central_people.jsonl").write_text("", encoding="utf-8")

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

    deploy_staged_payload(tmp_path, run_id="run-123")

    assert any(
        "UPDATE `personal_archive_dev`.`nlpdata`.`phase_central_people`" in stmt
        and "generation_scope = 'sample-scope'" in stmt
        for stmt in sql_client.statements
    )
    assert any(
        "UPDATE `personal_archive_dev`.`nlpdata`.`phase_central_people`" in stmt
        and "read_files('dbfs:/tmp/archive_graph_spacy/nlpdata/run-123/phase_central_people.jsonl'" in stmt
        for stmt in sql_client.statements
    )


def test_phase_scope_finalization_uses_run_scope_when_phase_payload_is_empty(
    monkeypatch, tmp_path: Path
) -> None:
    _write_payload_fixture(tmp_path)
    (tmp_path / "phases.jsonl").write_text("", encoding="utf-8")

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

    deploy_staged_payload(tmp_path, run_id="run-123")

    assert any(
        "UPDATE `personal_archive_dev`.`nlpdata`.`phases`" in stmt
        and "generation_scope = 'sample-scope'" in stmt
        for stmt in sql_client.statements
    )
    assert any(
        "UPDATE `personal_archive_dev`.`nlpdata`.`phase_central_people`" in stmt
        and "generation_scope = 'sample-scope'" in stmt
        for stmt in sql_client.statements
    )


def test_deactivate_all_current_phase_rows_sql_retire_all_current_phase_rows() -> None:
    from archive_graph_spacy.nlpdata.deploy import _deactivate_all_current_phase_rows_sql

    phases_sql = _deactivate_all_current_phase_rows_sql("personal_archive_dev", "nlpdata", "phases")
    children_sql = _deactivate_all_current_phase_rows_sql(
        "personal_archive_dev",
        "nlpdata",
        "phase_central_people",
    )

    assert "UPDATE `personal_archive_dev`.`nlpdata`.`phases`" in phases_sql
    assert "WHERE is_current = true" in phases_sql
    assert "generation_scope" not in phases_sql

    assert "UPDATE `personal_archive_dev`.`nlpdata`.`phase_central_people`" in children_sql
    assert "FROM `personal_archive_dev`.`nlpdata`.`phases`" in children_sql
    assert "WHERE is_current = true" in children_sql
    assert "generation_scope" not in children_sql


def test_deploy_staged_payload_adds_missing_contract_columns(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient(
        show_columns={
            "SHOW COLUMNS IN `personal_archive_dev`.`nlpdata`.`nlp_runs`": [
                {"col_name": "run_id"},
                {"col_name": "run_scope"},
                {"col_name": "source_catalog"},
                {"col_name": "started_at"},
                {"col_name": "completed_at"},
            ]
        }
    )

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

    deploy_staged_payload(tmp_path, run_id="run-123")

    assert any(
        "ALTER TABLE `personal_archive_dev`.`nlpdata`.`nlp_runs` ADD COLUMNS" in stmt
        and "`publish_diagnostics` STRING" in stmt
        for stmt in sql_client.statements
    )


def test_deploy_staged_payload_marks_partial_failure_as_rerunnable(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient(
        fail_on_statement="UPDATE `personal_archive_dev`.`nlpdata`.`message_theme_tags`\nSET is_current = true"
    )

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.get_workspace_client", lambda profile=None: object())
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: sql_client,
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory", lambda remote_dir, profile=None: None)

    result = deploy_staged_payload(tmp_path, run_id="run-123")

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["publish_outcome"] == "partial"
    assert diagnostics["recovery_action"] == "rerun_same_scope"
    assert diagnostics["manual_intervention_required"] is False
    assert diagnostics["error_detail"] == "simulated statement failure"
    assert "message_person_links" in diagnostics["finalized_tables"]
    assert "message_theme_tags" in diagnostics["failed_tables"]


def test_deploy_staged_payload_preserves_databricks_runtime_metadata(
    monkeypatch, tmp_path: Path
) -> None:
    _write_payload_fixture(tmp_path)
    run_rows = [
        {
            "run_id": "run-123",
            "run_scope": "sample-scope",
            "source_catalog": "personal_archive_dev",
            "started_at": "2026-03-08T00:00:00+00:00",
            "completed_at": "2026-03-08T00:00:10+00:00",
            "status": "completed",
            "input_interaction_count": 1,
            "output_row_counts": {},
            "quality_metrics": {},
            "publish_diagnostics": {
                "job_id": "586330214826449",
                "job_run_id": "187120647835483",
                "parent_job_run_id": "187120647835483",
                "task_run_id": "756240538904937",
                "task_key": "backfill_01_1974_2012",
                "task_name": "backfill_01_1974_2012",
            },
        }
    ]
    (tmp_path / "nlp_runs.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in run_rows),
        encoding="utf-8",
    )

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

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["job_id"] == "586330214826449"
    assert diagnostics["job_run_id"] == "187120647835483"
    assert diagnostics["parent_job_run_id"] == "187120647835483"
    assert diagnostics["task_run_id"] == "756240538904937"
    assert diagnostics["task_key"] == "backfill_01_1974_2012"
    assert diagnostics["task_name"] == "backfill_01_1974_2012"


def test_deploy_staged_payload_returns_diagnostics_when_persist_update_fails(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    sql_client = FakeSqlClient(
        fail_on_statement="UPDATE `personal_archive_dev`.`nlpdata`.`nlp_runs`\nSET publish_diagnostics ="
    )

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.get_workspace_client", lambda profile=None: object())
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: sql_client,
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory", lambda remote_dir, profile=None: None)

    result = deploy_staged_payload(tmp_path, run_id="run-123")

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["publish_outcome"] == "finalized"
    assert "diagnostics_persist_error" in diagnostics


def test_deploy_staged_payload_rejects_overlapping_active_scope(monkeypatch, tmp_path: Path) -> None:
    _write_payload_fixture(tmp_path)

    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.get_workspace_client", lambda profile=None: object())
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )
    monkeypatch.setattr("archive_graph_spacy.nlpdata.deploy.cleanup_staged_directory", lambda remote_dir, profile=None: None)

    result = deploy_staged_payload(
        tmp_path,
        run_id="run-123",
        active_scope_message_ids=(("m-001", "m-999"),),
    )

    diagnostics = result["publish_diagnostics"]
    assert diagnostics["publish_outcome"] == "failed"
    assert diagnostics["recovery_action"] == "serialize_overlapping_scope"
    assert diagnostics["manual_intervention_required"] is True
    assert diagnostics["overlap_policy"] == "overlapping_scope"


def test_staged_insert_sql_raises_if_current_state_pattern_is_missing(monkeypatch) -> None:
    monkeypatch.setitem(
        __import__("archive_graph_spacy.nlpdata.deploy", fromlist=["INSERT_SELECTS"]).INSERT_SELECTS,
        "message_person_links",
        "INSERT INTO {catalog}.{schema}.message_person_links SELECT 1",
    )

    from archive_graph_spacy.nlpdata.deploy import _staged_insert_sql

    with pytest.raises(RuntimeError, match="Expected to replace 'CAST\\(is_current AS BOOLEAN\\)'"):
        _staged_insert_sql(
            "message_person_links",
            catalog="`personal_archive_dev`",
            schema="`nlpdata`",
            remote_path="dbfs:/tmp/archive_graph_spacy/nlpdata/run-123/message_person_links.jsonl",
        )


def test_deploy_staged_payload_rejects_invalid_catalog_identifier(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.get_workspace_client",
        lambda profile=None: object(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.stage_payload_directory",
        lambda local_dir, run_id, profile=None: "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
    )

    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        deploy_staged_payload(tmp_path, run_id="run-123", catalog="personal_archive_dev;DROP SCHEMA x")


def test_deploy_staged_payload_rejects_invalid_run_id(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.get_workspace_client",
        lambda profile=None: object(),
    )
    monkeypatch.setattr(
        "archive_graph_spacy.nlpdata.deploy.DatabricksSqlClient",
        lambda workspace_client, warehouse_id: FakeSqlClient(),
    )

    with pytest.raises(ValueError, match="Invalid run_id"):
        deploy_staged_payload(tmp_path, run_id="../run-123")
