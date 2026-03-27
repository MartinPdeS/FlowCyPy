try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"

import FlowCyPy.units as _
import FlowCyPy.opto_electronics.circuits as _
import FlowCyPy.digital_processing.classifier as _
from .flow_cytometer import FlowCytometer
from .fluidics import Fluidics
from .opto_electronics import OptoElectronics
from .digital_processing import DigitalProcessing


debug_mode = False
