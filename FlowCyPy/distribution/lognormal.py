from FlowCyPy.distribution.base_class import Base
import numpy as np
from typing import Tuple
from scipy.stats import lognorm
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


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
        self._main_units = self.mean.units

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
            mean=self.mean.to(self._main_units).magnitude,
            sigma=self.std_dev.to(self._main_units).magnitude,
            size=n_samples.magnitude
        ) * self._main_units

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the x-values and the scaled PDF values for the log-normal distribution.

        Parameters
        ----------
        x : np.ndarray
            The input x-values (particle sizes) over which to compute the PDF.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            The input x-values and the corresponding scaled PDF values.
        """
        common_units = x.units

        pdf = lognorm.pdf(
            x.to(common_units).magnitude,
            s=self.std_dev.to(common_units).magnitude,
            scale=self.mean.to(common_units).magnitude
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Log-Normal({self.mean:.3f~P}, {self.std_dev:.3f~P})"
