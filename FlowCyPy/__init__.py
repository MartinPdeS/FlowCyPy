try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"

from .cytometer import FlowCytometer
from .simulation_settings import SimulationSettings
from .opto_electronics import OptoElectronics
from .fluidics import Fluidics
from .signal_processing import SignalProcessing

debug_mode = False