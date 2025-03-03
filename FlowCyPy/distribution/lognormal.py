from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from scipy.stats import lognorm
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


@dataclass(config=config_dict)
class LogNormal(Base):
    r"""
    Represents a log-normal distribution for particle properties.

    The log-normal distribution is described by its mean and standard deviation of the logarithm of the values:

    .. math::
        f(x) = \frac{1}{x \sigma \sqrt{2 \pi}} \exp \left( - \frac{(\ln(x) - \mu)^2}{2 \sigma^2} \right)

    where:
    - :math:`\mu` is the mean of the natural logarithm of the particle properties.
    - :math:`\sigma` is the standard deviation of the logarithm of particle properties.

    Parameters
    ----------
    mean : Quantity
        The mean particle properties.
    std_dev : Quantity
        The standard deviation of the logarithm of particle properties.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the properties).
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
    def generate(self, n_samples: int) -> Quantity:
        """
        Generates a log-normal distribution of scatterer properties.

        The generated properties follow a log-normal distribution, where the logarithm of the properties is normally distributed.

        Parameters
        ----------
        n_samples : Quantity
            The number of particle properties to generate.

        Returns
        -------
        Quantity
            An array of scatterer properties in meters.
        """
        return np.random.lognormal(
            mean=self._mean.magnitude,
            sigma=self._std_dev.magnitude,
            size=n_samples
        )

    def _generate_default_x(self, x_min: float = 0.01, x_max: float = 5, n_samples: int = 40) -> np.ndarray:
        """
        Generates a range of x-values based on the log-normal distribution parameters.

        Parameters
        ----------
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the mean. Default is 0.01.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the mean. Default is 5.
        n_samples : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        np.ndarray
            A range of x-values with appropriate units.
        """
        if x_min <= 0:
            raise ValueError("x_min must be greater than 0.")
        if x_min >= x_max:
            raise ValueError("x_min must be less than x_max.")

        scale = self.mean.magnitude
        x_min_value = x_min * scale
        x_max_value = x_max * scale
        return np.linspace(x_min_value, x_max_value, n_samples) * self._units

    def get_pdf(self, x_min: float = 0.9, x_max: float = 1.1, n_samples: int = 40) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the PDF values for the log-normal distribution.

        Parameters
        ----------
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the mean. Default is 0.01.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the mean. Default is 5.
        n_samples : int, optional
            Number of points in the generated range. Default is 500.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        x = self._generate_default_x(x_min=x_min, x_max=x_max, n_samples=n_samples)

        pdf = lognorm.pdf(x.magnitude, s=self._std_dev, scale=self._mean.magnitude)

        return x, pdf

    def __repr__(self) -> str:
        return f"Log-Normal({self.mean:.3f~P}, {self.std_dev:.3f~P})"
