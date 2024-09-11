from dataclasses import dataclass
from typing import Optional
import numpy as np
from typing import Tuple
from FlowCyPy.units import Quantity
from FlowCyPy.distribution.base_class import BaseDistribution
from pydantic.dataclasses import dataclass

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class WeibullDistribution(BaseDistribution):
    r"""
    Represents a Weibull distribution for particle sizes.

    The Weibull distribution is commonly used for modeling size distributions in biological systems.

    Attributes
    ----------
    shape : Quantity
        The shape parameter (k), controls the skewness of the distribution.
    scale : Quantity
        The scale parameter (λ), controls the spread of the distribution.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    shape: Quantity
    scale: Quantity
    scale_factor: Optional[float] = 1.0

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
        common_unit = self.shape.units

        return np.random.weibull(
            self.shape.magnitude,
            size=n_samples.magnitude
        ) * common_unit

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
        a = self.shape / self.scale
        b = (x / self.scale)
        c =  np.exp(-(x / self.scale) ** self.shape)
        pdf = a * b ** (self.shape - 1) * c

        return x, self.scale_factor * pdf
