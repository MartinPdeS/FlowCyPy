from typing import List, Optional, Union
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from dataclasses import field
from pydantic.dataclasses import dataclass
import seaborn as sns
import pandas as pd
from FlowCyPy.units import Quantity, refractive_index_unit, particle, liter
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.population import Population
from FlowCyPy.utils import PropertiesReport
from FlowCyPy.distribution import Base as BaseDistribution
from enum import Enum

config_dict = dict(arbitrary_types_allowed=True, extra='forbid')


class CouplingModel(Enum):
    MIE = 'mie'
    RAYLEIGH = 'rayleigh'
    UNIFORM = 'uniform'


@dataclass(config=config_dict, slots=True)
class Scatterer(PropertiesReport):
    """
    Defines and manages the size and refractive index distributions of scatterers (particles)
    passing through a flow cytometer. This class generates random scatterer sizes and refractive
    indices based on a list of provided distributions (e.g., Normal, LogNormal, Uniform, etc.).

    Parameters
    ----------
    populations : List[Population]
        A list of Population instances that define different scatterer populations.
    coupling_model : Optional[CouplingModel], optional
        The type of coupling factor to use (CouplingModel.MIE, CouplingModel.RAYLEIGH, CouplingModel.UNIFORM). Default is CouplingModel.MIE.
    medium_refractive_index : float
        The refractive index of the medium. Default is 1.0.
    """

    medium_refractive_index: Quantity = 1.0 * refractive_index_unit
    populations: List[Population] = field(default_factory=lambda: [])
    coupling_model: Optional[CouplingModel] = CouplingModel.MIE

    flow_cell: FlowCell = None
    n_events: int = None
    dataframe: pd.DataFrame = None

    def initialize(self, flow_cell: FlowCell) -> None:
        """
        Initializes particle size, refractive index, and medium refractive index distributions.

        Parameters
        ----------
        flow_cell : FlowCell
            An instance of the FlowCell class that describes the flow cell being used.

        Returns
        -------
        None
        """
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

    def plot(self, ax: Optional[plt.Axes] = None, show: bool = True, figure_size: tuple = (5, 5), log_plot: bool = False) -> None:
        """
        Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn jointplot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            An existing matplotlib axes to plot on. If None, a new figure and axes will be created. Default is None.
        show : bool, optional
            Whether to display the plot. Default is True.
        figure_size : tuple, optional
            The size of the figure to be displayed. Default is (5, 5).
        log_plot : bool, optional
            Whether to use logarithmic scales for the plot axes. Default is False.

        Returns
        -------
        None
        """
        df_reset = self.dataframe.reset_index()
        x_unit = df_reset['Size'].pint.units

        with plt.style.context(mps):
            g = sns.jointplot(
                data=df_reset,
                x='Size',
                y='RefractiveIndex',
                hue='Population',
                kind='scatter',
                alpha=0.8
            )

        g.ax_joint.set_xlabel(f"Size [{x_unit}]")

        if log_plot:
            g.ax_joint.set_xscale('log')
            g.ax_joint.set_yscale('log')
            g.ax_marg_x.set_xscale('log')
            g.ax_marg_y.set_yscale('log')

        plt.tight_layout()

        if show:
            plt.show()

    def print_properties(self) -> None:
        """
        Prints specific properties of the Scatterer instance, such as coupling factor and medium refractive index.

        Returns
        -------
        None
        """
        min_delta_position = abs(self.dataframe['Time'].diff()).min().to_compact()
        mean_delta_position = self.dataframe['Time'].diff().mean().to_compact()

        _dict = {
            'coupling factor': self.coupling_model.value,
            'medium refractive index': self.medium_refractive_index,
            'minimum time between events': min_delta_position,
            'average time between events': mean_delta_position
        }

        super(Scatterer, self).print_properties(**_dict)

        for population in self.populations:
            population.print_properties()

    def add_population(self, name: str, size: BaseDistribution, refractive_index: BaseDistribution, concentration: Quantity) -> 'Scatterer':
        """
        Adds a population to the Scatterer instance with the specified attributes.

        Parameters
        ----------
        name : str
            The name of the population.
        size : BaseDistribution
            The size distribution of the population.
        refractive_index : BaseDistribution
            The refractive index distribution of the population.
        concentration : Quantity
            The concentration of the population. Must have the dimensionality of 'particles per liter'.

        Returns
        -------
        Scatterer
            The Scatterer instance (to support chaining).

        Raises
        ------
        ValueError
            If the concentration does not have the expected dimensionality.
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
        return self

    def remove_population(self, name: str) -> 'Scatterer':
        """
        Removes a population from the Scatterer instance by name.

        Parameters
        ----------
        name : str
            The name of the population to remove.

        Returns
        -------
        Scatterer
            The Scatterer instance (to support chaining).

        Raises
        ------
        ValueError
            If the population with the specified name does not exist.
        """
        population_names = [p.name for p in self.populations]
        if name not in population_names:
            raise ValueError(f"Population '{name}' not found in Scatterer.")

        self.populations = [p for p in self.populations if p.name != name]
        return self

    def add_to_ax(self, *axes) -> None:
        """
        Adds vertical lines representing events for each population to the provided axes.

        Parameters
        ----------
        *axes : matplotlib.axes.Axes
            One or more matplotlib axes to which the vertical lines will be added.

        Returns
        -------
        None
        """
        vlines_color_palette = plt.get_cmap('Set2')

        for index, population in enumerate(self.populations):
            vlines_color = vlines_color_palette(index % 8)
            x = population.dataframe['Time']
            units = x.max().to_compact().units

            x.pint.values = x.pint.to(units)

            for ax in axes:
                ax.vlines(x=x, ymin=0, ymax=1, transform=ax.get_xaxis_transform(), color=vlines_color, lw=2.5, linestyle='--', label=f"{population.name}")

            ax.set_xlabel(f'Time [{units}]')

    @property
    def concentrations(self) -> List[Quantity]:
        """
        Gets the concentration of each population in the Scatterer instance.

        Returns
        -------
        List[Quantity]
            A list of concentrations for each population.
        """
        return [population.concentration for population in self.populations]

    @concentrations.setter
    def concentrations(self, values: Union[List[Quantity], Quantity]) -> None:
        """
        Sets the concentration of each population in the Scatterer instance.

        Parameters
        ----------
        values : Union[List[Quantity], Quantity]
            A list of concentrations to set for each population, or a single concentration value to set for all populations.

        Raises
        ------
        ValueError
            If the length of the values list does not match the number of populations or if any concentration has an incorrect dimensionality.
        """
        if isinstance(values, list):
            if len(values) != len(self.populations):
                raise ValueError("The length of the values list must match the number of populations.")

            for value in values:
                if value.dimensionality != (particle / liter).dimensionality:
                    raise ValueError(
                        f"Invalid concentration dimensionality: {value.dimensionality}. Expected dimensionality is 'particles per liter' or similar."
                    )

            for population, value in zip(self.populations, values):
                population.concentration = value
        else:
            if values.dimensionality != (particle / liter).dimensionality:
                raise ValueError(
                    f"Invalid concentration dimensionality: {values.dimensionality}. Expected dimensionality is 'particles per liter' or similar."
                )
            for population in self.populations:
                population.concentration = values
