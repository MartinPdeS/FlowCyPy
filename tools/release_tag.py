#!/usr/bin/env python3
"""Create a FlowCyPy release commit and annotated semantic-version tag."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "FlowCyPy" / "_version.py"
TAG_PATTERN = re.compile(r"v(?P<version>(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))$")


def run(*command: str, capture_output: bool = False, env: dict[str, str] | None = None) -> str:
    """Run a repository command and return stripped standard output."""
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=capture_output, env=env)
    return completed.stdout.strip() if capture_output else ""


def main() -> int:
    """Create a release commit and annotated tag without pushing either."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="annotated release tag, for example v1.1.1")
    arguments = parser.parse_args()
    match = TAG_PATTERN.fullmatch(arguments.tag)
    if match is None:
        print("release aborted: tag must use vMAJOR.MINOR.PATCH, for example v1.1.1", file=sys.stderr)
        return 1
    try:
        if run("git", "status", "--porcelain", capture_output=True):
            raise RuntimeError("working tree is not clean; commit or stash changes before creating a release tag")
        if run("git", "tag", "--list", arguments.tag, capture_output=True):
            raise RuntimeError(f"tag {arguments.tag} already exists")
        environment = os.environ.copy()
        environment["SETUPTOOLS_SCM_PRETEND_VERSION"] = match.group("version")
        run(sys.executable, "-m", "vcs_versioning", "--force-write-version-files", env=environment)
        if not VERSION_FILE.exists():
            raise RuntimeError("SCM versioning did not generate FlowCyPy/_version.py")
        run("git", "add", "FlowCyPy/_version.py")
        run("git", "commit", "-m", f"Release {arguments.tag}")
        run("git", "tag", "-a", arguments.tag, "-m", f"Release {arguments.tag}")
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"release aborted: {error}", file=sys.stderr)
        return 1
    print(f"created release commit and annotated tag {arguments.tag}")
    print("Push it when ready with: git push origin HEAD --tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
