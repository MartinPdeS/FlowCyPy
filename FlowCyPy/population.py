
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
class Population():
    """
    A class representing a population of scatterers in a flow cytometry setup.

    Parameters
    ----------
    name : str
        Name of the population distribution.
    refractive_index : Union[distribution.Base, Quantity]
        Refractive index or refractive index distributions.
    diameter : Union[distribution.Base, Quantity]
        Particle diameter or diameter distributions.
    particle_count : ParticleCount
        Scatterer density in particles per cubic meter, default is 1 particle/m³.

    """
    name: str
    refractive_index: Union[distribution.Base, Quantity]
    diameter: Union[distribution.Base, Quantity]
    particle_count: ParticleCount | Quantity

    def __post_init__(self):
        """
        Automatically converts all Quantity attributes to their base SI units (i.e., without any prefixes).
        This strips units like millimeter to meter, kilogram to gram, etc.
        """
        self.particle_count = ParticleCount(self.particle_count)
        # Convert all Quantity attributes to base SI units (without any prefixes)
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Quantity):
                # Convert the quantity to its base unit (strip prefix)
                setattr(self, attr_name, attr_value.to_base_units())

    @field_validator('refractive_index')
    def _validate_refractive_index(cls, value):
        """
        Validates that the refractive index is either a Quantity or a valid distribution.Base instance.

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The refractive index to validate.

        Returns
        -------
        Union[distribution.Base, Quantity]
            The validated refractive index.

        Raises
        ------
        TypeError
            If the refractive index is not of type Quantity or distribution.Base.
        """
        if isinstance(value, Quantity):
            assert value.check(RIU), "The refractive index value provided does not have refractive index units [RIU]"
            return distribution.Delta(position=value)

        if isinstance(value, distribution.Base):
            return value

        raise TypeError(f"refractive_index must be of type Quantity<RIU or refractive_index_units> or distribution.Base, but got {type(value)}")

    @field_validator('diameter')
    def _validate_diameter(cls, value):
        """
        Validates that the diameter is either a Quantity or a valid distribution.Base instance.

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The diameter to validate.

        Returns
        -------
        Union[distribution.Base, Quantity]
            The validated diameter.

        Raises
        ------
        TypeError
            If the diameter is not of type Quantity or distribution.Base.
        """
        if isinstance(value, Quantity):
            assert value.check(meter), "The diameter value provided does not have length units [meter]"
            return distribution.Delta(position=value)

        if isinstance(value, distribution.Base):
            return value

        raise TypeError(f"suze must be of type Quantity or distribution.Base, but got {type(value)}")

    def dilute(self, factor: float) -> None:
        self.particle_count /= factor

    def generate_sampling(self, sampling: Quantity) -> tuple:
        diameter = self.diameter.generate(sampling)

        ri = self.refractive_index.generate(sampling)

        return diameter, ri

    def _get_sampling(self, sampling: int) -> pd.DataFrame:
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
