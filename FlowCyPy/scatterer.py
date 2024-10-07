from typing import List, Optional
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from dataclasses import dataclass, field
import seaborn as sns
import pandas as pd
from FlowCyPy.units import Quantity, refractive_index_unit, particle, liter
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.population import Population
from FlowCyPy.utils import PropertiesReport
from FlowCyPy.distribution import Base as BaseDistribution

@dataclass
class Scatterer(PropertiesReport):
    """
    Defines and manages the size and refractive index distributions of scatterers (particles)
    passing through a flow cytometer. This class generates random scatterer sizes and refractive
    indices based on a list of provided distributions (e.g., Normal, LogNormal, Uniform, etc.).

    Parameters
    ----------
    refractive_index : Union[float, List[distribution.Base]]
        A single refractive index or a list of refractive index distributions.
    size : Union[float, List[distribution.Base]]
        A single particle size or a list of size distributions.
    coupling_factor : str, optional
        The type of coupling factor to use. Options are 'rayleigh' or 'uniform'. Default is 'rayleigh'.
    """

    populations: List[Population] = field(default_factory=lambda : [])
    coupling_factor: Optional[str] = 'mie'  # Coupling factor type ('mie', 'rayleigh', 'uniform')
    medium_refractive_index: float = 1.0 * refractive_index_unit # Refractive index or refractive index distributions

    def initialize(self, flow_cell: FlowCell) -> None:
        """Initializes particle size, refractive index, and medium refractive index distributions."""
        self.flow_cell = flow_cell

        for population in self.populations:
            population.initialize(flow_cell=self.flow_cell)

        self.dataframe = pd.concat(
            [p.dataframe for p in self.populations],
            axis=0,
            keys=[p.name for p in self.populations],
        )

        self.dataframe.index.names = ['Population', 'Index']

        self.n_events = len(self.dataframe)

    def plot(self, show: bool = True, figure_size: tuple = (5, 5), log_plot: bool = False) -> None:
        """
        Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn `jointplot`.

        This method plots the relationship between the scatterer sizes and refractive indices, including both
        their marginal distributions (as Kernel Density Estimates, KDEs) and a scatter plot overlay.

        The `jointplot` displays:
            - **Marginal KDE plots** for scatterer sizes (on the x-axis) and refractive indices (on the y-axis).
            - **Scatter plot** showing the relationship between the sizes and refractive indices.
            - **Joint KDE plot** to highlight the density of points in the scatter plot.

        The marginal and joint KDEs are filled to provide better visualization of density.
        """
        # Reset the index if necessary (to handle MultiIndex)
        df_reset = self.dataframe.reset_index()

        # Extract the units from the pint-pandas columns
        x_unit = df_reset['Size'].pint.units

        with plt.style.context(mps):
            g = sns.jointplot(
                data=df_reset,
                x='Size',
                y='RefractiveIndex',
                hue='Population',
                kind='kde',
                alpha=0.8,
                fill=True,
                joint_kws={'alpha': 0.7}
            )

            sns.scatterplot(
                data=df_reset,
                x='Size',
                y='RefractiveIndex',
                hue='Population',
                ax=g.ax_joint,
                alpha=0.6,
                zorder=1
            )

            # Set the x and y labels with units
            g.ax_joint.set_xlabel(f"Size [{x_unit}]")

            plt.tight_layout()

            if log_plot:
                ax = g.ax_joint
                ax.set_xscale('log')
                ax.set_yscale('log')
                g.ax_marg_x.set_xscale('log')
                g.ax_marg_y.set_yscale('log')


            if show:
                plt.show()

    def print_properties(self) -> None:
        """
        Prints specific properties of the Scatterer instance, such as coupling factor and medium refractive index.
        This method calls the parent class method to handle the actual property printing logic.

        Overrides:
            Scatterer.print_properties: Extends the parent method to print the desired properties.

        Returns:
            None
        """
        min_delta_position = abs(self.dataframe['Time'].diff()).min().to_compact()
        mean_delta_position = self.dataframe['Time'].diff().mean().to_compact()

        _dict = {
            'coupling factor': self.coupling_factor,
            'medium refractive index': self.medium_refractive_index,
            'minimum time between events': min_delta_position,
            'average time between events': mean_delta_position
        }

        super(Scatterer, self).print_properties(**_dict)

        for population in self.populations:
            population.print_properties()


    def add_population(self, name: str, size: BaseDistribution, refractive_index: BaseDistribution, concentration: Quantity) -> Population:
        """
        Adds a population to the Scatterer instance with the specified attributes: name, size distribution,
        refractive index distribution, and concentration.

        Args:
            name (str): The name of the population.
            size (BaseDistribution): The size distribution of the population.
            refractive_index (BaseDistribution): The refractive index distribution of the population.
            concentration (Quantity): The concentration of the population.

        Returns:
            None
        """
        if concentration.dimensionality != (particle / liter).dimensionality:
            raise ValueError(
            f"Invalid concentration dimensionality: {concentration.dimensionality}. Expected dimensionality is 'particles per liter' or similar."
        )

        population = Population(
            name=name,
            size=size,
            refractive_index=refractive_index,
            concentration=concentration
        )

        self.populations.append(population)

        return population
