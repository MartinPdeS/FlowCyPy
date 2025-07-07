import pandas as pd
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.flow_cell import FlowCell
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from FlowCyPy import units
from FlowCyPy import helper
from FlowCyPy import population # noqa: F401
from FlowCyPy import distribution # noqa: F401

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

    @helper.validate_input_units(run_time=units.second)
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

    @helper.validate_input_units(run_time=units.second)
    def plot(self, run_time: units.Quantity, figure_size: tuple = (7, 4), ax: plt.Axes = None, show: bool = True) -> None:
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
        n_samples : int
            Number of particles to sample and plot.
        figure_size : tuple, optional
            Figure size (width, height) in inches. Default is (7, 4).
        ax : matplotlib.axes.Axes, optional
            A matplotlib Axes instance to draw the plot on. If not provided, a new figure and axes
            are created.
        show : bool, optional
            Whether to display the plot immediately. Default is True.

        Returns
        -------
        matplotlib.axes.Axes
            The Axes instance with the plot.

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

        # Create plot
        if ax is None:
            with plt.style.context(mps):
                _, ax = plt.subplots(1, 1, figsize=figure_size)

        x = sampling['x'].pint.to(length_units).pint.quantity.magnitude
        y = sampling['y'].pint.to(length_units).pint.quantity.magnitude
        velocity = sampling['Velocity'].pint.to("meter/second").pint.quantity

        sc = ax.scatter(
            x,
            y,
            c=velocity.magnitude,
            cmap="viridis",
            edgecolor="black",
            label='Particle sampling'
        )

        # Create a dedicated colorbar axes next to the main axes:
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(sc, cax=cax, label=f"Velocity [{sampling['Velocity'].pint.units}]")

        ax.set(
            xlabel=f"X [{length_units}]",
            ylabel=f"Y [{length_units}]",
            title="Particle Spatial Distribution and Speed"
        )

        self.flow_cell.sheath._add_to_plot(
            ax=ax,
            length_units=length_units,
            color='lightblue',
            label='Sheath Region'
        )

        self.flow_cell.sample._add_to_plot(
            ax=ax,
            length_units=length_units,
            color='green',
            label='Sample Region'

        )

        ax.set_aspect('equal')
        plt.tight_layout()
        ax.legend(loc='upper right')

        if show:
            plt.show()

        return ax