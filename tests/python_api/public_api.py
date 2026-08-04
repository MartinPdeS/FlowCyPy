import subprocess
import sys

import FlowCyPy


def test_top_level_public_api_is_explicit():
    assert FlowCyPy.__all__ == [
        "__version__",
        "FlowCytometer",
        "Workflow",
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
    ]


def test_top_level_import_is_lazy():
    """Importing the package does not eagerly load simulation subsystems."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import FlowCyPy; "
            "assert 'FlowCyPy.workflow' not in sys.modules; "
            "assert 'FlowCyPy.opto_electronics' not in sys.modules; "
            "assert 'FlowCyPy.digital_processing' not in sys.modules",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stderr == ""
