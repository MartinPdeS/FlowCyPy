from typing import Tuple

import numpy as np
from pydantic.dataclasses import dataclass
from TypedUnit import Length, RefractiveIndex

from FlowCyPy.distribution.base_class import Base
from FlowCyPy.utils import config_dict


@dataclass(config=config_dict)
class Weibull(Base):
    r"""
    Represents a Weibull distribution for particle properties.

    The Weibull distribution is commonly used for modeling property distributions in biological systems.

    Parameters
    ----------
    shape : Length | RefractiveIndex
        The shape parameter (k), controls the skewness of the distribution.
    scale : Length | RefractiveIndex
        The scale parameter (λ), controls the spread of the distribution.
    """

    shape: Length | RefractiveIndex
    scale: Length | RefractiveIndex

    @property
    def _units(self) -> Length | RefractiveIndex:
        return self.shape.units

    @property
    def _shape(self) -> Length | RefractiveIndex:
        return self.shape.to(self._units)

    @property
    def _scale(self) -> Length | RefractiveIndex:
        return self.scale.to(self._units)

    def _generate_default_x(
        self, n_samples: int, x_min_factor: float, x_max_factor: float
    ) -> Length | RefractiveIndex:
        """
        Generates a default range of x-values for the Weibull distribution.

        Parameters
        ----------
        n_samples : int, optional
            Number of points in the generated range.
        x_min_factor : float, optional
            Factor for the minimum x-value relative to the scale parameter.
        x_max_factor : float, optional
            Factor for the maximum x-value relative to the scale parameter.

        Returns
        -------
        Length | RefractiveIndex
            A range of x-values with appropriate units.
        """

        if x_min_factor <= 0:
            raise ValueError("x_min_factor must be greater than 0.")

        x_min = self.scale.magnitude * x_min_factor
        x_max = self.scale.magnitude * x_max_factor
        return np.linspace(x_min, x_max, n_samples) * self.scale.units

    @Base.pre_generate
    def generate(self, n_samples: int) -> Length | RefractiveIndex:
        """
        Generates a Weibull distribution of scatterer properties.

        Parameters
        ----------
        n_samples : int
            The number of particle properties to generate.

        Returns
        -------
        Length | RefractiveIndex
            An array of particle properties in meters.
        """
        return np.random.weibull(self.shape.magnitude, size=n_samples)

    def get_pdf(
        self, n_samples: int = 100
    ) -> Tuple[Length | RefractiveIndex, np.ndarray]:
        """
        Returns the x-values and the PDF values for the Weibull distribution.

        If `x` is not provided, a default range of x-values is generated.

        Parameters
        ----------
        x : Length | RefractiveIndex, optional
            The input x-values (particle properties) over which to compute the PDF. If not provided, a range is generated.
        n_points : int, optional
            Number of points in the generated range if `x` is not provided. Default is 100.

        Returns
        -------
        Tuple[Length | RefractiveIndex, np.ndarray]
            The input x-values and the corresponding PDF values.
        """
        x = self._generate_default_x(n_samples=n_samples)

        common_units = self.scale.units
        scale_magnitude = self.scale.to(common_units).magnitude
        shape_magnitude = self.shape.to(common_units).magnitude

        pdf = (
            (shape_magnitude / scale_magnitude)
            * (
                (x.to(common_units).magnitude / scale_magnitude)
                ** (shape_magnitude - 1)
            )
            * np.exp(
                -((x.to(common_units).magnitude / scale_magnitude) ** shape_magnitude)
            )
        )

        return x, pdf

    def __repr__(self) -> str:
        return f"Weibull(shape={self.shape:.3f~P}, scale={self.scale:.3f~P})"
