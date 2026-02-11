# -*- coding: utf-8 -*-
from typing import List, Union

import pandas as pd
from TypedUnit import Concentration

from FlowCyPy.population import BasePopulation


class ScattererCollection:
    """
    Defines and manages the diameter and refractive index distributions of scatterers (particles)
    passing through a flow cytometer. This class generates random scatterer diameters and refractive
    indices based on a list of provided distributions (e.g., Normal, LogNormal, Uniform, etc.).

    """

    def __init__(self, populations: List[BasePopulation] = None):
        """
        Parameters
        ----------
        populations : List[BasePopulation]
            A list of Population instances that define different scatterer populations.
        """
        self.populations = populations or []
        self.dataframe: pd.DataFrame = None

    def get_population_ratios(self) -> list[float]:
        """
        Get the ratios of each population's concentration to the total concentration.

        Returns
        -------
        list[float]
            A list of concentration ratios for each population.
        """
        total_concentration = sum([p.particle_count for p in self.populations])

        return [
            (p.particle_count / total_concentration).magnitude for p in self.populations
        ]

    def add_population(self, *population: BasePopulation) -> "ScattererCollection":
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
    def concentrations(self) -> List[Concentration]:
        """
        Gets the concentration of each population in the ScattererCollection instance.

        Returns
        -------
        List[Concentration]
            A list of concentrations for each population.
        """
        return [population.concentration for population in self.populations]

    def set_concentrations(
        self, values: Union[List[Concentration], Concentration]
    ) -> None:
        """
        Sets the concentration of each population in the ScattererCollection instance.

        Parameters
        ----------
        values : Union[List[Concentration], Concentration]
            A list of concentrations to set for each population, or a single concentration value to set for all populations.

        Raises
        ------
        ValueError
            If the length of the values list does not match the number of populations or if any concentration has an incorrect dimensionality.
        """
        if isinstance(values, (list, tuple)):
            if len(values) != len(self.populations):
                raise ValueError(
                    "The length of the values list must match the number of populations."
                )

            for value in values:
                Concentration.check(value)

            for population, value in zip(self.populations, values):
                population.concentration = value
        else:
            Concentration.check(values)

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
