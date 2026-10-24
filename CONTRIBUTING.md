# Contributing to FlowCyPy

Thank you for improving FlowCyPy. Focused bug fixes, validation cases,
documentation corrections, and feature contributions are welcome.

## Development setup

FlowCyPy requires Python 3.11 or newer, CMake, a C++ compiler, pybind11, and
FFTW. Install the platform FFTW development package before building.

```bash
git clone https://github.com/MartinPdeS/FlowCyPy.git
cd FlowCyPy
make editable
make test
```

Rebuild the editable installation after changing native sources. Do not
hand-edit `FlowCyPy/_version.py`; the release helper updates it alongside
`pyproject.toml` and the Conda recipe.

## Contribution expectations

- Add tests for each behaviour change and use documented analytical,
  numerical, or experimental references for validation when available.
- Exercise public Python APIs and document units, physical assumptions, and
  numerical limits.
- Keep examples small enough for the documentation build.
- Do not commit generated documentation, build products, caches, or bytecode.

Before opening a pull request, run the relevant focused checks followed by:

```bash
make quality
make test
make release-check
```

Keep pull requests focused and describe the motivation, public behaviour,
verification, and platform/compiler details for native changes.

## Releases

Semantic release commands create and publish both the release commit and its
annotated tag:

```bash
make release patch
make release minor
make release major
```

Use `make tag VERSION=vX.Y.Z` when a local, reviewable tag is preferred.

## Shared release tooling

Install the pinned release tool in the interpreter used by Make, without
rebuilding this package:

```sh
python -m pip install "martinpdes-maintenance==0.2.2"
make release-check PYTHON=python
```

The same dependency is available through the project's `release` extra.
`tools/check_release.py`, `tools/next_release_version.py`, and
`tools/release_tag.py` are compatibility wrappers around `mps-maintenance`.
Package-specific metadata paths live in `[tool.mps-maintenance]` in
`pyproject.toml`. Release tooling is not a runtime dependency.

Preview the next release's metadata changes from a clean, full clone:

```sh
python tools/release_tag.py vX.Y.Z --dry-run
```

Fetch tags before selecting a version. Existing `make tag` and `make release`
commands keep their local-tag and push behavior respectively. The shared tool
requires an unused stable tag and a clean working tree. It stages only configured
release metadata and never pushes itself. If committing or tagging fails,
inspect `git status` and `git log -1` before recovering or retrying.

Package versions are explicit in `[project].version`. Builds do not derive
versions from Git tags or require setuptools-scm. Release commands update the
project version, package version file, and Conda recipe together.
