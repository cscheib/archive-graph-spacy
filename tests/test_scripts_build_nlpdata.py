import json
import subprocess


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
