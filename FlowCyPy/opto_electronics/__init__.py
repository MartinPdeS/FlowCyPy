import importlib.machinery
import importlib.util
import sys
from pathlib import Path

from FlowCyPy.units import ureg  # noqa: F401

from .system import OptoElectronics, Digitizer, circuits, Detector, Amplifier, source


def _load_native_module(name: str):
    """Load a sibling native module from the checkout or installed package."""
    package_directory = Path(__file__).parent
    package_parts = Path(*__name__.split("."))
    candidates = [
        package_directory / f"{name}{suffix}"
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
    ]
    candidates.extend(
        Path(search_path) / package_parts / f"{name}{suffix}"
        for search_path in sys.path
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
    )
    module_path = next((path for path in candidates if path.is_file()), None)
    if module_path is None:
        raise ImportError(
            f"Native extension {__name__}.{name!s} is not installed. "
            "Build FlowCyPy before importing its compiled components."
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
