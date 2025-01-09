from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from scipy.stats import norm
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


@dataclass(config=config_dict)
class Normal(Base):
    r"""
    Represents a normal (Gaussian) distribution for particle sizes.

    The normal distribution is described by its mean and standard deviation:

    .. math::
        f(x) = \frac{1}{\sqrt{2 \pi \sigma^2}} \exp \left( - \frac{(x - \mu)^2}{2 \sigma^2} \right)

    where:
    - :math:`\mu` is the mean of the distribution (average particle size).
    - :math:`\sigma` is the standard deviation (width of the distribution).
    - :math:`x` represents particle sizes.

    Parameters
    ----------
    mean : Quantity
        The mean (average) particle size in meters.
    std_dev : Quantity
        The standard deviation of particle sizes in meters.
    """

    mean: Quantity
    std_dev: Quantity
    _name = 'Normal'

    def __post_init__(self):
        self.std_dev = self.std_dev.to(self.mean.units)

    def generate(self, n_samples: int) -> np.ndarray:
        """
        Generates a normal distribution of scatterer sizes.

        The generated sizes are based on the normal distribution's mean and standard deviation.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of scatterer sizes in meters.
        """
        return np.random.normal(
            loc=self.mean.magnitude,
            scale=self.std_dev.magnitude,
            size=int(n_samples.magnitude)
        ) * self.mean.units

    def _generate_default_x(self, x_min: float = -3, x_max: float = 3, n_points: int = 20) -> np.ndarray:
        """
        Generates a range of x-values based on the mean and standard deviation.

        Parameters
        ----------
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the standard deviation from the mean. Default is -3.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the standard deviation from the mean. Default is 3.
        n_points : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        np.ndarray
            A range of x-values with appropriate units.
        """
        if x_min >= x_max:
            raise ValueError("x_min must be less than x_max.")
        if n_points < 2:
            raise ValueError("n_points must be at least 2.")

        mu = self.mean.magnitude
        sigma = self.std_dev.magnitude
        x_min_value = mu + x_min * sigma
        x_max_value = mu + x_max * sigma
        return np.linspace(x_min_value, x_max_value, n_points) * self.mean.units

    def get_pdf(self, x: np.ndarray = None, x_min: float = -3, x_max: float = 3, n_points: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the normal distribution.

        Parameters
        ----------
        x : np.ndarray, optional
            The input x-values (particle sizes) over which to compute the PDF. If not provided, a range is generated.
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the standard deviation from the mean. Default is -3.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the standard deviation from the mean. Default is 3.
        n_points : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        if x is None:
            x = self._generate_default_x(x_min=x_min, x_max=x_max, n_points=n_points)

        common_units = x.units
        pdf = norm.pdf(
            x.magnitude,
            loc=self.mean.to(common_units).magnitude,
            scale=self.std_dev.to(common_units).magnitude
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Normal({self.mean:.3f~P}, {self.std_dev:.3f~P})"
