
from FlowCyPy.distribution.base_class import Base
import numpy as np
from typing import Tuple
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Delta(Base):
    r"""
    Represents a delta-like distribution for particle sizes.

    In a delta distribution, all particle sizes are the same, representing a delta function:

    .. math::
        f(x) = \delta(x - x_0)

    where:
    - :math:`x_0` is the singular particle size.

    Parameters
    ----------
    position : Quantity
        The particle size for the delta distribution in meters.
    scale_factor : float, optional
        A scaling factor applied to the PDF (not the sizes).
    """

    position: Quantity
    _name = 'Delta'

    def __post_init__(self):
        self._main_units = self.position.units

    def generate(self, n_samples: int) -> np.ndarray:
        r"""
        Generates a singular distribution of scatterer sizes.

        All sizes generated will be exactly the same as `position`.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        np.ndarray
            An array of identical scatterer sizes in meters.
        """
        return np.ones(n_samples.magnitude) * self.position.magnitude * self._main_units

    def get_pdf(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        r"""
        Returns the x-values and the scaled PDF values for the singular distribution.

        The PDF is represented as a delta-like function centered at `position`.

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

        pdf = np.zeros_like(x)

        idx = (np.abs(x.magnitude - self.position.to(common_units).magnitude)).argmin()  # Delta-like function for singular value
        pdf[idx] = 1.0
        return x, pdf

    def __repr__(self) -> str:
        return f"Delta({self.position:.3f~P})"
