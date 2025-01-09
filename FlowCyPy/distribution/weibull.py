from FlowCyPy.distribution.base_class import Base, config_dict
import numpy as np
from typing import Tuple
from PyMieSim.units import Quantity
from pydantic.dataclasses import dataclass


@dataclass(config=config_dict)
class Weibull(Base):
    r"""
    Represents a Weibull distribution for particle sizes.

    The Weibull distribution is commonly used for modeling size distributions in biological systems.

    Parameters
    ----------
    shape : Quantity
        The shape parameter (k), controls the skewness of the distribution.
    scale : Quantity
        The scale parameter (λ), controls the spread of the distribution.
    """

    shape: Quantity
    scale: Quantity
    _name = 'Weibull'

    def __post_init__(self):
        self.scale = self.scale.to(self.shape.units)

    def _generate_default_x(self, n_points: int = 100, x_min_factor: float = 0.01, x_max_factor: float = 5) -> Quantity:
        """
        Generates a default range of x-values for the Weibull distribution.

        Parameters
        ----------
        n_points : int, optional
            Number of points in the generated range. Default is 100.
        x_min_factor : float, optional
            Factor for the minimum x-value relative to the scale parameter. Default is 0.01.
        x_max_factor : float, optional
            Factor for the maximum x-value relative to the scale parameter. Default is 5.

        Returns
        -------
        Quantity
            A range of x-values with appropriate units.
        """
        if n_points < 2:
            raise ValueError("n_points must be at least 2.")
        if x_min_factor <= 0:
            raise ValueError("x_min_factor must be greater than 0.")

        x_min = self.scale.magnitude * x_min_factor
        x_max = self.scale.magnitude * x_max_factor
        return np.linspace(x_min, x_max, n_points) * self.scale.units

    def generate(self, n_samples: int) -> Quantity:
        """
        Generates a Weibull distribution of scatterer sizes.

        Parameters
        ----------
        n_samples : int
            The number of particle sizes to generate.

        Returns
        -------
        Quantity
            An array of particle sizes in meters.
        """
        return np.random.weibull(
            self.shape.magnitude,
            size=n_samples
        ) * self.shape.units

    def get_pdf(self, x: Quantity = None, n_points: int = 100) -> Tuple[Quantity, np.ndarray]:
        """
        Returns the x-values and the PDF values for the Weibull distribution.

        If `x` is not provided, a default range of x-values is generated.

        Parameters
        ----------
        x : Quantity, optional
            The input x-values (particle sizes) over which to compute the PDF. If not provided, a range is generated.
        n_points : int, optional
            Number of points in the generated range if `x` is not provided. Default is 100.

        Returns
        -------
        Tuple[Quantity, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        if x is None:
            x = self._generate_default_x(n_points=n_points)

        common_units = self.scale.units
        scale_magnitude = self.scale.to(common_units).magnitude
        shape_magnitude = self.shape.to(common_units).magnitude

        pdf = (shape_magnitude / scale_magnitude) * \
              ((x.to(common_units).magnitude / scale_magnitude) ** (shape_magnitude - 1)) * \
              np.exp(-(x.to(common_units).magnitude / scale_magnitude) ** shape_magnitude)

        return x, pdf

    def __repr__(self) -> str:
        return f"Weibull(shape={self.shape:.3f~P}, scale={self.scale:.3f~P})"
