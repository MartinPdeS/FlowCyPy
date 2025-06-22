try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"

from .cytometer import FlowCytometer
from .scatterer_collection import ScattererCollection
from .detector import Detector
from .source import GaussianBeam, AstigmaticGaussianBeam
from .noises import NoiseSetting
from .signal_digitizer import SignalDigitizer
from .amplifier import TransimpedanceAmplifier
from .opto_electronics import OptoElectronics
from .flow_cell import FlowCell
from .fluidics import Fluidics
from .instances import *  # populations + PIN, PMT, APD,

debug_mode = False