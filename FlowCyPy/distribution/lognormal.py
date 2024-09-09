from FlowCyPy.distribution.base_class import BaseDistribution
from dataclasses import dataclass
import numpy as np
from typing import Tuple, Optional
from scipy.stats import lognorm
from FlowCyPy import ureg


@dataclass
class LogNormalDistribution(BaseDistribution):
    r"""
    Represents a log-normal distribution for particle sizes.

    The log-normal distribution is described by its mean and standard deviation of the logarithm of the values:

    .. math::
        f(x) = \frac{1}{x \sigma \sqrt{2 \pi}} \exp \left( - \frac{(\ln(x) - \mu)^2}{2 \sigma^2} \right)

    where:
    - :math:`\mu` is the mean of the natural logarithm of the particle sizes.
    - :math:`\sigma` is the standard deviation of the logarithm of particle sizes.

    Attributes
    ----------
    mean : float
        The mean particle size in meters.
    std_dev : float
        The standard deviation of the logarithm of particle sizes.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    mean: float
    std_dev: float
    scale_factor: Optional[float] = 1.0

    def generate(self, n_samples: int) -> np.ndarray:
        """
        Generates a log-normal distribution of scatterer sizes.

        The generated sizes follow a log-normal distribution, where the logarithm of the sizes is normally distributed.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of scatterer sizes in meters.
        """
        return np.random.lognormal(
            mean=self.mean,
            sigma=self.std_dev,
            size=n_samples.magnitude
        ) * ureg.meter

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the log-normal distribution.

        The `scale_factor` is applied to the PDF, not the generated sizes.

        Parameters
        ----------
        x : np.ndarray
            The input x-values (particle sizes) over which to compute the PDF.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding scaled PDF values.
        """
        pdf = lognorm.pdf(x, s=self.std_dev, scale=self.mean)

        return x, self.scale_factor * pdf