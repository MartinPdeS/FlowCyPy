.DEFAULT_GOAL := help

PYTHON ?= python3.13
BUILD_DIR ?= build
DOCS_BUILD_DIR ?= docs/build
SPHINXOPTS ?=
ROOT_DIR := $(CURDIR)
PYBIND11_DIR = $(shell $(PYTHON) -m pybind11 --cmakedir)
RELEASE_KIND := $(filter major minor patch,$(MAKECMDGOALS))

.PHONY: help docs docs-install configure build install quick rebuild editable clean quality test check release-check tag release major minor patch

help:
	@echo "FlowCyPy development commands"
	@echo ""
	@echo "  make editable              Build and install an editable package"
	@echo "  make test                  Run the test suite"
	@echo "  make quality               Run static checks"
	@echo "  make check                 Run quality and tests"
	@echo "  make release-check         Check release metadata"
	@echo "  make tag VERSION=vX.Y.Z    Create a release commit and annotated tag"
	@echo "  make release patch         Create and push the next patch release"
	@echo "  make release minor         Create and push the next minor release"
	@echo "  make release major         Create and push the next major release"
	@echo "  make docs                  Build the HTML documentation"
	@echo "  make docs-install          Install documentation dependencies"

docs-install:
	$(PYTHON) -m pip install -e ".[documentation]"

docs:
	MPLBACKEND=Agg $(PYTHON) -m sphinx -M html docs/source $(DOCS_BUILD_DIR) $(SPHINXOPTS)

quality:
	$(PYTHON) -m ruff check FlowCyPy tests

test:
	$(PYTHON) -m pytest --config-file=pytest.ini

check: quality test

release-check:
	$(PYTHON) -m martinpdes_maintenance.cli check $(if $(VERSION),--version $(VERSION),)

tag:
	$(PYTHON) -m martinpdes_maintenance.cli tag "$(VERSION)"

release:
	@test "$(words $(RELEASE_KIND))" -eq 1 || { echo "usage: make release [patch|minor|major]" >&2; exit 2; }
	@set -eu; release_tag="$$($(PYTHON) -m martinpdes_maintenance.cli next $(RELEASE_KIND))"; \
	$(PYTHON) -m martinpdes_maintenance.cli tag "$$release_tag"; \
	git push origin HEAD "refs/tags/$$release_tag"

major minor patch:
	@:

configure:
	cmake -S . -B $(BUILD_DIR) \
		-Dpybind11_DIR="$(PYBIND11_DIR)" \
		-DPython_EXECUTABLE="$$(which $(PYTHON))" \
		-DCMAKE_INSTALL_PREFIX="$(ROOT_DIR)"

build:
	cmake --build $(BUILD_DIR) -j

install:
	cmake --install $(BUILD_DIR)

uninstall:
	$(PYTHON) -m pip uninstall -y PyMieSim

quick: configure build install

rebuild: configure build install

editable:
	$(PYTHON) -m pip install --no-build-isolation -Cbuild-dir=build -Ceditable.rebuild=false -Ceditable.mode=inplace -e .

clean:
	rm -rf $(BUILD_DIR)
