import subprocess


def test_query_edges_prints_top_pairs() -> None:
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
