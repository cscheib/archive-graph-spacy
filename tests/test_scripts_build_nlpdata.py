import json
import subprocess
from pathlib import Path


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
