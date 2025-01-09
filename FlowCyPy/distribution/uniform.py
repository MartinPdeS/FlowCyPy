from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from scipy.stats import uniform
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass

@dataclass(config=config_dict)
class Uniform(Base):
    r"""
    Represents a uniform distribution for particle sizes.

    The uniform distribution assigns equal probability to all particle sizes within a specified range:

    .. math::
        f(x) = \frac{1}{b - a} \quad \text{for} \quad a \leq x \leq b

    where:
    - :math:`a` is the lower bound of the distribution.
    - :math:`b` is the upper bound of the distribution.

    Parameters
    ----------
    lower_bound : Quantity
        The lower bound for particle sizes in meters.
    upper_bound : Quantity
        The upper bound for particle sizes in meters.
    """

    lower_bound: Quantity
    upper_bound: Quantity
    _name = 'Uniform'

    def __post_init__(self):
        self.lower_bound = self.lower_bound.to(self.upper_bound.units)

    def _generate_default_x(self, n_points: int = 100) -> Quantity:
        """
        Generates a default range of x-values for the uniform distribution.

        Parameters
        ----------
        n_points : int, optional
            Number of points in the generated range. Default is 100.

        Returns
        -------
        Quantity
            A range of x-values with appropriate units.
        """
        if n_points < 2:
            raise ValueError("n_points must be at least 2.")

        x_min = self.lower_bound.magnitude / 1.1
        x_max = self.upper_bound.magnitude * 1.1

        return np.linspace(x_min, x_max, n_points) * self.lower_bound.units

    def generate(self, n_samples: Quantity) -> Quantity:
        """
        Generates a uniform distribution of scatterer sizes.

        The generated sizes are uniformly distributed between the specified `lower_bound` and `upper_bound`.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        Quantity
            An array of scatterer sizes in meters.
        """
        return np.random.uniform(
            self.lower_bound.magnitude,
            self.upper_bound.magnitude,
            n_samples.magnitude
        ) * self.lower_bound.units

    def get_pdf(self, x: Quantity = None, n_points: int = 100) -> Tuple[Quantity, np.ndarray]:
        """
        Returns the x-values and the PDF values for the uniform distribution.

        If `x` is not provided, a default range of x-values is generated.

        Parameters
        ----------
        x : Quantity, optional
            The input x-values (particle sizes) over which to compute the PDF. If not provided,
            a range is automatically generated.
        n_points : int, optional
            Number of points in the generated range if `x` is not provided. Default is 100.

        Returns
        -------
        Tuple[Quantity, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        if x is None:
            x = self._generate_default_x(n_points=n_points)

        common_unit = self.lower_bound.units

        pdf = uniform.pdf(
            x.to(common_unit).magnitude,
            loc=self.lower_bound.magnitude,
            scale=self.upper_bound.to(common_unit).magnitude - self.lower_bound.magnitude
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Uniform(lower_bound={self.lower_bound:.3f~P}, upper_bound={self.upper_bound:.3f~P})"
