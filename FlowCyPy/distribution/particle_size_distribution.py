from FlowCyPy.distribution.base_class import Base
import numpy as np
from typing import Tuple
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)

@dataclass(config=config_dict)
class RosinRammler(Base):
    r"""
    Represents a Particle Size Distribution using the Rosin-Rammler model.

    The Rosin-Rammler distribution is described by its characteristic size and
    spread parameter, and is used to model particle sizes in systems such as
    powders or granular materials.

    The distribution function is given by:

    .. math::
        F(x) = 1 - \exp \left( - \left( \frac{x}{d} \right)^k \right)

    where:
        - :math:`x` is the particle size.
        - :math:`d` is the characteristic particle size.
        - :math:`k` is the spread parameter.

    Parameters
    ----------
    characteristic_size : Quantity
        The characteristic particle size in meters.
    spread : float
        The spread parameter (shape factor).
    """

    characteristic_size: Quantity
    spread: float
    _name = 'Rosin-Rammler'

    def __post_init__(self):
        self._main_units = self.characteristic_size.units

    def generate(self, n_samples: Quantity) -> Quantity:
        """
        Generates a particle size distribution based on the Rosin-Rammler model.

        Parameters
        ----------
        n_samples : Quantity
            The number of particle sizes to generate.

        Returns
        -------
        Quantity
            An array of particle sizes in meters (or other units).
        """
        d = self.characteristic_size.to(self._main_units).magnitude
        k = self.spread

        # Inverse of the Rosin-Rammler CDF to generate random samples
        u = np.random.uniform(size=n_samples.magnitude)
        sizes = d * (-np.log(1 - u))**(1/k)

        return sizes * self._main_units

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        r"""
        Returns the x-values and the scaled PDF values for the particle size distribution.

        The PDF for the Rosin-Rammler distribution is derived from the CDF:

        .. math::
            f(x) = \frac{k}{d} \left( \frac{x}{d} \right)^{k-1} \exp \left( - \left( \frac{x}{d} \right)^k \right)

        Parameters
        ----------
        x : np.ndarray
            The input x-values (particle sizes) over which to compute the PDF.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding scaled PDF values.
        """
        common_units = x.units
        d = self.characteristic_size.to(common_units).magnitude
        k = self.spread

        # Rosin-Rammler PDF formula
        pdf = (k / d) * (x.magnitude / d)**(k - 1) * np.exp(-(x.magnitude / d)**k)

        return x, pdf

    def __repr__(self) -> str:
        return f"RR({self.characteristic_size:.3f~P}, {self.spread:.3f})"
