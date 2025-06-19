import pandas as pd
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.flow_cell import FlowCell

from FlowCyPy import units

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

    def generate_event_dataframe(self, run_time: units.Quantity) -> pd.DataFrame:
        """
        Generates a DataFrame of events based on the scatterer collection and flow cell properties.

        Parameters
        ----------
        run_time : pint.Quantity
            The duration of the acquisition in seconds.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing event data for the scatterers.
        """
        event_dataframe = self.flow_cell._generate_event_dataframe(
            self.scatterer_collection.populations,
            run_time=run_time
        )

        self.scatterer_collection.fill_dataframe_with_sampling(
            event_dataframe
        )

        return event_dataframe