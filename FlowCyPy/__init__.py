try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"

from .flow_cytometer import FlowCytometer
from .fluidics import Fluidics
from .opto_electronics import OptoElectronics
from .signal_processing import SignalProcessing
from .simulation_settings import SimulationSettings

debug_mode = False
