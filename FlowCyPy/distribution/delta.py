
from FlowCyPy.distribution.base_class import BaseDistribution
from dataclasses import dataclass
import numpy as np
from typing import Tuple, Optional
from FlowCyPy import ureg

@dataclass
class DeltaDistribution(BaseDistribution):
    """
    Represents a delta-like distribution for particle sizes.

    In a delta distribution, all particle sizes are the same, representing a delta function:

    .. math::
        f(x) = \delta(x - x_0)

    where:
    - :math:`x_0` is the singular particle size.

    Attributes
    ----------
    size_value : float
        The particle size for the delta distribution in meters.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    size_value: float
    scale_factor: Optional[float] = 1.0

    def generate(self, n_samples: int) -> np.ndarray:
        """
        Generates a singular distribution of scatterer sizes.

        All sizes generated will be exactly the same as `size_value`.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of identical scatterer sizes in meters.
        """
        return np.full(n_samples.magnitude, self.size_value) * ureg.meter

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the singular distribution.

        The PDF is represented as a delta-like function centered at `size_value`.

        Parameters
        ----------
        x : np.ndarray
            The input x-values (particle sizes) over which to compute the PDF.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding scaled PDF values.
        """
        pdf = np.zeros_like(x)
        idx = (np.abs(x - self.size_value)).argmin()  # Delta-like function for singular value
        pdf[idx] = 1.0
        return x, self.scale_factor * pdf
