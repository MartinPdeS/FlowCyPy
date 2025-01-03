
from typing import Union
from FlowCyPy import distribution
from dataclasses import field
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy.units import particle
from FlowCyPy.utils import PropertiesReport
from PyMieSim.units import Quantity, RIU, meter
from FlowCyPy.particle_count import ParticleCount


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Population(PropertiesReport):
    """
    A class representing a population of scatterers in a flow cytometry setup.

    Parameters
    ----------
    name : str
        Name of the population distribution.
    refractive_index : Union[distribution.Base, Quantity]
        Refractive index or refractive index distributions.
    size : Union[distribution.Base, Quantity]
        Particle size or size distributions.
    particle_count : ParticleCount
        Scatterer density in particles per cubic meter, default is 1 particle/m³.

    """
    name: str
    refractive_index: Union[distribution.Base, Quantity]
    size: Union[distribution.Base, Quantity]
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

    @field_validator('concentration')
    def _validate_concentration(cls, value):
        """
        Validates that the concentration is expressed in units of inverse volume.

        Parameters
        ----------
        value : Quantity
            The concentration to validate.

        Returns
        -------
        Quantity
            The validated concentration.

        Raises
        ------
            ValueError: If the concentration is not expressed in units of inverse volume.
        """
        if not value.check('particles / [length]**3'):
            raise ValueError(f"concentration must be in units of particles per volume (e.g., particles/m^3), but got {value.units}")
        return value

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

    @field_validator('size')
    def _validate_size(cls, value):
        """
        Validates that the size is either a Quantity or a valid distribution.Base instance.

        Parameters
        ----------
        value : Union[distribution.Base, Quantity]
            The size to validate.

        Returns
        -------
        Union[distribution.Base, Quantity]
            The validated size.

        Raises
        ------
        TypeError
            If the size is not of type Quantity or distribution.Base.
        """
        if isinstance(value, Quantity):
            assert value.check(meter), "The size value provided does not have length units [meter]"
            return distribution.Delta(position=value)

        if isinstance(value, distribution.Base):
            return value

        raise TypeError(f"suze must be of type Quantity or distribution.Base, but got {type(value)}")
    
    def dilute(self, factor: float) -> None:
        self.particle_count /= factor

from FlowCyPy.populations_instances import *  # noqa F403
