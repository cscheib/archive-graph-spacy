import json
import subprocess
from pathlib import Path

from archive_graph_spacy.scripts import build_nlpdata as build_nlpdata_module


def test_build_nlpdata_outputs_expected_tables() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.build_nlpdata",
            "data_samples",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["status"] == "completed"
    assert payload["input_interaction_count"] == 2
    assert "message_person_links" in payload["output_row_counts"]
    assert "runtime_seconds" in payload["quality_metrics"]


def test_build_nlpdata_writes_candidate_outputs_and_summary() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.build_nlpdata",
            "data_samples/candidate_assertions",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    derived_dir = Path(payload["derived_dir"])

    assert payload["output_row_counts"]["candidate_assertions"] == 5
    assert payload["candidate_assertions_summary"]["emitted_candidate_count"] == 5
    assert (derived_dir / "candidate_assertions.jsonl").exists()
    assert (derived_dir / "candidate_assertions_summary.json").exists()


def test_build_nlpdata_writes_reviewed_and_pair_outputs_for_phase3_fixture() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.build_nlpdata",
            "data_samples/feedback_relationship_outputs",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    derived_dir = Path(payload["derived_dir"])

    assert payload["output_row_counts"]["reviewed_effects"] >= 2
    assert payload["output_row_counts"]["person_person_edges"] >= 1
    assert payload["candidate_assertions_summary"]["reviewed_effect_counts"]["applied"] >= 1
    assert (derived_dir / "reviewed_effects.jsonl").exists()
    assert (derived_dir / "person_person_edges.jsonl").exists()
    assert (derived_dir / "person_person_edge_evidence.jsonl").exists()


def test_main_surfaces_publish_diagnostics_when_deploying(monkeypatch, capsys, tmp_path: Path) -> None:
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()
    (sample_dir / "contacts.jsonl").write_text(
        '{"person_id":"p-alice","display_name":"Alice Example","emails":["alice@example.com"],"entity_type":"person"}\n',
        encoding="utf-8",
    )
    (sample_dir / "messages.jsonl").write_text(
        '{"message_id":"m-001","source":"email","sender":"alice@example.com","recipients":[],"subject":"Trip hotel","body":"Flight hotel trip"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        build_nlpdata_module,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "export_dir": str(sample_dir),
                "source": "bundle",
                "output_dir": None,
                "deploy": True,
                "profile": None,
                "catalog": "personal_archive_dev",
                "schema": "nlpdata",
                "warehouse_id": "warehouse-1",
                "message_limit": None,
                "people_limit": None,
                "start_date": None,
                "end_date": None,
                "keep_staged_files": False,
            },
        )(),
    )
    monkeypatch.setattr(
        build_nlpdata_module,
        "deploy_staged_payload",
        lambda *args, **kwargs: {
            "catalog": "personal_archive_dev",
            "schema": "nlpdata",
            "remote_dir": "dbfs:/tmp/archive_graph_spacy/nlpdata/run-123",
            "warehouse_id": "warehouse-1",
            "publish_diagnostics": {
                "publish_outcome": "finalized",
                "recovery_action": "none",
                "manual_intervention_required": False,
            },
        },
    )

    assert build_nlpdata_module.main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["deployment"]["publish_diagnostics"]["publish_outcome"] == "finalized"
    assert payload["publish_diagnostics"]["recovery_action"] == "none"
