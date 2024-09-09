from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple

class BaseDistribution:
    """
    Base class for distributions used to define particle sizes in the flow cytometer.

    This class provides a structure for generating random scatterer sizes based on different statistical distributions.
    Each subclass must implement the `generate` method to generate a distribution of sizes and `get_pdf` to compute the
    probability density function (PDF) values.

    Attributes
    ----------
    scale_factor : float
        A scaling factor applied to the PDF of the distribution. By default, it is set to 1 (equal weight).
    """

    scale_factor: Optional[float] = 1.0

    def generate(self, n_samples: int) -> np.ndarray:
        """Generate a distribution of scatterer sizes."""
        raise NotImplementedError("Must be implemented by subclasses")

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the probability density function (PDF) values."""
        raise NotImplementedError("Must be implemented by subclasses")
