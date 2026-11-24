from enum import Enum

from FlowCyPy.units import ureg

from . import distributions, populations
from .flow_cell import FlowCell
from .population_events import PopulationEvents
from .scatterer_collection import ScattererCollection
from .system import Fluidics


class SheathFlowRate(Enum):
    """Preset sheath-flow operating points used by convenience APIs."""

    DEFAULT = 18 * ureg.milliliter / ureg.minute
    LOW = 20 * ureg.milliliter / ureg.minute
    MEDIUM = 30 * ureg.milliliter / ureg.minute
    HIGH = 40 * ureg.milliliter / ureg.minute


class SampleFlowRate(Enum):
    """Preset sample-flow operating points used by convenience APIs."""

    LOW = 10 * ureg.microliter / ureg.minute
    MEDIUM = 60 * ureg.microliter / ureg.minute
    HIGH = 120 * ureg.microliter / ureg.minute


__all__ = [
    "FlowCell",
    "Fluidics",
    "PopulationEvents",
    "SampleFlowRate",
    "ScattererCollection",
    "SheathFlowRate",
    "distributions",
    "populations",
]
