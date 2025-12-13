from typing import Tuple, Optional

import numpy as np
from pydantic.dataclasses import dataclass
from scipy.stats import lognorm
from TypedUnit import AnyUnit

from FlowCyPy.distribution.base_class import Base
from FlowCyPy.utils import config_dict


@dataclass(config=config_dict)
class LogNormal(Base):
    r"""
    Log normal distribution with optional hard cutoff.

    This class represents a log normal distribution for a positive particle
    property such as diameter or intensity. It supports an optional hard lower
    cutoff that turns the sampler into a truncated log normal distribution
    conditional on

    .. math::
        X \ge x_{\mathrm{cut}}.

    Definition
    ----------
    A log normal random variable is defined by

    .. math::
        \ln(X) \sim \mathcal{N}(\mu, \sigma^2),

    which implies the density

    .. math::
        f(x) = \frac{1}{x \sigma \sqrt{2\pi}}
               \exp\!\left(-\frac{(\ln x - \mu)^2}{2\sigma^2}\right),
        \quad x > 0.

    Parameterization used here
    --------------------------
    This implementation follows the NumPy and SciPy convention:

    - ``mean`` corresponds to :math:`\mu`, the mean of the underlying normal
      distribution of ``ln(X)``.
    - ``standard_deviation`` corresponds to :math:`\sigma`, the standard deviation
      of the underlying normal distribution of ``ln(X)``.

    In other words, ``mean`` and ``standard_deviation`` are parameters in log space.
    If you want to specify the arithmetic mean and standard deviation in linear
    space, you must convert them to :math:`\mu` and :math:`\sigma` before creating
    this distribution.

    Hard cutoff and truncation
    --------------------------
    When ``cutoff`` is provided, sampling is performed from the conditional law
    ``X | X >= cutoff`` by inverse CDF sampling on the restricted probability
    interval ``[F(cutoff), 1)`` where ``F`` is the log normal CDF.

    This provides an efficient way to emulate an idealized selection that removes
    all values below the cutoff. If you interpret the cutoff as a physical removal,
    you can compute the matching concentration multiplier via
    :meth:`survival_fraction_above`.

    Parameters
    ----------
    mean
        Log space mean :math:`\mu` with units carried for consistency with the
        rest of the framework. In practice, this should be dimensionless.
    standard_deviation
        Log space standard deviation :math:`\sigma`. In practice, this should be
        dimensionless and strictly positive.
    cutoff
        Optional hard minimum value for ``X`` in linear space, with the same
        units as the sampled property.
        If provided, generated samples satisfy ``x >= cutoff`` by construction.

    Notes
    -----
    - The sampled values are always positive by definition.
    - If you use this distribution for diameter, the log space parameters should
      be calibrated carefully, because the tail behavior can dominate coincidence
      and swarm statistics.
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
        Log space mean in internal units.

        Returns
        -------
        AnyUnit
            ``mean`` converted to ``self._units``.
        """
        return self.mean.to(self._units)

    @property
    def _standard_deviation(self) -> AnyUnit:
        """
        Log space standard deviation in internal units.

        Returns
        -------
        AnyUnit
            ``standard_deviation`` converted to ``self._units``.
        """
        return self.standard_deviation.to(self._units)

    def cdf(self, x: AnyUnit) -> float:
        """
        Evaluate the log normal CDF at ``x`` (ignoring any cutoff).

        Parameters
        ----------
        x
            Quantity with the same units as the sampled property.

        Returns
        -------
        float
            CDF value in ``[0, 1]``.
        """
        x_value = x.to(self._units).magnitude
        if x_value <= 0.0:
            return 0.0

        mu = float(self._mean.magnitude)
        sigma = float(self._standard_deviation.magnitude)
        if sigma <= 0.0:
            raise ValueError("standard_deviation must be positive.")

        value = lognorm.cdf(x_value, s=sigma, scale=np.exp(mu))
        return float(np.clip(value, 0.0, 1.0))

    def survival_fraction_above(self, cutoff: AnyUnit) -> float:
        """
        Compute the survival fraction above a cutoff, ``P(X >= cutoff)``.

        This is the concentration multiplier that is consistent with interpreting
        the cutoff as removing all values below ``cutoff`` from an otherwise
        unchanged population.

        Parameters
        ----------
        cutoff
            Hard minimum value in linear space, with the same units as the sampled
            property.

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
    ) -> Tuple["LogNormal", float]:
        """
        Return a truncated LogNormal distribution and an optional concentration multiplier.

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
            Hard minimum value for truncation (linear space).
        reduce_concentration_consistently
            Whether to return the survival fraction as a concentration multiplier.

        Returns
        -------
        truncated_distribution, concentration_multiplier
            ``truncated_distribution`` is a new instance with ``cutoff`` set.
            ``concentration_multiplier`` is either the survival fraction or 1.0.
        """
        truncated_distribution = LogNormal(
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
        Generate random samples in linear space.

        Without cutoff
        --------------
        Uses the NumPy generator:

        .. math::
            X = \exp(\mu + \sigma Z), \quad Z \sim \mathcal{N}(0, 1).

        With cutoff
        -----------
        Samples from ``X | X >= cutoff`` by inverse CDF sampling:

        1. Compute ``p0 = F(cutoff)``.
        2. Draw ``u ~ Uniform(0, 1)`` and set ``p = p0 + u (1 - p0)``.
        3. Return ``x = F^{-1}(p)``.

        Parameters
        ----------
        n_samples
            Number of samples to draw.

        Returns
        -------
        AnyUnit
            Samples in linear space with units.
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
            samples = np.random.lognormal(mean=mu, sigma=sigma, size=int(n_samples))
            return samples * self._units

        cutoff_value = self.cutoff.to(self._units).magnitude
        if cutoff_value <= 0.0:
            samples = np.random.lognormal(mean=mu, sigma=sigma, size=int(n_samples))
            return samples * self._units

        cdf_at_cutoff = lognorm.cdf(cutoff_value, s=sigma, scale=np.exp(mu))
        cdf_at_cutoff = float(np.clip(cdf_at_cutoff, 0.0, 1.0 - 1e-15))

        probabilities = cdf_at_cutoff + uniform_samples * (1.0 - cdf_at_cutoff)
        probabilities = np.clip(probabilities, 1e-12, 1.0 - 1e-12)

        samples = lognorm.ppf(probabilities, s=sigma, scale=np.exp(mu))

        samples = np.maximum(samples, cutoff_value)

        return samples * self._units

    def _generate_default_x(
        self, x_min: float = 0.01, x_max: float = 5.0, n_samples: int = 200
    ) -> np.ndarray:
        """
        Generate a default x grid for plotting in linear space.

        The grid is constructed as a multiplicative range around the scale implied
        by ``mean`` (in linear space this corresponds to ``exp(mu)``).

        Parameters
        ----------
        x_min
            Lower bound factor relative to ``exp(mu)``. Must be positive.
        x_max
            Upper bound factor relative to ``exp(mu)``. Must be greater than ``x_min``.
        n_samples
            Number of points in the returned grid.

        Returns
        -------
        np.ndarray
            1D array of x values with units.
        """
        if x_min <= 0:
            raise ValueError("x_min must be greater than 0.")
        if x_min >= x_max:
            raise ValueError("x_min must be less than x_max.")

        mu = float(self._mean.magnitude)
        scale_linear = float(np.exp(mu))

        x_min_value = float(x_min) * scale_linear
        x_max_value = float(x_max) * scale_linear

        return np.linspace(x_min_value, x_max_value, int(n_samples)) * self._units

    def get_pdf(
        self, x_min: float = 0.01, x_max: float = 5.0, n_samples: int = 200
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return x values and the PDF in linear space.

        If ``cutoff`` is None, this returns the standard log normal PDF.

        If ``cutoff`` is set, this returns the truncated PDF:

            pdf_trunc(x) = pdf(x) / P(X >= cutoff)   for x >= cutoff
                           0                          otherwise

        Parameters
        ----------
        x_min
            Lower bound factor relative to ``exp(mu)`` for the default grid.
        x_max
            Upper bound factor relative to ``exp(mu)`` for the default grid.
        n_samples
            Number of points used for the x grid.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            ``x`` with units and ``pdf`` as a unitless NumPy array.
        """
        x = self._generate_default_x(x_min=x_min, x_max=x_max, n_samples=n_samples).to(
            self._units
        )

        x_values = x.magnitude
        mu = float(self._mean.magnitude)
        sigma = float(self._standard_deviation.magnitude)

        pdf = lognorm.pdf(x_values, s=sigma, scale=np.exp(mu))

        if self.cutoff is not None:
            cutoff_value = self.cutoff.to(self._units).magnitude
            survival = 1.0 - lognorm.cdf(cutoff_value, s=sigma, scale=np.exp(mu))
            survival = float(np.clip(survival, 1e-15, 1.0))
            pdf = np.where(x_values >= cutoff_value, pdf / survival, 0.0)

        return x, pdf

    def __repr__(self) -> str:
        if self.cutoff is None:
            return f"LogNormal({self.mean:.3f~P}, {self.standard_deviation:.3f~P})"
        return f"LogNormal({self.mean:.3f~P}, {self.standard_deviation:.3f~P}, cutoff={self.cutoff:.3f~P})"
