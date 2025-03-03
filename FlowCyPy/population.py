
from typing import Union
from FlowCyPy import distribution
import pandas as pd
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from pint_pandas import PintArray
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import gridspec

from PyMieSim.units import Quantity, RIU, meter
from FlowCyPy.particle_count import ParticleCount


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

from FlowCyPy.populations_instances import *  # noqa F403
