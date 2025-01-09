from typing import List, Optional, Union
from MPSPlots.styles import mps
import pandas as pd
from FlowCyPy.units import Quantity, RIU, particle, liter
from FlowCyPy.population import Population
from FlowCyPy.utils import PropertiesReport
from FlowCyPy.distribution import Base as BaseDistribution
from typing import Optional, List
from pint_pandas import PintArray
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from enum import Enum
from FlowCyPy import units


class CouplingModel(Enum):
    MIE = 'mie'
    RAYLEIGH = 'rayleigh'
    UNIFORM = 'uniform'


class ScattererCollection(PropertiesReport):
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
        self.dataframe: pd.DataFrame = None

    def get_population_ratios(self) -> list[float]:
        total_concentration = sum([p.particle_count.value for p in self.populations])

        return [(p.particle_count.value / total_concentration).magnitude for p in self.populations]

    def get_population_dataframe(self, total_sampling: Optional[Quantity]) -> pd.DataFrame:
        """
        Generate a DataFrame by sampling particles from populations.

        Parameters
        ----------
        total_sampling : Quantity, optional
            Total number of samples to draw, distributed across populations based on their ratios.

        Returns
        -------
        pd.DataFrame
            A MultiIndex DataFrame containing the sampled data from all populations. The first
            index level indicates the population name, and the second level indexes the sampled data.
        """
        ratios = self.get_population_ratios()

        sampling_list = [int(ratio * total_sampling.magnitude) for ratio in ratios]

        population_names = [p.name for p in self.populations]

        # Create tuples for the MultiIndex
        multi_index_tuples = [
            (pop_name, idx) for pop_name, n in zip(population_names, sampling_list) for idx in range(n)
        ]

        # Create the MultiIndex
        multi_index = pd.MultiIndex.from_tuples(multi_index_tuples, names=["Population", "Index"])

        # Initialize an empty DataFrame with the MultiIndex
        scatterer_dataframe = pd.DataFrame(index=multi_index)

        self.fill_dataframe_with_sampling(scatterer_dataframe=scatterer_dataframe)

        return scatterer_dataframe

    def add_population(self, *population: Population) -> 'ScattererCollection':
        """
        Adds a population to the ScattererCollection instance with the specified attributes.

        Parameters
        ----------
        name : str
            The name of the population.
        size : BaseDistribution
            The size distribution of the population.
        refractive_index : BaseDistribution
            The refractive index distribution of the population.

        Returns
        -------
        ScattererCollection
            The ScattererCollection instance (to support chaining).

        Raises
        ------
        ValueError
            If the concentration does not have the expected dimensionality.
        """
        self.populations.extend(population)
        return population

    @property
    def concentrations(self) -> List[Quantity]:
        """
        Gets the concentration of each population in the ScattererCollection instance.

        Returns
        -------
        List[Quantity]
            A list of concentrations for each population.
        """
        return [population.concentration for population in self.populations]

    @concentrations.setter
    def concentrations(self, values: Union[List[Quantity], Quantity]) -> None:
        """
        Sets the concentration of each population in the ScattererCollection instance.

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
        """
        Dilutes the populations in the flow cytometry system by a given factor.

        Parameters
        ----------
        factor : float
            The dilution factor to apply to each population. For example, a factor
            of 0.5 reduces the population density by half.

        Returns
        -------
        None
            The method modifies the populations in place.

        Notes
        -----
            - This method iterates over all populations in the system and applies the
            `dilute` method of each population.
            - The specific implementation of how a population is diluted depends on
            the `dilute` method defined in the `population` object.

        Examples
        --------
        Dilute all populations by 50%:
        >>> system.dilute(0.5)
        """
        for population in self.populations:
            population.dilute(factor)

    def fill_dataframe_with_sampling(self, scatterer_dataframe: pd.DataFrame) -> None:
        """
        Fills a DataFrame with size and refractive index sampling data for each population.

        Parameters
        ----------
        scatterer_dataframe : pd.DataFrame
            A DataFrame indexed by population names (first level) and containing the
            following columns: `'Size'`: To be filled with particle size data. `'RefractiveIndex'`:
            To be filled with refractive index data. The DataFrame must already have the required structure.

        Returns
        -------
        None
            The method modifies the `scatterer_dataframe` in place, adding size and
            refractive index sampling data.

        After filling, the DataFrame will be populated with size and refractive index data.
        """
        for population in self.populations:
            sub_dataframe = scatterer_dataframe.xs(population.name)
            sampling = len(sub_dataframe) * units.particle

            size, ri = population.generate_sampling(sampling)

            scatterer_dataframe.loc[population.name, 'Size'] = PintArray(size, dtype=size.units)
            scatterer_dataframe.loc[population.name, 'RefractiveIndex'] = PintArray(ri, dtype=ri.units)

    def plot(self, n_points: int = 100) -> None:
        """
        Visualizes the joint and marginal distributions of size and refractive index
        for multiple populations in the scatterer collection.

        This method creates a joint plot using `sns.JointGrid`, where:
        - The joint area displays filled contours representing the PDF values of size and refractive index.
        - The marginal areas display the size and refractive index PDFs as filled plots.

        Each population is plotted with a distinct color using a transparent colormap for the joint area.

        Parameters
        ----------
        n_points : int, optional
            The number of points used to compute the size and refractive index PDFs. Default is 100.
            Increasing this value results in smoother distributions but increases computation time.

        Notes
        -----
        - The joint area uses a transparent colormap, transitioning from fully transparent
        to fully opaque for better visualization of overlapping populations.
        - Marginal plots show semi-transparent filled curves for clarity.

        Example
        -------
        >>> scatterer_collection.plot(n_points=200)

        This will generate a plot with 200 points in the PDFs for size and refractive index.
        """
        def create_transparent_colormap(base_color):
            """
            Create a colormap that transitions from transparent to a specified base color.
            """
            return LinearSegmentedColormap.from_list(
                "transparent_colormap",
                [(base_color[0], base_color[1], base_color[2], 0),  # Fully transparent
                (base_color[0], base_color[1], base_color[2], 1)],  # Fully opaque
                N=256
            )

        # Create a JointGrid for visualization
        with plt.style.context(mps):
            grid = sns.JointGrid()

        for index, population in enumerate(self.populations):
            # Get size and refractive index PDFs
            size, size_pdf = population.size.get_pdf(n_points=n_points)
            ri, ri_pdf = population.refractive_index.get_pdf(n_points=n_points)

            # Create a grid of size and ri values
            X, Y = np.meshgrid(size, ri)
            Z = np.outer(ri_pdf, size_pdf)  # Compute the PDF values on the grid

            # Create a transparent colormap for this population
            base_color = sns.color_palette()[index]
            transparent_cmap = create_transparent_colormap(base_color)

            # Plot the joint area as a filled contour plot
            grid.ax_joint.contourf(
                X, Y, Z, levels=10, cmap=transparent_cmap, extend="min"
            )

            # Plot the marginal distributions
            grid.ax_marg_x.fill_between(size.magnitude, size_pdf, color=f"C{index}", alpha=0.5)
            grid.ax_marg_y.fill_betweenx(ri.magnitude, ri_pdf, color=f"C{index}", alpha=0.5)

        # Set axis labels
        grid.ax_joint.set_xlabel(f"Size [{size.units}]")
        grid.ax_joint.set_ylabel(f"Refractive Index [{ri.units}]")

        plt.tight_layout()

        # Show the plot
        plt.show()
