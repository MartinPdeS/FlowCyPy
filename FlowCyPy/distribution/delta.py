from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


@dataclass(config=config_dict)
class Delta(Base):
    r"""
    Represents a delta Dirac distribution for particle properties.

    In a delta Dirac distribution, all particle properties are the same, represented by the Dirac delta function:

    .. math::
        f(x) = \delta(x - x_0)

    where:
    - :math:`x_0` is the singular particle property.

    Parameters
    ----------
    position : Quantity
        The particle property for the delta distribution in meters.
    """

    position: Quantity

    @property
    def _units(self) -> Quantity:
        return self.position.units

    def __post_init__(self):
        self._main_units = self.position.units

    @Base.pre_generate
    def generate(self, n_samples: int) -> Quantity:
        r"""
        Generates a singular distribution of scatterer properties.

        All sipropertieszes generated will be exactly the same as `position`.

        Parameters
        ----------
        n_samples : int
            The number of particle properties to generate.

        Returns
        -------
        Quantity
            An array of identical scatterer properties in meters.
        """
        return np.ones(n_samples) * self.position.magnitude

    def _generate_default_x(self, x_min_factor: float = 0.9, x_max_factor: float = 1.1, n_samples: int = 100) -> Quantity:
        """
        Generates a default range of x-values around the `position`.

        Parameters
        ----------
        x_min_factor : float, optional
            Factor for the minimum x-value relative to the `position`. Default is 0.9 (90% of the position).
        x_max_factor : float, optional
            Factor for the maximum x-value relative to the `position`. Default is 1.1 (110% of the position).
        n_samples : int, optional
            Number of points in the generated range. Default is 100.

        Returns
        -------
        Quantity
            A range of x-values with appropriate units.
        """
        if x_min_factor >= x_max_factor:
            raise ValueError("x_min_factor must be less than x_max_factor.")

        x_min = self.position.magnitude * x_min_factor
        x_max = self.position.magnitude * x_max_factor
        return np.linspace(x_min, x_max, n_samples) * self.position.units

    def get_pdf(self, x_min_factor: float = 0.99, x_max_factor: float = 1.01, n_samples: int = 21) -> Tuple[Quantity, np.ndarray]:
        r"""
        Returns the x-values and the scaled PDF values for the singular distribution.

        Returns
        -------
        Tuple[Quantity, np.ndarray]
            The input x-values and the corresponding scaled PDF values.
        """
        x = self._generate_default_x(
            x_min_factor=x_min_factor,
            x_max_factor=x_max_factor,
            n_samples=n_samples
        )

        common_units = x.units
        pdf = np.zeros_like(x.magnitude)

        # Find the closest x-value to the delta position
        idx = (np.abs(x.magnitude - self.position.to(common_units).magnitude)).argmin()
        pdf[idx] = 1.0  # Dirac delta spike at the closest x-value
        return x, pdf

    def __repr__(self) -> str:
        return f"Delta(position={self.position:.3f~P})"
