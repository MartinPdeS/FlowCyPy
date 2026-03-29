from .flow_cell import FlowCell
from . import populations
from . import distributions
from .scatterer_collection import ScattererCollection
from .main import Fluidics
from enum import Enum

from FlowCyPy.units import ureg


class SheathFlowRate(Enum):
    DEFAULT = 18 * ureg.milliliter / ureg.minute
    LOW = 20 * ureg.milliliter / ureg.minute
    MEDIUM = 30 * ureg.milliliter / ureg.minute
    HIGH = 40 * ureg.milliliter / ureg.minute


class SampleFlowRate(Enum):
    LOW = 10 * ureg.microliter / ureg.minute
    MEDIUM = 60 * ureg.microliter / ureg.minute
    HIGH = 120 * ureg.microliter / ureg.minute
