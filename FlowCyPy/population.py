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

from FlowCyPy import distribution
from FlowCyPy.utils import config_dict
from FlowCyPy.sampling_method import ExplicitModel, GammaModel


class BasePopulation:
    dye_label: list = []

    def add_dye_label(self, fluorophore, labeling_model):
        self.dye_label.append((fluorophore, labeling_model))

    def calculate_number_of_events(
        self, flow_area: Area, flow_speed: Velocity, run_time: Time
    ) -> Particle:
        """
        Calculates the total number of particles based on the flow volume and the defined concentration.

        Parameters
        ----------
        flow_area : Area
            The cross-sectional area of the flow (e.g., in square meters).
        flow_speed : Velocity
            The speed of the flow (e.g., in meters per second).
        run_time : Time
            The total duration of the flow (e.g., in seconds).

        Returns
        -------
        Particle
            The total number of particles.

        Raises
        ------
        ValueError
            If no concentration is defined and the total number of particles cannot be calculated.
        """
        if isinstance(self.particle_count, Particle):
            return self.particle_count

        elif isinstance(self.particle_count, Concentration):
            flow_volume = flow_area * flow_speed * run_time
            return self.concentration * flow_volume

        raise ValueError("Invalid particle count representation.")

    def compute_particle_flux(
        self, flow_speed: Velocity, flow_area: Area, run_time: Time
    ) -> ParticleFlux:
        """
        Computes the particle flux in the flow system, accounting for flow speed,
        flow area, and either the particle concentration or a predefined number of particles.

        Parameters
        ----------
        flow_speed : Velocity
            The speed of the flow (e.g., in meters per second).
        flow_area : Area
            The cross-sectional area of the flow tube (e.g., in square meters).
        run_time : Time
            The total duration of the flow (e.g., in seconds).

        Returns
        -------
        ParticleFlux
            The particle flux in particles per second (particle/second).
        """
        if isinstance(self.particle_count, Particle):
            return self.particle_count / run_time

        elif isinstance(self.particle_count, Concentration):
            flow_volume_per_second = flow_speed * flow_area
            return self.particle_count * flow_volume_per_second

        raise ValueError("Invalid particle count representation.")

    @field_validator(
        "refractive_index", "core_refractive_index", "shell_refractive_index"
    )
    def _validate_refractive_index(cls, value):
        """
        Validate the refractive index input.

        This validator ensures that the refractive index is provided either as a Quantity with the correct
        refractive index units (RIU) or as an instance of distribution.Base. If a Quantity is provided,
        it is converted to a Delta distribution .

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The refractive index value to validate.

        Returns
        -------
        distribution.Base
            A distribution representation of the refractive index.

        Raises
        ------
        TypeError
            If the input is not a Quantity with RIU units or a valid distribution.Base instance.
        """
        if isinstance(value, distribution.Base):
            return value
        elif RefractiveIndex.check(value):
            return distribution.Delta(position=value)
        raise TypeError(
            f"refractive_index must be of type Quantity (with RIU) or distribution.Base, but got {type(value)}"
        )

    @field_validator("diameter", "core_diameter", "shell_thickness")
    def _validate_diameter(cls, value):
        """
        Validate the diameter input.

        This validator ensures that the particle diameter is provided either as a Quantity with length
        units (e.g., meters) or as an instance of distribution.Base. If provided as a Quantity, it is converted
        to a Delta distribution.

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The particle diameter value to validate.

        Returns
        -------
        distribution.Base
            A distribution representation of the particle diameter.

        Raises
        ------
        TypeError
            If the input is not a Quantity with length units or a valid distribution.Base instance.
        """
        if isinstance(value, distribution.Base):
            return value
        elif Length.check(value):
            return distribution.Delta(position=value)
        raise TypeError(
            f"Diameter must be of type Quantity or distribution.Base, but got {type(value)}"
        )

    def dilute(self, factor: float) -> None:
        """
        Dilute the particle population.

        This method reduces the particle_count by a given factor, effectively diluting the population.

        Parameters
        ----------
        factor : float
            The dilution factor by which the particle count is divided.
        """
        self.particle_count /= factor

    def add_dye_to_sampling(self, sampling_dict, diameter_sample) -> dict:
        """
        Adds dye labeling information to the sampling dictionary.
        Parameters
        ----------
        sampling_dict : dict
            The existing sampling dictionary to which dye information will be added.
        diameter_sample : Quantity
            The sampled diameters of the particles.

        Returns
        -------
        dict
            The updated sampling dictionary with dye labeling information added.
        """

        for dye, model in self.dye_label:
            count_sample = model.sample_labels_given_diameter(diameter_sample)
            sampling_dict[f"Dye:{dye.name}"] = count_sample

        return sampling_dict


@dataclass(config=config_dict)
class Sphere(BasePopulation):
    """
    Represents a population of scatterers (particles) in a flow cytometry setup.

    This class encapsulates the properties of a particle population including its name,
    refractive index, particle diameter, and particle count (density). The refractive index
    and diameter can be provided as either fixed values (Quantity) or as statistical distributions
    (instances of distribution.Base). The class automatically converts Quantity attributes to their
    base SI units during initialization.

    Parameters
    ----------
    name : str
        The identifier or label for the population.
    refractive_index : distribution.Base | RefractiveIndex
        The refractive index (or its distribution) of the particles. If provided as a Quantity,
        it must have units of refractive index (RIU). If provided as a distribution, it should be an
        instance of distribution.Base.
    diameter : distribution.Base | Length
        The particle diameter (or its distribution). If provided as a Quantity, it must have units
        of length (e.g., meters). If provided as a distribution, it should be an instance of
        distribution.Base.
    particle_count : Particle | Concentration
        The number density of particles (scatterers) per cubic meter.

    """

    name: str
    refractive_index: distribution.Base | RefractiveIndex
    diameter: distribution.Base | Length
    medium_refractive_index: distribution.Base
    particle_count: Particle | Concentration
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
        diameter_sample = self.diameter.generate(sampling)
        refractive_index_sample = self.refractive_index.generate(sampling)
        medium_refractive_index_sample = self.medium_refractive_index.generate(sampling)

        sampled_data = {
            "Diameter": diameter_sample,
            "RefractiveIndex": refractive_index_sample,
            "MediumRefractiveIndex": medium_refractive_index_sample,
        }

        sampled_data = self.add_dye_to_sampling(sampled_data, diameter_sample)

        for key, value in sampled_data.items():
            dataframe.loc[:, key] = PintArray(value, dtype=value.units)


@dataclass(config=config_dict)
class CoreShell(BasePopulation):
    """
    Represents a population of core-shell scatterers in a flow cytometry setup.

    In a core-shell particle, the inner core is defined by its diameter and the outer shell
    is defined by its thickness. The overall particle diameter is given by:

        overall_diameter = core_diameter + 2 * shell_thickness

    The refractive indices for the core and shell can be provided either as fixed values (Quantity)
    or as statistical distributions (instances of distribution.Base). The particle_count defines the
    scatterer density in particles per cubic meter.

    Parameters
    ----------
    name : str
        The identifier or label for the population.
    core_diameter : distribution.Base | Length
        The diameter of the particle core. If provided as a Quantity, it must have length units
        (e.g., meter). If provided as a distribution, it must be an instance of distribution.Base.
    shell_thickness : distribution.Base | Length
        The thickness of the particle shell. If provided as a Quantity, it must have length units.
        If provided as a distribution, it must be an instance of distribution.Base.
    refractive_index_core : distribution.Base | RefractiveIndex
        The refractive index (or its distribution) of the core. If provided as a Quantity, it must have
        refractive index units (RIU).
    refractive_index_shell : distribution.Base | RefractiveIndex
        The refractive index (or its distribution) of the shell. If provided as a Quantity, it must have
        refractive index units (RIU).
    particle_count : Particle | Concentration
        The particle density in particles per cubic meter.

    """

    name: str
    core_diameter: distribution.Base | Length
    shell_thickness: distribution.Base | Length
    core_refractive_index: distribution.Base | RefractiveIndex
    shell_refractive_index: distribution.Base | RefractiveIndex
    medium_refractive_index: distribution.Base
    particle_count: Particle | Concentration
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

        core_diameter_sample = self.core_diameter.generate(sampling)
        shell_thickness_sample = self.shell_thickness.generate(sampling)
        core_refractive_index_sample = self.core_refractive_index.generate(sampling)
        shell_refractive_index_sample = self.shell_refractive_index.generate(sampling)
        medium_refractive_index_sample = self.medium_refractive_index.generate(sampling)

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
