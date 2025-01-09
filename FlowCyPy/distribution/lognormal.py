from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from scipy.stats import lognorm
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


@dataclass(config=config_dict)
class LogNormal(Base):
    r"""
    Represents a log-normal distribution for particle sizes.

    The log-normal distribution is described by its mean and standard deviation of the logarithm of the values:

    .. math::
        f(x) = \frac{1}{x \sigma \sqrt{2 \pi}} \exp \left( - \frac{(\ln(x) - \mu)^2}{2 \sigma^2} \right)

    where:
    - :math:`\mu` is the mean of the natural logarithm of the particle sizes.
    - :math:`\sigma` is the standard deviation of the logarithm of particle sizes.

    Parameters
    ----------
    mean : Quantity
        The mean particle size in meters.
    std_dev : Quantity
        The standard deviation of the logarithm of particle sizes.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    mean: Quantity
    std_dev: Quantity
    _name = 'Log-normal'

    def __post_init__(self):
        self.std_dev = self.std_dev.to(self.mean.units)

    def generate(self, n_samples: int) -> Quantity:
        """
        Generates a log-normal distribution of scatterer sizes.

        The generated sizes follow a log-normal distribution, where the logarithm of the sizes is normally distributed.

        Parameters
        ----------
        n_samples : Quantity
            The number of particle sizes to generate.

        Returns
        -------
        Quantity
            An array of scatterer sizes in meters.
        """
        return np.random.lognormal(
            mean=self.mean.magnitude,
            sigma=self.std_dev.magnitude,
            size=n_samples.magnitude
        ) * self.mean.units

    def _generate_default_x(self, x_min: float = 0.01, x_max: float = 5, n_points: int = 40) -> np.ndarray:
        """
        Generates a range of x-values based on the log-normal distribution parameters.

        Parameters
        ----------
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the mean. Default is 0.01.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the mean. Default is 5.
        n_points : int, optional
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
        if n_points < 2:
            raise ValueError("n_points must be at least 2.")

        scale = self.mean.magnitude
        x_min_value = x_min * scale
        x_max_value = x_max * scale
        return np.linspace(x_min_value, x_max_value, n_points) * self.mean.units

    def get_pdf(self, x: np.ndarray = None, x_min: float = 0.9, x_max: float = 1.1, n_points: int = 40) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the PDF values for the log-normal distribution.

        Parameters
        ----------
        x : np.ndarray, optional
            The input x-values (particle sizes) over which to compute the PDF. If not provided, a range is generated.
        x_min : float, optional
            Factor for the minimum x-value as a multiple of the mean. Default is 0.01.
        x_max : float, optional
            Factor for the maximum x-value as a multiple of the mean. Default is 5.
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
        pdf = lognorm.pdf(
            x.to(common_units).magnitude,
            s=self.std_dev,  # Shape parameter
            scale=self.mean.to(common_units).magnitude  # Scale parameter
        )

        return x, pdf


    def __repr__(self) -> str:
        return f"Log-Normal({self.mean:.3f~P}, {self.std_dev:.3f~P})"
