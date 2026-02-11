import pandas as pd
from TypedUnit import ureg, Time, ParticleFlux, Concentration, Particle
import numpy as np

from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy import population  # noqa: F401
from FlowCyPy.simulation_settings import SimulationSettings  # noqa: F401
from FlowCyPy.binary.flow_cell import FlowCell  # noqa: F401
from FlowCyPy.binary import distributions  # noqa: F401


class Fluidics:
    def __init__(self, scatterer_collection: ScattererCollection, flow_cell: FlowCell):
        """
        Initializes the Fluidics system with a scatterer collection and a flow cell.

        Parameters
        ----------
        scatterer_collection : ScattererCollection, optional
            The collection of particles or scatterers to be processed in the flow cytometer.
        flow_cell : FlowCell, optional
            The flow cell through which the particles will pass.
        """
        self.scatterer_collection = scatterer_collection
        self.flow_cell = flow_cell
