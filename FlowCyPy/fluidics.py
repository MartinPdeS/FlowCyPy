from FlowCyPy.scatterer_collection import ScattererCollection

from FlowCyPy.simulation_settings import SimulationSettings  # noqa: F401
from FlowCyPy.binary.flow_cell import FlowCell  # noqa: F401
from FlowCyPy.binary import distributions, populations  # noqa: F401


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
