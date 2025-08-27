from typing import Tuple

import numpy as np
from pydantic.dataclasses import dataclass
from scipy.stats import uniform
from TypedUnit import Length, RefractiveIndex

from FlowCyPy.distribution.base_class import Base
from FlowCyPy.utils import config_dict


@dataclass(config=config_dict)
class Uniform(Base):
    r"""
    Represents a uniform distribution for particle properties.

    The uniform distribution assigns equal probability to all particle properties within a specified range:

    .. math::
        f(x) = \frac{1}{b - a} \quad \text{for} \quad a \leq x \leq b

    where:
    - :math:`a` is the lower bound of the distribution.
    - :math:`b` is the upper bound of the distribution.

    Parameters
    ----------
    lower_bound : Length | RefractiveIndex
        The lower bound for particle properties in meters.
    upper_bound : Length | RefractiveIndex
        The upper bound for particle properties in meters.
    """

    lower_bound: Length | RefractiveIndex
    upper_bound: Length | RefractiveIndex

    @property
    def _units(self) -> Length | RefractiveIndex:
        return self.lower_bound.units

    @property
    def _lower_bound(self) -> Length | RefractiveIndex:
        return self.lower_bound.to(self._units)

    @property
    def _upper_bound(self) -> Length | RefractiveIndex:
        return self.upper_bound.to(self._units)

    def __post_init__(self):
        self.lower_bound = self.lower_bound.to(self.upper_bound.units)

    def _generate_default_x(self, n_samples: int = 100) -> Length | RefractiveIndex:
        """
        Generates a default range of x-values for the uniform distribution.

        Parameters
        ----------
        n_points : int, optional
            Number of points in the generated range. Default is 100.

        Returns
        -------
        Length | RefractiveIndex
            A range of x-values with appropriate units.
        """
        x_min = self._lower_bound.magnitude / 1.1
        x_max = self._upper_bound.magnitude * 1.1

        return np.linspace(x_min, x_max, n_samples) * self._units

    @Base.pre_generate
    def generate(self, n_samples: int) -> Length | RefractiveIndex:
        """
        Generates a uniform distribution of scatterer properties.

        The generated properties are uniformly distributed between the specified `lower_bound` and `upper_bound`.

        Parameters
        ----------
        n_samples : int
            The number of particle properties to generate.

        Returns
        -------
        Length | RefractiveIndex
            An array of scatterer properties in meters.
        """
        return np.random.uniform(
            self._lower_bound.magnitude, self._upper_bound.magnitude, n_samples
        )

    def get_pdf(
        self, n_samples: int = 100
    ) -> Tuple[Length | RefractiveIndex, np.ndarray]:
        """
        Returns the x-values and the PDF values for the uniform distribution.

        If `x` is not provided, a default range of x-values is generated.

        Parameters
        ----------
        n_samples : int, optional
            Number of points in the generated range if `x` is not provided. Default is 100.

        Returns
        -------
        Tuple[Length | RefractiveIndex, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        x = self._generate_default_x(n_samples=n_samples)

        pdf = uniform.pdf(
            x.magnitude,
            loc=self._lower_bound.magnitude,
            scale=self._upper_bound.magnitude - self._lower_bound.magnitude,
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Uniform(lower_bound={self.lower_bound:.3f~P}, upper_bound={self.upper_bound:.3f~P})"
