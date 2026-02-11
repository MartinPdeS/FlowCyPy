# -*- coding: utf-8 -*-
from pydantic import field_validator
from pydantic.dataclasses import dataclass
from pint_pandas import PintArray
from TypedUnit import (
    Area,
    Concentration,
    Dimensionless,
    Length,
    Particle,
    ParticleFlux,
    RefractiveIndex,
    Time,
    Velocity,
)

from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.binary.distributions import BaseDistribution
from FlowCyPy.binary import distributions
from FlowCyPy.utils import config_dict
from FlowCyPy.sampling_method import ExplicitModel, GammaModel


class BasePopulation:

    @field_validator(
        "refractive_index",
        "core_refractive_index",
        "shell_refractive_index",
        "medium_refractive_index",
    )
    def _validate_refractive_index(cls, value):
        """
        Validate the refractive index input.

        This validator ensures that the refractive index is provided either as a Quantity with the correct
        refractive index units (RIU) or as an instance of BaseDistribution. If a Quantity is provided,
        it is converted to a Delta distribution .

        Parameters
        ----------
        value : Union[BaseDistribution, Quantity]
            The refractive index value to validate.

        Returns
        -------
        BaseDistribution
            A distribution representation of the refractive index.

        Raises
        ------
        TypeError
            If the input is not a Quantity with RIU units or a valid BaseDistribution instance.
        """
        if isinstance(value, BaseDistribution):
            return value
        elif RefractiveIndex.check(value):
            return distributions.Delta(value=value)
        raise TypeError(
            f"refractive_index must be of type Quantity (with RIU) or BaseDistribution, but got {type(value)}"
        )

    @field_validator("diameter", "core_diameter", "shell_thickness")
    def _validate_diameter(cls, value):
        """
        Validate the diameter input.

        This validator ensures that the particle diameter is provided either as a Quantity with length
        units (e.g., meters) or as an instance of BaseDistribution. If provided as a Quantity, it is converted
        to a Delta distribution.

        Parameters
        ----------
        value : Union[BaseDistribution, Quantity]
            The particle diameter value to validate.

        Returns
        -------
        BaseDistribution
            A distribution representation of the particle diameter.

        Raises
        ------
        TypeError
            If the input is not a Quantity with length units or a valid BaseDistribution instance.
        """
        if isinstance(value, BaseDistribution):
            return value
        elif Length.check(value):
            return distributions.Delta(value=value)
        raise TypeError(
            f"Diameter must be of type Quantity or BaseDistribution, but got {type(value)}"
        )

    def dilute(self, factor: float) -> None:
        """
        Dilute the particle population.

        This method reduces the concentration by a given factor, effectively diluting the population.

        Parameters
        ----------
        factor : float
            The dilution factor by which the particle count is divided.
        """
        self.concentration /= factor


@dataclass(config=config_dict)
class Sphere(BasePopulation):
    """
    Represents a population of scatterers (particles) in a flow cytometry setup.

    This class encapsulates the properties of a particle population including its name,
    refractive index, particle diameter, and particle count (density). The refractive index
    and diameter can be provided as either fixed values (Quantity) or as statistical distributions
    (instances of BaseDistribution). The class automatically converts Quantity attributes to their
    base SI units during initialization.

    Parameters
    ----------
    name : str
        The identifier or label for the population.
    refractive_index : BaseDistribution | RefractiveIndex
        The refractive index (or its distribution) of the particles. If provided as a Quantity,
        it must have units of refractive index (RIU). If provided as a distribution, it should be an
        instance of BaseDistribution.
    diameter : BaseDistribution | Length
        The particle diameter (or its distribution). If provided as a Quantity, it must have units
        of length (e.g., meters). If provided as a distribution, it should be an instance of
        BaseDistribution.
    concentration : Particle | Concentration
        The number density of particles (scatterers) per cubic meter.

    """

    name: str
    refractive_index: BaseDistribution | RefractiveIndex
    diameter: BaseDistribution | Length
    medium_refractive_index: BaseDistribution | RefractiveIndex
    concentration: Particle | Concentration
    sampling_method: object = ExplicitModel()

    def __post_init__(self):
        self.sampling_method.population = self

    def add_property_to_frame(self, dataframe) -> tuple:
        """
        Generate a sampling of particle properties.

        This method uses the underlying distributions (or fixed quantities) for diameter and refractive index
        to generate a sample set for simulation or analysis.


        This method creates a dictionnary with the following entries:
            - 'Diameter': The generated diameters.
            - 'RefractiveIndex': The generated refractive index values.

        Parameters
        ----------
        dataframe : pd.DataFrame
            The DataFrame to which the generated properties will be added.

        Returns
        -------
        tuple
            A tuple containing the generated diameter sample and refractive index sample.
        """
        sampling = len(dataframe)
        diameter_sample = self.diameter.sample(sampling)
        ri_sample = self.refractive_index.sample(sampling)
        medium_ri_sample = self.medium_refractive_index.sample(sampling)

        sampled_data = {
            "Diameter": diameter_sample,
            "RefractiveIndex": ri_sample,
            "MediumRefractiveIndex": medium_ri_sample,
        }

        for key, value in sampled_data.items():
            dataframe.loc[:, key] = PintArray(value, dtype=value.units)

    def get_effective_concentration(self):
        """ "
        Calculate the effective concentration of particles that fall within the specified cutoffs
        for diameter and refractive index.

        Returns
        -------
        Quantity
            The effective concentration of particles.
        """
        if SimulationSettings.population_cutoff_bypass:
            return self.concentration

        p_diameter = self.diameter.proportion_within_cutoffs()
        p_RI = self.refractive_index.proportion_within_cutoffs()
        p_joint = p_diameter * p_RI

        return self.concentration * p_joint


@dataclass(config=config_dict)
class CoreShell(BasePopulation):
    """
    Represents a population of core-shell scatterers in a flow cytometry setup.

    In a core-shell particle, the inner core is defined by its diameter and the outer shell
    is defined by its thickness. The overall particle diameter is given by:

        overall_diameter = core_diameter + 2 * shell_thickness

    The refractive indices for the core and shell can be provided either as fixed values (Quantity)
    or as statistical distributions (instances of BaseDistribution). The concentration defines the
    scatterer density in particles per cubic meter.

    Parameters
    ----------
    name : str
        The identifier or label for the population.
    core_diameter : BaseDistribution | Length
        The diameter of the particle core. If provided as a Quantity, it must have length units
        (e.g., meter). If provided as a distribution, it must be an instance of BaseDistribution.
    shell_thickness : BaseDistribution | Length
        The thickness of the particle shell. If provided as a Quantity, it must have length units.
        If provided as a distribution, it must be an instance of BaseDistribution.
    refractive_index_core : BaseDistribution | RefractiveIndex
        The refractive index (or its distribution) of the core. If provided as a Quantity, it must have
        refractive index units (RIU).
    refractive_index_shell : BaseDistribution | RefractiveIndex
        The refractive index (or its distribution) of the shell. If provided as a Quantity, it must have
        refractive index units (RIU).
    concentration : Particle | Concentration
        The particle density in particles per cubic meter.

    """

    name: str
    core_diameter: BaseDistribution | Length
    shell_thickness: BaseDistribution | Length
    core_refractive_index: BaseDistribution | RefractiveIndex
    shell_refractive_index: BaseDistribution | RefractiveIndex
    medium_refractive_index: BaseDistribution
    concentration: Particle | Concentration
    sampling_method: object = ExplicitModel()

    def __post_init__(self):
        self.sampling_method.population = self

    def add_property_to_frame(self, dataframe, sampling: Dimensionless) -> tuple:
        r"""
        Generate a sampling of core-shell particle properties.

        This method generates a sample set for the core diameter, shell thickness, core refractive index,
        and shell refractive index from their underlying distributions (or fixed values).

        This method creates a dictionnary with the following entries:
            - 'CoreDiameter': The generated core diameters.
            - 'ShellThickness': The generated shell thickness values.
            - 'CoreRefractiveIndex': The generated core refractive indices.
            - 'ShellRefractiveIndex': The generated shell refractive indices.

        Parameters
        ----------
        sampling : Quantity
            The sampling parameter used by the distributions.

        Returns
        -------
        tuple
            A tuple containing the generated samples in the order:
            (core_diameter, shell_thickness, refractive_index_core, refractive_index_shell).
        """

        core_diameter_sample = self.core_diameter.sample(sampling)
        shell_thickness_sample = self.shell_thickness.sample(sampling)
        core_refractive_index_sample = self.core_refractive_index.sample(sampling)
        shell_refractive_index_sample = self.shell_refractive_index.sample(sampling)
        medium_refractive_index_sample = self.medium_refractive_index.sample(sampling)

        sampled_data = {
            "CoreDiameter": core_diameter_sample,
            "ShellThickness": shell_thickness_sample,
            "CoreRefractiveIndex": core_refractive_index_sample,
            "ShellRefractiveIndex": shell_refractive_index_sample,
            "MediumRefractiveIndex": medium_refractive_index_sample,
        }

        sampled_data = self.add_dye_to_sampling(
            sampled_data, core_diameter_sample + shell_thickness_sample * 2
        )

        for key, value in sampled_data.items():
            dataframe.loc[:, key] = PintArray(value, dtype=value.units)

    def get_effective_concentration(self):
        """ "
        Calculate the effective concentration of particles that fall within the specified cutoffs
        for core diameter, shell thickness, core refractive index, and shell refractive index.

        Returns
        -------
        Quantity
            The effective concentration of particles.
        """
        if SimulationSettings.population_cutoff_bypass:
            return self.concentration

        p_core_diameter = self.core_diameter.proportion_within_cutoffs()
        p_shell_thickness = self.shell_thickness.proportion_within_cutoffs()
        p_core_RI = self.core_refractive_index.proportion_within_cutoffs()
        p_shell_RI = self.shell_refractive_index.proportion_within_cutoffs()

        p_joint = p_core_diameter * p_shell_thickness * p_core_RI * p_shell_RI

        return self.concentration * p_joint
