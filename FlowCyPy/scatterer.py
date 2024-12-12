from typing import List, Optional, Union
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
import seaborn as sns
import pandas as pd
import numpy
from FlowCyPy.units import Quantity, RIU, particle, liter
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.population import Population
from FlowCyPy.utils import PropertiesReport
from FlowCyPy.distribution import Base as BaseDistribution
from FlowCyPy.logger import ScattererLogger
from FlowCyPy.particle_count import ParticleCount
from enum import Enum
from pint_pandas import PintType, PintArray


class CouplingModel(Enum):
    MIE = 'mie'
    RAYLEIGH = 'rayleigh'
    UNIFORM = 'uniform'


class Scatterer(PropertiesReport):
    """
    Defines and manages the size and refractive index distributions of scatterers (particles)
    passing through a flow cytometer. This class generates random scatterer sizes and refractive
    indices based on a list of provided distributions (e.g., Normal, LogNormal, Uniform, etc.).

    """
    def __init__(self, medium_refractive_index: Quantity = 1.0 * RIU, populations: List[Population] = None, coupling_model: Optional[CouplingModel] = CouplingModel.MIE):
        """
        Parameters
        ----------
        populations : List[Population]
            A list of Population instances that define different scatterer populations.
        coupling_model : Optional[CouplingModel], optional
            The type of coupling factor to use (CouplingModel.MIE, CouplingModel.RAYLEIGH, CouplingModel.UNIFORM). Default is CouplingModel.MIE.
        medium_refractive_index : float
            The refractive index of the medium. Default is 1.0.
        """
        self.populations = populations or []
        self.medium_refractive_index = medium_refractive_index
        self.coupling_model = coupling_model

        self.flow_cell: FlowCell = None
        self.n_events: int = None
        self.dataframe: pd.DataFrame = None

    def initialize(self, flow_cell: FlowCell, size_units: str = 'micrometer') -> None:
        """
        Initializes particle size, refractive index, and medium refractive index distributions.

        Parameters
        ----------
        flow_cell : FlowCell
            An instance of the FlowCell class that describes the flow cell being used.

        """
        self.flow_cell = flow_cell

        for population in self.populations:
            population.initialize(flow_cell=self.flow_cell)
            population.dataframe.Size = population.dataframe.Size.pint.to(size_units)

        if len(self.populations) != 0:
            self.dataframe = pd.concat(
                [population.dataframe for population in self.populations],
                axis=0,
                keys=[population.name for population in self.populations],
            )
            self.dataframe.index.names = ['Population', 'Index']

        else:
            dtypes = {
                'Time': PintType('second'),            # Time column with seconds unit
                'Position': PintType('meter'),         # Position column with meters unit
                'Size': PintType('meter'),        # Size column with micrometers unit
                'RefractiveIndex': PintType('meter')  # Dimensionless unit for refractive index
            }

            multi_index = pd.MultiIndex.from_tuples([], names=["Population", "Index"])

            # Create an empty DataFrame with specified column types and a multi-index
            self.dataframe = pd.DataFrame(
                {col: pd.Series(dtype=dtype) for col, dtype in dtypes.items()},
                index=multi_index
            )

        self.n_events = len(self.dataframe)

    def distribute_time_linearly(self, sequential_population: bool = False) -> None:
        """
        Distributes particle arrival times linearly across the total runtime of the flow cell.

        Optionally randomizes the order of times for all populations to simulate non-sequential particle arrivals.

        Parameters
        ----------
        sequential_population : bool, optional
            If `True`, organize the order of arrival times across all populations (default is `False`).

        """
        # Generate linearly spaced time values across the flow cell runtime
        linear_spacing = numpy.linspace(0, self.flow_cell.run_time, self.n_events)

        # Optionally randomize the linear spacing
        if not sequential_population:
            numpy.random.shuffle(linear_spacing)

        # Assign the linearly spaced or randomized times to the scatterer DataFrame
        self.dataframe.Time = PintArray(linear_spacing, dtype=self.dataframe.Time.pint.units)

    def plot(self, ax: Optional[plt.Axes] = None, show: bool = True, alpha: float = 0.8, bandwidth_adjust: float = 1, log_plot: bool = False, color_palette: Optional[Union[str, dict]] = None) -> None:
        """
        Visualizes the joint distribution of scatterer sizes and refractive indices using a Seaborn jointplot.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Existing matplotlib axes to plot on. If `None`, a new figure and axes are created. Default is `None`.
        show : bool, optional
            If `True`, displays the plot after creation. Default is `True`.
        alpha : float, optional
            Transparency level for the scatter plot points, ranging from 0 (fully transparent) to 1 (fully opaque). Default is 0.8.
        bandwidth_adjust : float, optional
            Bandwidth adjustment factor for the kernel density estimate of the marginal distributions. Higher values produce smoother density estimates. Default is 1.
        log_plot : bool, optional
            If `True`, applies a logarithmic scale to both axes of the joint plot and their marginal distributions. Default is `False`.
        color_palette : str or dict, optional
            The color palette to use for the hue in the scatterplot. Can be a seaborn palette name
            (e.g., 'viridis', 'coolwarm') or a dictionary mapping hue levels to specific colors. Default is None.

        Returns
        -------
        None
            This function does not return any value. It either displays the plot (if `show=True`) or simply creates it for later use.

        Notes
        -----
        This method resets the index of the internal dataframe and extracts units from the 'Size' column.
        The plot uses the specified matplotlib style (`mps`) for consistent styling.

        """
        df_reset = self.dataframe.reset_index()

        if len(df_reset.Time) == 1:
            return

        x_unit = df_reset['Size'].pint.units

        with plt.style.context(mps):
            g = sns.jointplot(data=df_reset, x='Size', y='RefractiveIndex',
                hue='Population', palette=color_palette, kind='scatter',
                alpha=alpha, marginal_kws=dict(bw_adjust=bandwidth_adjust)
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
            population._log_properties()

    def _log_properties(self) -> None:
        """
        Logs key properties of the Scatterer instance in a formatted table, including its name,
        refractive index, size, concentration, and number of events.

        The results are displayed in a formatted table using `tabulate` for clarity.
        """
        # Gather properties
        logger = ScattererLogger(self)

        logger.log_properties(table_format="fancy_grid")

    def add_population(self, population: Population, particle_count: ParticleCount) -> 'Scatterer':
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
        particle_count : ParticleCount
            The concentration or number of particle of the population. Must have the dimensionality of 'particles per liter'.

        Returns
        -------
        Scatterer
            The Scatterer instance (to support chaining).

        Raises
        ------
        ValueError
            If the concentration does not have the expected dimensionality.
        """
        population.particle_count = ParticleCount(particle_count)

        self.populations.append(population)
        return population

    def _add_population(self, name: str, size: BaseDistribution, refractive_index: BaseDistribution, concentration: Quantity) -> 'Scatterer':
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
        return population

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

        for index, (population_name, group) in enumerate(self.dataframe.groupby(level=0)):
            vlines_color = vlines_color_palette(index % 8)
            x = group['Time']
            units = x.max().to_compact().units
            x.pint.values = x.pint.to(units)
            for ax in axes:
                ax.vlines(x=x, ymin=0, ymax=1, transform=ax.get_xaxis_transform(), color=vlines_color, lw=2.5, linestyle='--', label=population_name)

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
        if isinstance(values, (list, tuple)):
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

    def dilute(self, factor: float) -> None:
        for population in self.populations:
            population.concentration /= factor
