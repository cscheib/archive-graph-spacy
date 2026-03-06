import json
import subprocess


def test_run_sample_outputs_summary() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.run_sample",
            "data_samples/sample_messages.jsonl",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload[0]["message_id"] == "m-001"
    assert payload[0]["summary"]["linked_mentions"] >= 1
