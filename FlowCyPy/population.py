
from typing import Union
from FlowCyPy import distribution
import pandas as pd
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from pint_pandas import PintArray
from FlowCyPy.units import Quantity, nanometer, RIU, micrometer, particle
from FlowCyPy.particle_count import ParticleCount

from PyMieSim.units import Quantity, RIU, meter


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Population:
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

    Attributes
    ----------
    name : str
        The name of the population.
    refractive_index : distribution.Base
        The validated refractive index, stored as a distribution (via Delta if originally a Quantity).
    diameter : distribution.Base
        The validated diameter, stored as a distribution (via Delta if originally a Quantity).
    particle_count : ParticleCount
        The scatterer density in particles per cubic meter, stored as a ParticleCount.
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

    @field_validator('refractive_index')
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

    @field_validator('diameter')
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

    def generate_sampling(self, sampling: int) -> tuple:
        """
        Generate a sampling of particle properties.

        This method uses the underlying distributions (or fixed quantities) for diameter and refractive index
        to generate a sample set for simulation or analysis.

        Parameters
        ----------
        sampling : int
            The sampling parameter (e.g., number of samples or a resolution quantity) used by the distributions.

        Returns
        -------
        tuple
            A tuple containing the generated diameter sample and refractive index sample.
        """
        diameter = self.diameter.generate(sampling)
        ri = self.refractive_index.generate(sampling)
        return diameter, ri

    def _get_sampling(self, sampling: int) -> pd.DataFrame:
        """
        Generate a DataFrame with particle sampling data.

        This internal method generates a pandas DataFrame containing samples for particle diameter ("Size")
        and refractive index ("RefractiveIndex") based on a specified number of samples.

        Parameters
        ----------
        sampling : int
            The number of samples to generate.

        Returns
        -------
        pd.DataFrame
            A DataFrame with two columns: 'Size' and 'RefractiveIndex', containing the sampled values.
        """
        diameter = self.diameter.generate(sampling)
        ri = self.refractive_index.generate(sampling)
        dataframe = pd.DataFrame(columns=['Size', 'RefractiveIndex'])
        dataframe['Size'] = PintArray(diameter, dtype=diameter.units)
        dataframe['RefractiveIndex'] = PintArray(ri, dtype=ri.units)
        return dataframe



class CallablePopulationMeta(type):
    def __getattr__(cls, attr):
        raise AttributeError(f"{cls.__name__} must be called as {cls.__name__}() to access its population instance.")


class CallablePopulation(metaclass=CallablePopulationMeta):
    def __init__(self, name, diameter_dist, ri_dist):
        self._name = name
        self._diameter_distribution = diameter_dist
        self._ri_distribution = ri_dist

    def __call__(self, particle_count: Quantity = 1 * particle):
        return Population(
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
def get_microbeads(diameter: Quantity, refractive_index: Quantity, name: str) -> Population:
    diameter_distribution = distribution.Delta(position=diameter)
    ri_distribution = distribution.Delta(position=refractive_index)

    microbeads = Population(
        name=name,
        diameter=diameter_distribution,
        refractive_index=ri_distribution
    )

    return microbeads
