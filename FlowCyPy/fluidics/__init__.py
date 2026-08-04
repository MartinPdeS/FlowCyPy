import sys

from .flow_cell import FlowCell
from . import populations
from . import distributions
from . import _population_events
from . import _scatterer_collection
from .main import Fluidics
from enum import Enum

from FlowCyPy.units import ureg

PopulationEvents = _population_events.PopulationEvents
PopulationEvents.__module__ = f"{__name__}.population_events"
sys.modules[f"{__name__}.population_events"] = _population_events

ScattererCollection = _scatterer_collection.ScattererCollection
ScattererCollection.__module__ = f"{__name__}.scatterer_collection"
sys.modules[f"{__name__}.scatterer_collection"] = _scatterer_collection


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
