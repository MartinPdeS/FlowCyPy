import importlib.machinery
import importlib.util
import sys
from pathlib import Path

from FlowCyPy.units import ureg  # noqa: F401

from .system import OptoElectronics, Digitizer, circuits, Detector, Amplifier, source


def _load_native_module(name: str):
    """Load a sibling native module without source-module fallback during bootstrap."""
    package_directory = Path(__file__).parent
    module_path = next(
        package_directory / f"{name}{suffix}"
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
        if (package_directory / f"{name}{suffix}").exists()
    )
    qualified_name = f"{__name__}.{name}"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load native module {qualified_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


ScatteringModel = _load_native_module("coupling_model").ScatteringModel

__all__ = [
    "Amplifier",
    "Detector",
    "Digitizer",
    "OptoElectronics",
    "ScatteringModel",
    "circuits",
    "source",
]
