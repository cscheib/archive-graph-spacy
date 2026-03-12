import subprocess


def _build_edges_for_data_samples() -> None:
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.build_edges",
            "data_samples",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_query_edges_prints_top_pairs() -> None:
    _build_edges_for_data_samples()

    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.query_edges",
            "data_samples/derived",
            "--query",
            "top_pairs",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Alice Example" in completed.stdout
    assert "Bob Example" in completed.stdout


def test_query_edges_hides_owner_from_top_pairs() -> None:
    _build_edges_for_data_samples()

    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.query_edges",
            "data_samples/derived",
            "--query",
            "top_pairs",
            "--owner-person-id",
            "p-alice",
            "--owner-mode",
            "hide",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Alice Example" not in completed.stdout


def test_query_edges_hides_owner_from_top_mentions() -> None:
    _build_edges_for_data_samples()

    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.query_edges",
            "data_samples/derived",
            "--query",
            "top_mentions",
            "--owner-person-id",
            "p-bob",
            "--owner-mode",
            "hide",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Bob Example" not in completed.stdout
