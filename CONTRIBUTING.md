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
hand-edit `FlowCyPy/_version.py`; SCM versioning generates it for releases.

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
