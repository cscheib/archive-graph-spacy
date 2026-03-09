from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.deploy_bundle import (
    DIST_PATH,
    build_deploy_version,
    compute_wheel_fingerprint,
    expected_wheel_path,
    remove_stale_build_artifacts,
    read_project_version,
    replace_project_version,
)


def test_read_project_version_extracts_version() -> None:
    text = '[project]\nname = "archive-graph-spacy"\nversion = "0.1.0"\n'
    assert read_project_version(text) == "0.1.0"


def test_build_deploy_version_uses_wheel_fingerprint() -> None:
    version = build_deploy_version("0.1.0", fingerprint="00000000000a")
    assert version == "0.1.0.post10"


def test_replace_project_version_updates_only_project_version() -> None:
    original = (
        '[project]\n'
        'name = "archive-graph-spacy"\n'
        'version = "0.1.0"\n'
        '\n'
        '[tool.example]\n'
        'other_version = "leave-me-alone"\n'
    )
    updated = replace_project_version(original, "0.1.0.post10")
    assert 'version = "0.1.0.post10"' in updated
    assert 'other_version = "leave-me-alone"' in updated


def test_compute_wheel_fingerprint_is_stable_for_same_tree() -> None:
    first = compute_wheel_fingerprint()
    second = compute_wheel_fingerprint()
    assert first == second


def test_remove_stale_build_artifacts_deletes_existing_package_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("tools.deploy_bundle.DIST_PATH", tmp_path)
    old_wheel = tmp_path / "archive_graph_spacy-0.1.0-py3-none-any.whl"
    old_sdist = tmp_path / "archive_graph_spacy-0.1.0.tar.gz"
    unrelated = tmp_path / "other-package-1.0.0.whl"
    old_wheel.write_text("wheel")
    old_sdist.write_text("sdist")
    unrelated.write_text("keep")

    remove_stale_build_artifacts()

    assert not old_wheel.exists()
    assert not old_sdist.exists()
    assert unrelated.exists()


def test_expected_wheel_path_matches_deploy_version_name(monkeypatch) -> None:
    monkeypatch.setattr("tools.deploy_bundle.DIST_PATH", Path("/tmp/dist"))
    assert expected_wheel_path("0.1.0.post10") == Path(
        "/tmp/dist/archive_graph_spacy-0.1.0.post10-py3-none-any.whl"
    )
