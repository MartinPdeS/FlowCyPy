from typing import Tuple, Optional

import numpy as np
from pydantic.dataclasses import dataclass
from scipy.stats import norm
from TypedUnit import AnyUnit

from FlowCyPy.distribution.base_class import Base
from FlowCyPy.utils import config_dict


@dataclass(config=config_dict)
class Normal(Base):
    r"""
    Normal (Gaussian) distribution with optional hard cutoff.

    This class represents a normal distribution for a particle property such as
    diameter or refractive index. It supports an optional hard lower cutoff that
    turns the sampler into a truncated normal distribution conditional on

    .. math::
        X \ge x_{\mathrm{cut}}.

    Without cutoff
    --------------
    Samples are drawn from:

    .. math::
        X \sim \mathcal{N}(\mu, \sigma^2).

    With cutoff
    -----------
    Samples are drawn from the conditional distribution:

    .. math::
        X \mid X \ge x_{\mathrm{cut}}.

    This is implemented by inverse CDF sampling on the restricted probability
    interval ``[F(x_cut), 1)`` where ``F`` is the Gaussian CDF. This avoids
    rejection sampling and provides predictable performance even when the cutoff
    is far into the tail.

    Parameters
    ----------
    mean
        Mean value :math:`\mu` of the distribution, with units.
    standard_deviation
        Standard deviation :math:`\sigma` of the distribution, with the same
        units as ``mean``.
    cutoff
        Optional hard minimum value. If provided, generated samples satisfy
        ``x >= cutoff`` by construction.
    """

    mean: AnyUnit
    standard_deviation: AnyUnit
    cutoff: Optional[AnyUnit] = None

    @property
    def _units(self) -> AnyUnit:
        """
        Units used internally for computations.

        Returns
        -------
        AnyUnit
            Units of ``mean``.
        """
        return self.mean.units

    @property
    def _mean(self) -> AnyUnit:
        """
        Mean expressed in internal units.

        Returns
        -------
        AnyUnit
            Mean converted to ``self._units``.
        """
        return self.mean.to(self._units)

    @property
    def _standard_deviation(self) -> AnyUnit:
        """
        Standard deviation expressed in internal units.

        Returns
        -------
        AnyUnit
            Standard deviation converted to ``self._units``.
        """
        return self.standard_deviation.to(self._units)

    def cdf(self, x: AnyUnit) -> float:
        """
        Evaluate the Gaussian CDF at ``x`` (ignoring any cutoff).

        Parameters
        ----------
        x
            Quantity with the same units as ``mean``.

        Returns
        -------
        float
            CDF value in ``[0, 1]``.
        """
        x_value = x.to(self._units).magnitude
        mu = self._mean.magnitude
        sigma = self._standard_deviation.magnitude

        if sigma <= 0.0:
            raise ValueError("standard_deviation must be positive.")

        value = norm.cdf(x_value, loc=mu, scale=sigma)
        return float(np.clip(value, 0.0, 1.0))

    def survival_fraction_above(self, cutoff: AnyUnit) -> float:
        r"""
        Compute the survival fraction above a cutoff, ``P(X >= cutoff)``.

        This quantity is the concentration multiplier you would apply if you
        interpret the cutoff as physically removing all values below ``cutoff``
        from an otherwise unchanged population.

        Parameters
        ----------
        cutoff
            Hard minimum value with the same units as ``mean``.

        Returns
        -------
        float
            Survival fraction in ``[0, 1]``.
        """
        return float(np.clip(1.0 - self.cdf(cutoff), 0.0, 1.0))

    def apply_cutoff(
        self,
        cutoff: AnyUnit,
        reduce_concentration_consistently: bool = True,
    ) -> Tuple["Normal", float]:
        """
        Return a truncated Normal distribution and an optional concentration multiplier.

        Interpretation
        --------------
        - The returned distribution samples from ``X | X >= cutoff``.
        - If ``reduce_concentration_consistently`` is True, the returned multiplier
          is ``P(X >= cutoff)`` so that concentration can be scaled consistently
          with the same underlying distribution.
        - If False, the multiplier is 1.0.

        Parameters
        ----------
        cutoff
            Hard minimum value for truncation.
        reduce_concentration_consistently
            Whether to return the survival fraction as a concentration multiplier.

        Returns
        -------
        truncated_distribution, concentration_multiplier
            ``truncated_distribution`` is a new instance with ``cutoff`` set.
            ``concentration_multiplier`` is either the survival fraction or 1.0.
        """
        truncated_distribution = Normal(
            mean=self.mean,
            standard_deviation=self.standard_deviation,
            cutoff=cutoff,
        )

        concentration_multiplier = (
            self.survival_fraction_above(cutoff=cutoff)
            if reduce_concentration_consistently
            else 1.0
        )

        return truncated_distribution, concentration_multiplier

    @Base.pre_generate
    def generate(self, n_samples: int) -> AnyUnit:
        r"""
        Generate random samples.

        Without cutoff
        --------------
        Samples are drawn directly from ``Normal(mean, standard_deviation)``.

        With cutoff
        -----------
        Samples are drawn from the truncated normal distribution
        ``X | X >= cutoff`` using inverse CDF sampling:

        1. Compute :math:`p_0 = F(cutoff)`.
        2. Draw ``u ~ Uniform(0, 1)`` and set ``p = p0 + u (1 - p0)``.
        3. Return :math:`x = F^{-1}(p)`.

        Parameters
        ----------
        n_samples
            Number of samples to draw.

        Returns
        -------
        AnyUnit
            Samples with the same units as ``mean``.

        Raises
        ------
        ValueError
            If ``standard_deviation`` is not strictly positive.
        """
        if n_samples <= 0:
            return np.array([]) * self._units

        mu = float(self._mean.magnitude)
        sigma = float(self._standard_deviation.magnitude)
        if sigma <= 0.0:
            raise ValueError("standard_deviation must be positive.")

        uniform_samples = np.random.uniform(size=int(n_samples))
        uniform_samples = np.clip(uniform_samples, 1e-12, 1.0 - 1e-12)

        if self.cutoff is None:
            samples = np.random.normal(loc=mu, scale=sigma, size=int(n_samples))
            return samples

        cutoff_value = self.cutoff.to(self._units).magnitude

        cdf_at_cutoff = norm.cdf(cutoff_value, loc=mu, scale=sigma)
        cdf_at_cutoff = float(np.clip(cdf_at_cutoff, 0.0, 1.0 - 1e-15))

        probabilities = cdf_at_cutoff + uniform_samples * (1.0 - cdf_at_cutoff)
        probabilities = np.clip(probabilities, 1e-12, 1.0 - 1e-12)

        samples = norm.ppf(probabilities, loc=mu, scale=sigma)

        samples = np.maximum(samples, cutoff_value)

        return samples

    def _generate_default_x(
        self, x_min: float = -3, x_max: float = 3, n_samples: int = 200
    ) -> np.ndarray:
        """
        Generate a default x grid for plotting.

        The grid spans ``[mu + x_min sigma, mu + x_max sigma]`` in internal units.

        Parameters
        ----------
        x_min
            Lower bound in units of sigma relative to the mean.
        x_max
            Upper bound in units of sigma relative to the mean.
        n_samples
            Number of points in the returned grid.

        Returns
        -------
        np.ndarray
            1D array of x values with units.
        """
        if x_min >= x_max:
            raise ValueError("x_min must be less than x_max.")

        mu = float(self._mean.magnitude)
        sigma = float(self._standard_deviation.magnitude)

        x_min_value = mu + float(x_min) * sigma
        x_max_value = mu + float(x_max) * sigma

        return np.linspace(x_min_value, x_max_value, int(n_samples)) * self._units

    def get_pdf(
        self,
        x: np.ndarray = None,
        x_min: float = -3,
        x_max: float = 3,
        n_samples: int = 200,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return x values and the PDF.

        If ``cutoff`` is None, this returns the standard normal PDF.

        If ``cutoff`` is set, this returns the truncated PDF:

            pdf_trunc(x) = pdf(x) / P(X >= cutoff)   for x >= cutoff
                           0                          otherwise

        Parameters
        ----------
        x
            Optional x grid with units. If not provided, a default grid is generated.
        x_min
            Lower bound in sigma units for the default grid.
        x_max
            Upper bound in sigma units for the default grid.
        n_samples
            Number of points used for the default grid.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            ``x`` with units and ``pdf`` as a unitless NumPy array.
        """
        if x is None:
            x = self._generate_default_x(x_min=x_min, x_max=x_max, n_samples=n_samples)

        x_in_units = x.to(self._units)
        x_values = x_in_units.magnitude

        mu = float(self._mean.magnitude)
        sigma = float(self._standard_deviation.magnitude)

        pdf = norm.pdf(x_values, loc=mu, scale=sigma)

        if self.cutoff is not None:
            cutoff_value = self.cutoff.to(self._units).magnitude
            survival = 1.0 - norm.cdf(cutoff_value, loc=mu, scale=sigma)
            survival = float(np.clip(survival, 1e-15, 1.0))

            pdf = np.where(x_values >= cutoff_value, pdf / survival, 0.0)

        return x_in_units, pdf

    def __repr__(self) -> str:
        if self.cutoff is None:
            return f"Normal({self.mean:.3f~P}, {self.standard_deviation:.3f~P})"
        return f"Normal({self.mean:.3f~P}, {self.standard_deviation:.3f~P}, cutoff={self.cutoff:.3f~P})"
