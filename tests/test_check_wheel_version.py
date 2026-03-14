from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.check_wheel_version import (
    diff_text,
    has_wheel_payload_changes,
    pyproject_has_non_version_changes,
    validate_versions,
    version_was_bumped,
    working_tree_changed_paths,
)


def test_pyproject_diff_ignores_version_only_changes() -> None:
    diff_text = """\
diff --git a/pyproject.toml b/pyproject.toml
@@ -2 +2 @@
-version = "0.1.2"
+version = "0.1.3"
"""
    assert not pyproject_has_non_version_changes(diff_text)


def test_pyproject_diff_detects_dependency_changes() -> None:
    diff_text = """\
diff --git a/pyproject.toml b/pyproject.toml
@@ -5,0 +6 @@
+  "pytest>=8.4,<9.0",
"""
    assert pyproject_has_non_version_changes(diff_text)


def test_has_wheel_payload_changes_for_package_code() -> None:
    assert has_wheel_payload_changes(["src/archive_graph_spacy/nlpdata/pipeline.py"], "")


def test_has_wheel_payload_changes_for_pyproject_metadata_changes() -> None:
    diff_text = """\
@@ -5,0 +6 @@
+description = "new"
"""
    assert has_wheel_payload_changes(["pyproject.toml"], diff_text)


def test_version_was_bumped_requires_forward_progress() -> None:
    assert version_was_bumped("0.1.2", "0.1.3")
    assert not version_was_bumped("0.1.2", "0.1.2")
    assert not version_was_bumped("0.1.3", "0.1.2")


def test_validate_versions_requires_bump_for_wheel_payload_changes() -> None:
    errors = validate_versions(
        staged_paths=["src/archive_graph_spacy/nlpdata/pipeline.py"],
        pyproject_diff_text="",
        previous_project_version="0.1.2",
        current_project_version="0.1.2",
        current_bundle_version="0.1.2",
    )
    assert errors == [
        "Wheel-impacting staged changes require a base version bump in pyproject.toml ('0.1.2' -> '0.1.2')."
    ]


def test_validate_versions_requires_databricks_sync() -> None:
    errors = validate_versions(
        staged_paths=["pyproject.toml", "databricks.yml"],
        pyproject_diff_text='-version = "0.1.2"\n+version = "0.1.3"\n',
        previous_project_version="0.1.2",
        current_project_version="0.1.3",
        current_bundle_version="0.1.2",
    )
    assert errors == [
        "databricks.yml variables.wheel_version.default must match pyproject.toml [project].version "
        "('0.1.2' != '0.1.3')."
    ]


def test_working_tree_changed_paths_merges_tracked_and_untracked(monkeypatch) -> None:
    class Result:
        def __init__(self, stdout: str, returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    calls: list[list[str]] = []

    def fake_run_git_command(args: list[str]) -> Result:
        calls.append(args)
        if args[:3] == ["diff", "--name-only", "HEAD"]:
            return Result("src/archive_graph_spacy/nlpdata/pipeline.py\nREADME.md\n")
        if args[:2] == ["ls-files", "--others"]:
            return Result("src/archive_graph_spacy/new_module.py\nREADME.md\n")
        raise AssertionError(args)

    monkeypatch.setattr("tools.check_wheel_version.run_git_command", fake_run_git_command)

    assert working_tree_changed_paths() == [
        "src/archive_graph_spacy/nlpdata/pipeline.py",
        "README.md",
        "src/archive_graph_spacy/new_module.py",
    ]
    assert calls == [
        ["diff", "--name-only", "HEAD", "--diff-filter=ACMRD"],
        ["ls-files", "--others", "--exclude-standard"],
    ]


def test_diff_text_uses_head_in_working_tree_mode(monkeypatch) -> None:
    class Result:
        def __init__(self) -> None:
            self.stdout = "diff"
            self.stderr = ""
            self.returncode = 0

    observed_args: list[list[str]] = []

    def fake_run_git_command(args: list[str]) -> Result:
        observed_args.append(args)
        return Result()

    monkeypatch.setattr("tools.check_wheel_version.run_git_command", fake_run_git_command)

    assert diff_text("pyproject.toml", mode="working-tree") == "diff"
    assert observed_args == [["diff", "--unified=0", "HEAD", "--", "pyproject.toml"]]
