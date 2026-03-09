from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
VERSION_RE = re.compile(r'(?m)^version = "(?P<version>[^"]+)"$')
WHEEL_INPUTS = ("README.md", "pyproject.toml", "src/archive_graph_spacy")


def read_project_version(pyproject_text: str) -> str:
    match = VERSION_RE.search(pyproject_text)
    if not match:
        raise ValueError("Could not find [project].version in pyproject.toml")
    return match.group("version")


def strip_post_release(version: str) -> str:
    return version.split(".post", 1)[0]


def iter_wheel_files() -> list[Path]:
    files: list[Path] = []
    for relative in WHEEL_INPUTS:
        path = REPO_ROOT / relative
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def compute_wheel_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in iter_wheel_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:12]


def build_deploy_version(base_version: str, fingerprint: str | None = None) -> str:
    wheel_hash = fingerprint or compute_wheel_fingerprint()
    wheel_hash_number = int(wheel_hash, 16)
    return f"{strip_post_release(base_version)}.post{wheel_hash_number}"


def replace_project_version(pyproject_text: str, version: str) -> str:
    updated, count = VERSION_RE.subn(f'version = "{version}"', pyproject_text, count=1)
    if count != 1:
        raise ValueError("Could not replace [project].version in pyproject.toml")
    return updated


def run_command(args: list[str]) -> None:
    subprocess.run(args, cwd=REPO_ROOT, check=True)


def deploy_bundle(target: str) -> str:
    original_text = PYPROJECT_PATH.read_text()
    base_version = read_project_version(original_text)
    deploy_version = build_deploy_version(base_version)
    PYPROJECT_PATH.write_text(replace_project_version(original_text, deploy_version))
    try:
        run_command(
            [
                "databricks",
                "bundle",
                "deploy",
                "-t",
                target,
                "--var",
                f"wheel_version={deploy_version}",
            ]
        )
    finally:
        PYPROJECT_PATH.write_text(original_text)
    return deploy_version


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deploy the Databricks bundle with a deterministic wheel version derived from wheel contents."
    )
    parser.add_argument("target", nargs="?", default="dev", help="Databricks bundle target")
    args = parser.parse_args()
    deploy_version = deploy_bundle(args.target)
    print(f"Deployed bundle with wheel version {deploy_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
