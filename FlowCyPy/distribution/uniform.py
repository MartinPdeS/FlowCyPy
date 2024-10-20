from FlowCyPy.distribution.base_class import Base
import numpy as np
from typing import Tuple
from scipy.stats import uniform
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Uniform(Base):
    r"""
    Represents a uniform distribution for particle sizes.

    The uniform distribution assigns equal probability to all particle sizes within a specified range:

    .. math::
        f(x) = \frac{1}{b - a} \quad \text{for} \quad a \leq x \leq b

    where:
    - :math:`a` is the lower bound of the distribution.
    - :math:`b` is the upper bound of the distribution.

    Parameters
    ----------
    lower_bound : float
        The lower bound for particle sizes in meters.
    upper_bound : float
        The upper bound for particle sizes in meters.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    lower_bound: Quantity
    upper_bound: Quantity
    _name = 'Uniform'

    def __post_init__(self):
        self._main_units = self.lower_bound.units

    def generate(self, n_samples: Quantity) -> Quantity:
        """
        Generates a uniform distribution of scatterer sizes.

        The generated sizes are uniformly distributed between the specified `lower_bound` and `upper_bound`.

        Parameters
        ----------
        n_samples : Quantity
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of scatterer sizes in meters.
        """
        return np.random.uniform(
            self.lower_bound.to(self._main_units).magnitude,
            self.upper_bound.to(self._main_units).magnitude,
            n_samples.magnitude
        ) * self._main_units

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
        common_unit = self.lower_bound.units

        pdf = uniform.pdf(
            x.to(common_unit).magnitude,
            loc=self.lower_bound.magnitude,
            scale=self.upper_bound.to(common_unit).magnitude - self.lower_bound.magnitude
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Uniform({self.lower_bound:.3f~P}, {self.upper_bound:.3f~P})"
