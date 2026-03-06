import subprocess
from pathlib import Path


def test_visualize_graph_writes_html(tmp_path: Path) -> None:
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

    output_path = tmp_path / "graph.html"
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.visualize_graph",
            "data_samples/derived",
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    html = output_path.read_text(encoding="utf-8")
    assert output_path.exists()
    assert "Alice Example" in html
    assert "Bob Example" in html
    assert "Graph Guide" in html
    assert "co-participant messages" in html
