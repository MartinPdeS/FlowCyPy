import matplotlib.pyplot as plt
import pandas as pd
from MPSPlots import helper
from TypedUnit import Time, validate_units

from FlowCyPy import distribution, population  # noqa: F401
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.scatterer_collection import ScattererCollection


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

    @validate_units
    def generate_event_dataframe(self, run_time: Time) -> pd.DataFrame:
        """
        Generates a DataFrame of events based on the scatterer collection and flow cell properties.

        Parameters
        ----------
        run_time : Time
            The duration of the acquisition in seconds.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing event data for the scatterers.
        """
        event_dataframe = self.flow_cell._generate_event_dataframe(
            self.scatterer_collection.populations, run_time=run_time
        )

        self.scatterer_collection.fill_dataframe_with_sampling(event_dataframe)

        return event_dataframe

    @helper.pre_plot(nrows=1, ncols=1)
    @validate_units
    def plot(self, axes: plt.Axes, run_time: Time) -> None:
        r"""
        Plot the spatial distribution of sampled particles with velocity color-coding.

        This method samples a specified number of particles from the focused sample stream
        and generates a scatter plot of their positions in the y-z plane. The particles are
        color-coded by their local x-direction velocity using a continuous colormap. In addition,
        the plot includes overlays that represent the channel boundaries (sheath + sample regions)
        and the sample region boundaries.

        A dedicated colorbar is added to the right of the main axes and its height is adjusted
        to match the plot, using a separate axes created with ``mpl_toolkits.axes_grid1.make_axes_locatable``.

        Parameters
        ----------
        run_time : Time
            The duration of the acquisition in seconds.

        Notes
        -----
        - The plot uses orthogonal splines and a horizontal layout (left-to-right).
        - Global styling parameters such as node style and edge styling are applied.
        - The method requires that the object defines ``self.width``, ``self.height``,
        ``self.sample.width``, ``self.sample.height``, and a method ``self.sample_particles(n_samples)``.
        - The colorbar is created with a dedicated axes to ensure it spans the full height of the plot.

        """
        sampling = self.generate_event_dataframe(run_time=run_time)

        length_units = self.flow_cell.width.units

        x = sampling["x"].pint.to(length_units).pint.quantity.magnitude
        y = sampling["y"].pint.to(length_units).pint.quantity.magnitude
        velocity = sampling["Velocity"].pint.to("meter/second").pint.quantity

        sc = axes.scatter(
            x,
            y,
            c=velocity.magnitude,
            cmap="viridis",
            edgecolor="black",
            label="Particle sampling",
        )

        # Create a dedicated colorbar axes next to the main axes:
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        divider = make_axes_locatable(axes)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(sc, cax=cax, label=f"Velocity [{sampling['Velocity'].pint.units}]")

        axes.set(
            xlabel=f"X [{length_units}]",
            ylabel=f"Y [{length_units}]",
            title="Particle Spatial Distribution and Speed",
        )

        self.flow_cell.sheath._add_to_plot(
            ax=axes, length_units=length_units, color="lightblue", label="Sheath Region"
        )

        self.flow_cell.sample._add_to_plot(
            ax=axes, length_units=length_units, color="green", label="Sample Region"
        )

        axes.set_aspect("equal")
        axes.legend(loc="upper right")
