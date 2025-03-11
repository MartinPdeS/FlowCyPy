try:
    from ._version import version as __version__  # noqa: F401

except ImportError:
    __version__ = "0.0.0"


from .cytometer import FlowCytometer
from .scatterer_collection import ScattererCollection, CouplingModel
# from .population import Population
from .detector import Detector
from .source import GaussianBeam, AstigmaticGaussianBeam
from .noises import NoiseSetting
from .signal_digitizer import SignalDigitizer
