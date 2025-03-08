
from typing import Union
from FlowCyPy import distribution
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy.units import Quantity, nanometer, RIU, micrometer, particle
from FlowCyPy.particle_count import ParticleCount

from PyMieSim.units import Quantity, RIU, meter


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


class BasePopulation:
    @field_validator('refractive_index', 'core_refractive_index', 'shell_refractive_index')
    def _validate_refractive_index(cls, value):
        """
        Validate the refractive index input.

        This validator ensures that the refractive index is provided either as a Quantity with the correct
        refractive index units (RIU) or as an instance of distribution.Base. If a Quantity is provided,
        it is converted to a Delta distribution.

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
        if isinstance(value, Quantity):
            assert value.check(RIU), "The refractive index must have refractive index units [RIU]."
            return distribution.Delta(position=value)
        if isinstance(value, distribution.Base):
            return value
        raise TypeError(
            f"refractive_index must be of type Quantity (with RIU) or distribution.Base, but got {type(value)}"
        )

    @field_validator('diameter', 'core_diameter', 'shell_thickness')
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
        if isinstance(value, Quantity):
            assert value.check(meter), "The diameter must have length units (meter)."
            return distribution.Delta(position=value)
        if isinstance(value, distribution.Base):
            return value
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
    refractive_index : Union[distribution.Base, Quantity]
        The refractive index (or its distribution) of the particles. If provided as a Quantity,
        it must have units of refractive index (RIU). If provided as a distribution, it should be an
        instance of distribution.Base.
    diameter : Union[distribution.Base, Quantity]
        The particle diameter (or its distribution). If provided as a Quantity, it must have units
        of length (e.g., meters). If provided as a distribution, it should be an instance of
        distribution.Base.
    particle_count : ParticleCount | Quantity
        The number density of particles (scatterers) per cubic meter. If a Quantity is provided,
        it should be convertible to a ParticleCount.

    """

    name: str
    refractive_index: Union[distribution.Base, Quantity]
    diameter: Union[distribution.Base, Quantity]
    particle_count: ParticleCount | Quantity

    def __post_init__(self):
        """
        Post-initialization processing.

        This method converts any Quantity attributes to their base SI units (i.e., removes any prefixes)
        and ensures that the particle_count is stored as a ParticleCount instance.
        """
        self.particle_count = ParticleCount(self.particle_count)
        # Convert all attributes that are Quantity instances to their base SI units.
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Quantity):
                setattr(self, attr_name, attr_value.to_base_units())

    def generate_sampling(self, sampling: int) -> tuple:
        """
        Generate a sampling of particle properties.

        This method uses the underlying distributions (or fixed quantities) for diameter and refractive index
        to generate a sample set for simulation or analysis.


        This method creates a dictionnary with the following entries:
            - 'Diameter': The generated diameters.
            - 'RefractiveIndex': The generated refractive index values.

        Parameters
        ----------
        sampling : int
            The sampling parameter (e.g., number of samples or a resolution quantity) used by the distributions.

        Returns
        -------
        tuple
            A tuple containing the generated diameter sample and refractive index sample.
        """
        return {
            'Diameter': self.diameter.generate(sampling),
            'RefractiveIndex': self.refractive_index.generate(sampling)
        }


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
    core_diameter : Union[distribution.Base, Quantity]
        The diameter of the particle core. If provided as a Quantity, it must have length units
        (e.g., meter). If provided as a distribution, it must be an instance of distribution.Base.
    shell_thickness : Union[distribution.Base, Quantity]
        The thickness of the particle shell. If provided as a Quantity, it must have length units.
        If provided as a distribution, it must be an instance of distribution.Base.
    refractive_index_core : Union[distribution.Base, Quantity]
        The refractive index (or its distribution) of the core. If provided as a Quantity, it must have
        refractive index units (RIU).
    refractive_index_shell : Union[distribution.Base, Quantity]
        The refractive index (or its distribution) of the shell. If provided as a Quantity, it must have
        refractive index units (RIU).
    particle_count : ParticleCount | Quantity
        The particle density in particles per cubic meter.

    """

    name: str
    core_diameter: Union[distribution.Base, Quantity]
    shell_thickness: Union[distribution.Base, Quantity]
    core_refractive_index: Union[distribution.Base, Quantity]
    shell_refractive_index: Union[distribution.Base, Quantity]
    particle_count: ParticleCount | Quantity

    def __post_init__(self):
        """
        Post-initialization processing.

        This method ensures that:
            - All Quantity attributes are converted to their base SI units.
            - The particle_count is stored as a ParticleCount instance.
            - The core_diameter, shell_thickness, and refractive indices are validated via their respective field validators.

        """
        self.particle_count = ParticleCount(self.particle_count)
        # Convert any Quantity attribute to its base SI units.
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Quantity):
                setattr(self, attr_name, attr_value.to_base_units())

    def overall_diameter(self, sampling: Quantity) -> Quantity:
        """
        Generate the overall particle diameter.

        This method calculates the overall particle diameter for a given sampling by generating
        the core diameter and shell thickness samples from their respective distributions. The overall
        diameter is computed as:

            overall_diameter = core_diameter + 2 * shell_thickness

        Parameters
        ----------
        sampling : Quantity
            The sampling parameter used by the distributions to generate values.

        Returns
        -------
        Quantity
            The overall diameter of the particles.
        """
        core = self.core_diameter.generate(sampling)
        shell = self.shell_thickness.generate(sampling)
        return core + 2 * shell

    def generate_sampling(self, sampling: Quantity) -> tuple:
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
        return {
            'CoreDiameter':  self.core_diameter.generate(sampling),
            'ShellThickness':  self.shell_thickness.generate(sampling),
            'CoreRefractiveIndex': self.core_refractive_index.generate(sampling),
            'ShellRefractiveIndex': self.shell_refractive_index.generate(sampling)
        }


class CallablePopulationMeta(type):
    def __getattr__(cls, attr):
        raise AttributeError(f"{cls.__name__} must be called as {cls.__name__}() to access its population instance.")


class CallablePopulation(metaclass=CallablePopulationMeta):
    def __init__(self, name, diameter_dist, ri_dist):
        self._name = name
        self._diameter_distribution = diameter_dist
        self._ri_distribution = ri_dist

    def __call__(self, particle_count: Quantity = 1 * particle):
        return Sphere(
            particle_count=particle_count,
            name=self._name,
            diameter=self._diameter_distribution,
            refractive_index=self._ri_distribution,
        )


# Define populations
_populations = (
    ('Exosome',          70 * nanometer, 2.0, 1.39 * RIU, 0.02 * RIU),
    ('MicroVesicle',    400 * nanometer, 1.5, 1.39 * RIU, 0.02 * RIU),
    ('ApoptoticBodies',  2 * micrometer, 1.2, 1.40 * RIU, 0.03 * RIU),
    ('HDL',              10 * nanometer, 3.5, 1.33 * RIU, 0.01 * RIU),
    ('LDL',              20 * nanometer, 3.0, 1.35 * RIU, 0.02 * RIU),
    ('VLDL',             50 * nanometer, 2.0, 1.445 * RIU, 0.0005 * RIU),
    ('Platelet',       2000 * nanometer, 2.5, 1.38 * RIU, 0.01 * RIU),
    ('CellularDebris',   3 * micrometer, 1.0, 1.40 * RIU, 0.03 * RIU),
)

# Dynamically create population classes
for (name, diameter, diameter_spread, ri, ri_spread) in _populations:
    diameter_distribution = distribution.RosinRammler(
        characteristic_property=diameter,
        spread=diameter_spread
    )

    ri_distribution = distribution.Normal(
        mean=ri,
        std_dev=ri_spread
    )

    # Create a class dynamically for each population
    cls = type(name, (CallablePopulation,), {})
    globals()[name] = cls(name, diameter_distribution, ri_distribution)


# Helper function for microbeads
def get_microbeads(diameter: Quantity, refractive_index: Quantity, name: str) -> Sphere:
    diameter_distribution = distribution.Delta(position=diameter)
    ri_distribution = distribution.Delta(position=refractive_index)

    microbeads = Sphere(
        name=name,
        diameter=diameter_distribution,
        refractive_index=ri_distribution
    )

    return microbeads
