from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
DATABRICKS_PATH = REPO_ROOT / "databricks.yml"
README_PATH = REPO_ROOT / "README.md"
PACKAGE_PATH = REPO_ROOT / "src/archive_graph_spacy"
PROJECT_VERSION_RE = re.compile(r'(?m)^version = "(?P<version>[^"]+)"$')
DATABRICKS_WHEEL_VERSION_RE = re.compile(r'(?m)^  wheel_version:\n(?:    .*\n)*?    default: "(?P<version>[^"]+)"$')
SEMVER_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")


def run_git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def read_version(text: str, pattern: re.Pattern[str], source_name: str) -> str:
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Could not read version from {source_name}")
    return match.group("version")


def read_project_version(text: str) -> str:
    return read_version(text, PROJECT_VERSION_RE, "pyproject.toml")


def read_bundle_wheel_version(text: str) -> str:
    return read_version(text, DATABRICKS_WHEEL_VERSION_RE, "databricks.yml")


def read_git_text(spec: str) -> str | None:
    result = run_git_command(["show", spec])
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "exists on disk, but not in" in stderr or "does not exist" in stderr or "invalid object name" in stderr:
            return None
        raise RuntimeError(stderr or f"git show {spec!r} failed")
    return result.stdout


def staged_changed_paths() -> list[str]:
    result = run_git_command(["diff", "--cached", "--name-only", "--diff-filter=ACMRD"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff --cached failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def working_tree_changed_paths() -> list[str]:
    tracked_result = run_git_command(["diff", "--name-only", "HEAD", "--diff-filter=ACMRD"])
    if tracked_result.returncode != 0:
        raise RuntimeError(tracked_result.stderr.strip() or "git diff HEAD failed")
    untracked_result = run_git_command(["ls-files", "--others", "--exclude-standard"])
    if untracked_result.returncode != 0:
        raise RuntimeError(untracked_result.stderr.strip() or "git ls-files failed")
    ordered_paths = [
        line.strip() for line in tracked_result.stdout.splitlines() if line.strip()
    ] + [line.strip() for line in untracked_result.stdout.splitlines() if line.strip()]
    return list(dict.fromkeys(ordered_paths))


def diff_text(path: str, *, mode: str) -> str:
    diff_args = ["diff", "--unified=0"]
    if mode == "staged":
        diff_args.append("--cached")
    else:
        diff_args.append("HEAD")
    result = run_git_command([*diff_args, "--", path])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git diff failed for {path}")
    return result.stdout


def pyproject_has_non_version_changes(diff_text: str) -> bool:
    for line in diff_text.splitlines():
        if not line or line.startswith(("diff --git", "index ", "--- ", "+++ ", "@@")):
            continue
        if line[0] not in {"+", "-"}:
            continue
        if line.startswith(('+version = "', '-version = "')):
            continue
        return True
    return False


def has_wheel_payload_changes(staged_paths: list[str], pyproject_diff_text: str) -> bool:
    for path in staged_paths:
        if path == README_PATH.name:
            return True
        if path.startswith(f"{PACKAGE_PATH.relative_to(REPO_ROOT).as_posix()}/"):
            return True
    return PYPROJECT_PATH.name in staged_paths and pyproject_has_non_version_changes(pyproject_diff_text)


def parse_base_version(version: str) -> tuple[int, int, int] | None:
    normalized = version.split(".post", 1)[0]
    match = SEMVER_RE.match(normalized)
    if not match:
        return None
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def version_was_bumped(previous_version: str | None, current_version: str) -> bool:
    if previous_version is None:
        return True
    if previous_version == current_version:
        return False
    previous_parts = parse_base_version(previous_version)
    current_parts = parse_base_version(current_version)
    if previous_parts is None or current_parts is None:
        return True
    return current_parts > previous_parts


def validate_versions(
    *,
    staged_paths: list[str],
    pyproject_diff_text: str,
    previous_project_version: str | None,
    current_project_version: str,
    current_bundle_version: str,
) -> list[str]:
    errors: list[str] = []
    if current_bundle_version != current_project_version:
        errors.append(
            "databricks.yml variables.wheel_version.default must match pyproject.toml [project].version "
            f"({current_bundle_version!r} != {current_project_version!r})."
        )
    if has_wheel_payload_changes(staged_paths, pyproject_diff_text) and not version_was_bumped(
        previous_project_version, current_project_version
    ):
        previous_display = previous_project_version or "<none>"
        errors.append(
            "Wheel-impacting staged changes require a base version bump in pyproject.toml "
            f"({previous_display!r} -> {current_project_version!r})."
        )
    return errors


def current_versions() -> tuple[str | None, str, str]:
    previous_pyproject = read_git_text(f"HEAD:{PYPROJECT_PATH.name}")
    previous_project_version = (
        read_project_version(previous_pyproject) if previous_pyproject is not None else None
    )
    current_project_version = read_project_version(PYPROJECT_PATH.read_text())
    current_bundle_version = read_bundle_wheel_version(DATABRICKS_PATH.read_text())
    return previous_project_version, current_project_version, current_bundle_version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when wheel-impacting staged changes do not bump the base wheel version."
    )
    parser.add_argument(
        "--mode",
        choices=("staged", "working-tree"),
        default=os.environ.get("WHEEL_VERSION_CHECK_MODE", "staged"),
        help="Check staged changes for pre-commit or working tree changes for bundle deploy.",
    )
    args = parser.parse_args(argv)

    changed_paths = staged_changed_paths() if args.mode == "staged" else working_tree_changed_paths()

    previous_project_version, current_project_version, current_bundle_version = current_versions()
    pyproject_diff_text = diff_text(PYPROJECT_PATH.name, mode=args.mode) if PYPROJECT_PATH.name in changed_paths else ""
    errors = validate_versions(
        staged_paths=changed_paths,
        pyproject_diff_text=pyproject_diff_text,
        previous_project_version=previous_project_version,
        current_project_version=current_project_version,
        current_bundle_version=current_bundle_version,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(
            "Bump [project].version in pyproject.toml and keep databricks.yml wheel_version in sync "
            "when wheel contents change.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
