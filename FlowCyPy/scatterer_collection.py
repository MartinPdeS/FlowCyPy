from typing import List, Optional, Union
from MPSPlots.styles import mps
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List
from pint_pandas import PintArray
from enum import Enum

from FlowCyPy import units
from FlowCyPy.units import Quantity, RIU, particle, liter
from FlowCyPy.population import Population


class CouplingModel(Enum):
    MIE = 'mie'
    RAYLEIGH = 'rayleigh'
    UNIFORM = 'uniform'


class ScattererCollection():
    """
    Defines and manages the diameter and refractive index distributions of scatterers (particles)
    passing through a flow cytometer. This class generates random scatterer diameters and refractive
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

    def get_population_dataframe(self, total_sampling: Optional[Quantity], use_ratio: bool = True) -> pd.DataFrame:
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
        if use_ratio:
            ratios = self.get_population_ratios()
        else:
            ratios = [1] * len(self.populations)

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
        diameter : BaseDistribution
            The diameter distribution of the population.
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

    def set_concentrations(self, values: Union[List[Quantity], Quantity]) -> None:
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

            - This method iterates over all populations in the system and applies the `dilute` method of each population.
            - The specific implementation of how a population is diluted depends on the `dilute` method defined in the `population` object.

        Examples
        --------
        Dilute all populations by 50%:
        >>> system.dilute(0.5)
        """
        for population in self.populations:
            population.dilute(factor)

    def fill_dataframe_with_sampling(self, scatterer_dataframe: pd.DataFrame) -> None:
        """
        Fills a DataFrame with diameter and refractive index sampling data for each population.

        Parameters
        ----------
        scatterer_dataframe : pd.DataFrame
            A DataFrame indexed by population names (first level) and containing the
            following columns: `'Diameter'`: To be filled with particle diameter data. `'RefractiveIndex'`:
            To be filled with refractive index data. The DataFrame must already have the required structure.

        Returns
        -------
        None
            The method modifies the `scatterer_dataframe` in place, adding diameter and
            refractive index sampling data.

        After filling, the DataFrame will be populated with diameter and refractive index data.
        """
        for population in self.populations:
            # Check if population.name is in the dataframe's index
            if population.name not in scatterer_dataframe.index:
                continue  # Skip this iteration if population.name is not present

            # Safely access the sub-dataframe and proceed
            sub_dataframe = scatterer_dataframe.xs(population.name)
            sampling = len(sub_dataframe) * units.particle

            diameter, ri = population.generate_sampling(sampling)

            scatterer_dataframe.loc[population.name, 'Diameter'] = PintArray(diameter, dtype=diameter.units)
            scatterer_dataframe.loc[population.name, 'RefractiveIndex'] = PintArray(ri, dtype=ri.units)

    def plot(self, sampling: int = 1000, show: bool = True, use_ratio: bool = False):
        """
        Visualizes the joint and marginal distributions of diameter and refractive index
        for all populations in the scatterer collection using sampled data and seaborn's jointplot.

        This method generates a DataFrame with samples drawn from each population (distributed
        according to their relative particle counts), then creates a KDE joint plot with marginal
        distributions. Each population is distinguished by color.

        Parameters
        ----------
        sampling : int, optional
            Total number of samples to draw across all populations. The samples are distributed
            among populations based on their concentration ratios. Default is 1000.
        show : bool, optional
            If True, displays the plot immediately.

        Returns
        -------
        g : seaborn.axisgrid.JointGrid
            The JointGrid object containing the plot.
        """
        # Convert the total sample count into a Quantity.
        total_sampling = sampling * particle  # Assumes 'particle' is a valid unit from PyMieSim.units

        # Generate the DataFrame with sampling.
        df = self.get_population_dataframe(total_sampling, use_ratio=use_ratio)

        print(df)

        # Reset the MultiIndex to obtain a column for population names.
        df_reset = df.reset_index()

        # Create the joint plot using seaborn's jointplot.
        # Note: As of seaborn 0.11+, jointplot supports the hue parameter.
        with plt.style.context(mps):
            g = sns.jointplot(
                data=df_reset,
                y='Diameter',
                x='RefractiveIndex',
                hue='Population',
                kind='kde',
                fill=True,
                common_norm=False,
                height=8,
            )

        # Set axis labels (using the units from the first population; assumes consistency across populations).
        g.set_axis_labels(
            f"Diameter [{self.populations[0].diameter._units}]",
            f"Refractive Index [{self.populations[0].refractive_index._units}]"
        )

        # Set a title for the plot.
        plt.suptitle("Scatterer Collection", fontsize=16, y=1.02)
        plt.tight_layout()

        if show:
            plt.show()

        return g