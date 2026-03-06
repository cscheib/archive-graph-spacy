import subprocess
from pathlib import Path


def test_visualize_ego_writes_html(tmp_path: Path) -> None:
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

    output_path = tmp_path / "ego.html"
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.visualize_ego",
            "data_samples/derived",
            "p-alice",
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    html = output_path.read_text(encoding="utf-8")
    assert "Alice Example" in html
    assert "p-alice" in html
    assert "Graph Guide" in html
    assert "co-participant messages" in html


def test_visualize_ego_can_hide_owner_neighbor(tmp_path: Path) -> None:
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

    output_path = tmp_path / "ego_hidden_owner.html"
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "archive_graph_spacy.scripts.visualize_ego",
            "data_samples/derived",
            "p-bob",
            "--output",
            str(output_path),
            "--owner-person-id",
            "p-alice",
            "--owner-mode",
            "hide",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    html = output_path.read_text(encoding="utf-8")
    assert output_path.exists()
    assert "Alice Example" not in html
