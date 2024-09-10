from dataclasses import dataclass
from typing import Optional
import numpy as np
from typing import Tuple
from FlowCyPy.units import Quantity
from FlowCyPy.distribution.base_class import BaseDistribution

@dataclass
class WeibullDistribution(BaseDistribution):
    r"""
    Represents a Weibull distribution for particle sizes.

    The Weibull distribution is commonly used for modeling size distributions in biological systems.

    Attributes
    ----------
    shape : float
        The shape parameter (k), controls the skewness of the distribution.
        Default is 1.5, which gives a moderate skewness.
    scale : float
        The scale parameter (λ), controls the spread of the distribution.
        Default is 1.0, which defines the average size.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    shape: Optional[float] = 1.5  # Default shape parameter
    scale: Optional[float] = 1.0  # Default scale parameter
    scale_factor: Optional[float] = 1.0

    def __post_init__(self):
        if isinstance(self.shape, Quantity):
            self.shape = self.shape.to_base_units().magnitude

        if isinstance(self.scale, Quantity):
            self.scale = self.scale.to_base_units().magnitude

    def generate(self, n_samples: int) -> np.ndarray:
        """
        Generates a Weibull distribution of scatterer sizes.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of particle sizes in meters.
        """
        return np.random.weibull(
            self.shape,
            n_samples.magnitude
        )

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the PDF values for the Weibull distribution.

        Parameters
        ----------
        x : np.ndarray
            The input x-values (particle sizes) over which to compute the PDF.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        pdf = (self.shape / self.scale) * (x / self.scale) ** (self.shape - 1) * np.exp(-(x / self.scale) ** self.shape)

        return x, self.scale_factor * pdf
