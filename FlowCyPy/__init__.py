try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"

import FlowCyPy.units as _
from .fluidics import Fluidics, distributions, populations
import FlowCyPy.opto_electronics.circuits as _
import FlowCyPy.digital_processing.classifier as _
from .flow_cytometer import FlowCytometer
from .units import ureg
from .opto_electronics import OptoElectronics, circuits, source
from .digital_processing import (
    DigitalProcessing,
    classifier,
    discriminator,
    peak_locator,
)
from .workflow import Workflow


debug_mode = False

__all__ = [
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
