#!/usr/bin/env python3
"""Check FlowCyPy's SCM-derived release metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "FlowCyPy" / "_version.py"


def source_version() -> str:
    """Return the generated source version."""
    match = re.search(r"^__version__\s*=\s*version\s*=\s*['\"]([^'\"]+)", VERSION_FILE.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise RuntimeError("could not find the generated package version")
    return match.group(1)


def main() -> int:
    """Check the dynamic project version and optionally an expected version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="expected version, optionally prefixed with v")
    arguments = parser.parse_args()
    try:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        if "version" not in project["project"].get("dynamic", []):
            raise RuntimeError("pyproject.toml must retain dynamic SCM versioning")
        version = source_version()
    except (KeyError, RuntimeError) as error:
        print(f"release check failed: {error}", file=sys.stderr)
        return 1
    expected = arguments.version.removeprefix("v") if arguments.version else version
    if version != expected:
        print(f"ERROR: FlowCyPy/_version.py declares {version}; expected {expected}", file=sys.stderr)
        return 1
    print(f"OK       FlowCyPy/_version.py: {version}")
    print(f"OK       pyproject.toml: dynamic SCM versioning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
