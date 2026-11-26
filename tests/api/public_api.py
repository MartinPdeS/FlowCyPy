import subprocess
import sys

import pytest

import FlowCyPy


def test_top_level_public_api_is_explicit():
    assert FlowCyPy.__all__ == [
        "__version__",
        "FlowCytometer",
        "EventCollection",
        "Fluidics",
        "distributions",
        "populations",
        "OptoElectronics",
        "circuits",
        "source",
        "DigitalProcessing",
        "classifier",
        "discriminator",
        "peak_locator",
        "ureg",
        "debug_mode",
        "DetectionAnalyzer",
    ]


def test_top_level_import_is_lazy():
    """Importing the package does not eagerly load simulation subsystems."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import FlowCyPy; "
                "assert 'FlowCyPy.flow_cytometer' not in sys.modules; "
                "assert 'FlowCyPy.opto_electronics' not in sys.modules; "
                "assert 'FlowCyPy.digital_processing' not in sys.modules"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stderr == ""


def test_fluidics_imports_in_fresh_interpreter():
    """Native event annotations must not prevent importing simulation modules."""
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from FlowCyPy.fluidics import Fluidics, PopulationEvents; "
                "from FlowCyPy.event_collection import EventCollection; "
                "from FlowCyPy import EventCollection as PublicCollection; "
                "assert PublicCollection is EventCollection and EventCollection().empty"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("export", ["DigitalProcessing", "FlowCytometer"])
def test_public_subsystems_initialize_native_units(export):
    """Each lazy public import works without an earlier units import."""
    subprocess.run(
        [
            sys.executable,
            "-c",
            f"import FlowCyPy; getattr(FlowCyPy, {export!r})",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
