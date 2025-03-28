import numpy as np
from typing import Optional, Tuple, Callable
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from FlowCyPy.units import Quantity

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)

class Base:
    """
    Base class for distributions used to define particle diameters in the flow cytometer.

    This class provides a structure for generating random scatterer diameters based on different statistical distributions.
    Each subclass must implement the `generate` method to generate a distribution of diameters and `get_pdf` to compute the
    probability density function (PDF) values.

    Parameters
    ----------
    scale_factor : float
        A scaling factor applied to the PDF of the distribution. By default, it is set to 1 (equal weight).
    """

    scale_factor: Optional[float] = 1.0

    def generate(self, n_samples: int) -> np.ndarray:
        """Generate a distribution of scatterer diameters."""
        raise NotImplementedError("Must be implemented by subclasses")

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the probability density function (PDF) values."""
        raise NotImplementedError("Must be implemented by subclasses")

    def plot(self, n_samples: int = 4000, bins: int = 50) -> None:
        """
        Plots a histogram of the generated particle diameters based on the log-normal distribution.

        Parameters
        ----------
        n_samples : int, optional
            The number of particle diameters to generate for the histogram (default is 1000).
        bins : int, optional
            The number of bins in the histogram (default is 50).
        """
        samples = self.generate(n_samples)

        # Plotting the PDF
        with plt.style.context(mps):  # Assuming mps is a custom style
            figure, ax = plt.subplots(1, 1)
            ax.hist(samples, bins=bins, color='blue', edgecolor='black', alpha=0.7)

            ax.set(
                title='Distribution',
                xlabel=f'Distributed parameter [{self._units}]',
                ylabel='Probability Density Function (PDF)'
            )

            plt.show()

    def __str__(self) -> str:
        return self.__repr__()

    def pre_generate(function: Callable) -> Callable:
        def wrapper(self, n_samples: Quantity):

            return function(self=self, n_samples=n_samples) * self._units

        return wrapper