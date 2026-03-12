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


def test_run_sample_uses_sibling_contacts_when_present(tmp_path) -> None:
    import shutil

    shutil.copy("data_samples/sample_messages.jsonl", tmp_path / "messages.jsonl")
    shutil.copy("data_samples/sample_contacts.jsonl", tmp_path / "contacts.jsonl")

    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.run_sample",
            str(tmp_path / "messages.jsonl"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload[0]["message_id"] == "m-001"


def test_run_sample_accepts_explicit_contacts_path(tmp_path) -> None:
    import shutil

    shutil.copy("data_samples/sample_messages.jsonl", tmp_path / "messages.jsonl")
    shutil.copy("data_samples/sample_contacts.jsonl", tmp_path / "contacts.jsonl")

    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.run_sample",
            str(tmp_path / "messages.jsonl"),
            str(tmp_path / "contacts.jsonl"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload[0]["message_id"] == "m-001"
