from FlowCyPy.distribution.base_class import BaseDistribution
from dataclasses import dataclass
import numpy as np
from typing import Tuple, Optional
from scipy.stats import uniform
from FlowCyPy import ureg


@dataclass
class UniformDistribution(BaseDistribution):
    r"""
    Represents a uniform distribution for particle sizes.

    The uniform distribution assigns equal probability to all particle sizes within a specified range:

    .. math::
        f(x) = \frac{1}{b - a} \quad \text{for} \quad a \leq x \leq b

    where:
    - :math:`a` is the lower bound of the distribution.
    - :math:`b` is the upper bound of the distribution.

    Attributes
    ----------
    lower_bound : float
        The lower bound for particle sizes in meters.
    upper_bound : float
        The upper bound for particle sizes in meters.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    lower_bound: float
    upper_bound: float
    scale_factor: Optional[float] = 1.0

    def generate(self, n_samples: int) -> np.ndarray:
        """
        Generates a uniform distribution of scatterer sizes.

        The generated sizes are uniformly distributed between the specified `lower_bound` and `upper_bound`.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of scatterer sizes in meters.
        """
        return np.random.uniform(self.lower_bound, self.upper_bound, n_samples.magnitude) * ureg.meter

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the uniform distribution.

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
        pdf = uniform.pdf(x, loc=self.lower_bound, scale=self.upper_bound - self.lower_bound)
        return x, self.scale_factor * pdf