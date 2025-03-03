from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from scipy.stats import norm
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


@dataclass(config=config_dict)
class Normal(Base):
    r"""
    Represents a normal (Gaussian) distribution for particle properties.

    The normal distribution is described by its mean and standard deviation:

    .. math::
        f(x) = \frac{1}{\sqrt{2 \pi \sigma^2}} \exp \left( - \frac{(x - \mu)^2}{2 \sigma^2} \right)

    where:
    - :math:`\mu` is the mean of the distribution (average particle property).
    - :math:`\sigma` is the standard deviation (width of the distribution).
    - :math:`x` represents particle properties.

    Parameters
    ----------
    mean : Quantity
        The mean (average) particle property in meters.
    std_dev : Quantity
        The standard deviation of particle properties in meters.
    """

    mean: Quantity
    std_dev: Quantity

    @property
    def _units(self) -> Quantity:
        return self.mean.units

    @property
    def _mean(self) -> Quantity:
        return self.mean.to(self._units)

    @property
    def _std_dev(self) -> Quantity:
        return self.std_dev.to(self._units)

    @Base.pre_generate
    def generate(self, n_samples: int) -> np.ndarray:
        """
        Generates a normal distribution of scatterer properties.

        The generated properties are based on the normal distribution's mean and standard deviation.

        Parameters
        ----------
        n_samples : int
            The number of particle properties to generate.

        Returns
        -------
        np.ndarray
            An array of scatterer properties in meters.
        """
        return np.random.normal(
            loc=self._mean.magnitude,
            scale=self._std_dev.magnitude,
            size=n_samples
        )

    def _generate_default_x(self, x_min: float = -3, x_max: float = 3, n_samples: int = 20) -> np.ndarray:
        """
        Generates a range of x-values based on the mean and standard deviation.

        Parameters
        ----------
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the standard deviation from the mean. Default is -3.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the standard deviation from the mean. Default is 3.
        n_samples : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        np.ndarray
            A range of x-values with appropriate units.
        """
        if x_min >= x_max:
            raise ValueError("x_min must be less than x_max.")

        mu = self._mean.magnitude
        sigma = self._std_dev.magnitude
        x_min_value = mu + x_min * sigma
        x_max_value = mu + x_max * sigma
        return np.linspace(x_min_value, x_max_value, n_samples) * self._units

    def get_pdf(self, x: np.ndarray = None, x_min: float = -3, x_max: float = 3, n_samples: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the normal distribution.

        Parameters
        ----------
        x : np.ndarray, optional
            The input x-values (particle properties) over which to compute the PDF. If not provided, a range is generated.
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the standard deviation from the mean. Default is -3.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the standard deviation from the mean. Default is 3.
        n_samples : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        x = self._generate_default_x(x_min=x_min, x_max=x_max, n_samples=n_samples)

        pdf = norm.pdf(
            x.magnitude,
            loc=self.mean.magnitude,
            scale=self.std_dev.magnitude
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Normal({self.mean:.3f~P}, {self.std_dev:.3f~P})"
