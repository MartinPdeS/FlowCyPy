from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


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

    @property
    def _units(self) -> Quantity:
        return self.characteristic_size.units

    @Base.pre_generate
    def generate(self, n_samples: int) -> Quantity:
        """
        Generates a particle size distribution based on the Rosin-Rammler model.

        Parameters
        ----------
        n_samples : Quantity
            The number of particle sizes to generate (dimensionless).

        Returns
        -------
        Quantity
            An array of particle sizes in meters (or other units).
        """
        # Convert characteristic size to main units
        d = self.characteristic_size.magnitude

        # Generate uniform random samples in [0, 1)
        u = np.random.uniform(size=n_samples)
        u = np.clip(u, 1e-10, 1 - 1e-10)  # Avoid numerical issues

        # Apply inverse CDF of Rosin-Rammler distribution
        return d * (-np.log(1 - u))**(1 / self.spread)

    def _generate_default_x(self, x_min: float, x_max: float, n_samples: int = 100) -> np.ndarray:
        """
        Generates a default range for x-values based on the characteristic size
        and spread of the Rosin-Rammler distribution.

        Parameters
        ----------
        x_min : float
            Factor for the minimum x-value as a fraction of the characteristic size.
        x_max : float
            Factor for the maximum x-value as a multiple of the characteristic size.
        n_samples : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        np.ndarray
            A default range of x-values with appropriate units.
        """
        if x_min <= 0:
            raise ValueError("x_min must be greater than 0.")
        if x_max <= x_min:
            raise ValueError("x_max must be greater than x_min.")

        d = self.characteristic_size.magnitude  # Characteristic size in base units
        x_min = d * x_min  # Scale x_min by characteristic size
        x_max = d * x_max  # Scale x_max by characteristic size
        return np.linspace(x_min, x_max, n_samples) * self._units

    def get_pdf(self, x_min: float = 0.01, x_max: float = 4, n_samples: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        r"""
        Returns the x-values and the scaled PDF values for the particle size distribution.

        The PDF for the Rosin-Rammler distribution is derived from the CDF:

        .. math::
            f(x) = \frac{k}{d} \left( \frac{x}{d} \right)^{k-1} \exp \left( - \left( \frac{x}{d} \right)^k \right)

        Parameters
        ----------
        x_min : float, optional
            Factor for the minimum x-value as a fraction of the characteristic size. Default is 0.01.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the characteristic size. Default is 5.
        n_samples : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding scaled PDF values.
        """
        # Generate x-values based on user-defined or default parameters
        x = self._generate_default_x(x_min=x_min, x_max=x_max, n_samples=n_samples)

        x = x.to(self._units)
        _x = x.magnitude
        d = self.characteristic_size.to(self._units).magnitude
        k = self.spread
        # k = 2.5
        # Rosin-Rammler PDF formula
        pdf = (k / d) * (_x / d)**(k - 1) * np.exp(-(_x / d)**k)

        return x, pdf

    def __repr__(self) -> str:
        return f"RR({self.characteristic_size:.3f~P}, {self.spread:.3f})"
