from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.deploy_bundle import (
    build_deploy_version,
    compute_wheel_fingerprint,
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
