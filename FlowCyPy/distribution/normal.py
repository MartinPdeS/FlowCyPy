from FlowCyPy.distribution.base_class import BaseDistribution
from dataclasses import dataclass
import numpy as np
from typing import Tuple, Optional
from scipy.stats import norm
from FlowCyPy import ureg


@dataclass
class NormalDistribution(BaseDistribution):
    r"""
    Represents a normal (Gaussian) distribution for particle sizes.

    The normal distribution is described by its mean and standard deviation:

    .. math::
        f(x) = \frac{1}{\sqrt{2 \pi \sigma^2}} \exp \left( - \frac{(x - \mu)^2}{2 \sigma^2} \right)

    where:
    - :math:`\mu` is the mean of the distribution (average particle size).
    - :math:`\sigma` is the standard deviation (width of the distribution).
    - :math:`x` represents particle sizes.

    Attributes
    ----------
    mean : float
        The mean (average) particle size in meters.
    std_dev : float
        The standard deviation of particle sizes in meters.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    mean: float
    std_dev: float
    scale_factor: Optional[float] = 1.0

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
            loc=self.mean,
            scale=self.std_dev,
            size=n_samples.magnitude
        ) * ureg.meter

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the normal distribution.

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
        pdf = norm.pdf(x, loc=self.mean, scale=self.std_dev)
        return x, self.scale_factor * pdf
