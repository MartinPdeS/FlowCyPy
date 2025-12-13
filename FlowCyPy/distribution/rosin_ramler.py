from typing import Tuple, Optional

import numpy as np
from pydantic.dataclasses import dataclass
from TypedUnit import AnyUnit

from FlowCyPy.distribution.base_class import Base
from FlowCyPy.utils import config_dict


@dataclass(config=config_dict)
class RosinRammler(Base):
    r"""
    Rosin Rammler particle size distribution.

    This class implements the Rosin Rammler distribution, which is mathematically
    equivalent to a Weibull distribution parameterized by a scale parameter
    ``d`` (here ``characteristic_value``) and a shape parameter ``k``
    (here ``spread``).

    The cumulative distribution function is

    .. math::
        F(x) = 1 - \exp\!\left(-\left(\frac{x}{d}\right)^k\right),

    where ``x`` is the sampled property (typically a diameter), ``d`` is the
    characteristic property (scale) and ``k`` controls the distribution width.

    Hard cutoff and truncation
    --------------------------
    When ``cutoff`` is provided, sampling is performed from the truncated
    distribution conditional on

    .. math::
        X \ge x_{\mathrm{cut}}.

    Operationally, this is not rejection sampling.
    Instead, truncation is implemented by remapping uniform random numbers
    from ``[0, 1)`` to the CDF interval ``[F(cutoff), 1)`` and applying the
    standard inverse CDF transform.

    This provides an efficient way to emulate an idealized size selection step.
    If you interpret the cutoff as a physical removal of particles below the
    cutoff, you can use :meth:`survival_fraction_above` to compute the
    concentration multiplier consistent with the same distribution.

    Parameters
    ----------
    characteristic_value
        Scale parameter ``d`` with length units.
        In many applications this is a characteristic diameter.

    spread
        Shape parameter ``k``.
        Must be strictly positive.

    cutoff
        Optional hard minimum value with the same units as ``characteristic_value``.
        If provided, generated samples satisfy ``x >= cutoff`` by construction.

    Notes
    -----
    The Rosin Rammler model is often used for particulate materials.
    In biological nanoparticle contexts it can be a convenient phenomenological
    model, but you should verify that the tail behavior is realistic for the
    application, especially when applying strong cutoffs.
    """

    characteristic_value: AnyUnit
    spread: float
    cutoff: Optional[AnyUnit] = None

    @property
    def _units(self) -> AnyUnit:
        """
        Units used internally for computations.

        Returns
        -------
        AnyUnit
            Units of ``characteristic_value``.
        """
        return self.characteristic_value.units

    def cdf(self, x: AnyUnit) -> float:
        r"""
        Evaluate the cumulative distribution function at ``x``.

        Parameters
        ----------
        x
            Quantity with the same dimensionality as ``characteristic_value``.

        Returns
        -------
        float
            CDF value in the interval ``[0, 1]``.

        Raises
        ------
        ValueError
            If ``spread`` is not strictly positive.
        """
        k = float(self.spread)
        if k <= 0.0:
            raise ValueError("spread must be positive.")

        scale_value = self.characteristic_value.to(self._units).magnitude
        x_value = x.to(self._units).magnitude

        if x_value <= 0.0:
            return 0.0

        value = 1.0 - np.exp(-((x_value / scale_value) ** k))
        return float(np.clip(value, 0.0, 1.0))

    def survival_fraction_above(self, cutoff: AnyUnit) -> float:
        r"""
        Compute the survival fraction above a cutoff, ``P(X >= cutoff)``.

        This quantity is the natural concentration multiplier if you interpret
        the cutoff as physically removing all particles smaller than ``cutoff``
        from an otherwise unchanged distribution.

        For the Rosin Rammler distribution,

        .. math::
            P(X \ge x_{\mathrm{cut}}) = \exp\!\left(-\left(\frac{x_{\mathrm{cut}}}{d}\right)^k\right).

        Parameters
        ----------
        cutoff
            Hard minimum value with length units.

        Returns
        -------
        float
            Survival fraction in ``[0, 1]``.

        Raises
        ------
        ValueError
            If ``spread`` is not strictly positive.
        """
        k = float(self.spread)
        if k <= 0.0:
            raise ValueError("spread must be positive.")

        scale_value = self.characteristic_value.to(self._units).magnitude
        cutoff_value = cutoff.to(self._units).magnitude

        if cutoff_value <= 0.0:
            return 1.0

        survival = np.exp(-((cutoff_value / scale_value) ** k))
        return float(np.clip(survival, 0.0, 1.0))

    def apply_cutoff(
        self,
        cutoff: AnyUnit,
        reduce_concentration_consistently: bool = True,
    ) -> Tuple["RosinRammler", float]:
        r"""
        Return a truncated Rosin Rammler distribution and an optional
        concentration multiplier.

        This is a convenience method that supports two distinct operations.

        1. Truncating the distribution for sampling
           The returned distribution samples from the conditional law
           ``X | X >= cutoff``.

        2. Optionally updating population concentration consistently
           If you interpret the cutoff as a physical removal of particles,
           the appropriate concentration multiplier is the survival fraction
           ``P(X >= cutoff)`` computed from the same distribution.

        Parameters
        ----------
        cutoff
            Hard minimum value used to define the truncated sampling distribution.

        reduce_concentration_consistently
            If True, return the survival fraction ``P(X >= cutoff)`` as the
            concentration multiplier.
            If False, return ``1.0`` as the multiplier.

        Returns
        -------
        truncated_distribution, concentration_multiplier
            ``truncated_distribution`` is a new :class:`RosinRammler` instance
            with the same scale and shape but with ``cutoff`` set.

            ``concentration_multiplier`` is:
                - ``P(X >= cutoff)`` if ``reduce_concentration_consistently`` is True
                - ``1.0`` otherwise

        Examples
        --------
        Sample truncation only:

        .. code-block:: python

            rr_truncated, _ = rr.apply_cutoff(30 * ureg.nanometer, reduce_concentration_consistently=False)

        Truncation plus concentration update:

        .. code-block:: python

            rr_truncated, multiplier = rr.apply_cutoff(30 * ureg.nanometer, reduce_concentration_consistently=True)
            population.particle_count *= multiplier
            population.diameter = rr_truncated
        """
        truncated_distribution = RosinRammler(
            characteristic_value=self.characteristic_value,
            spread=self.spread,
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

        Sampling is performed via the inverse CDF (quantile) transform.

        Without cutoff
        --------------
        Draw ``u ~ Uniform(0, 1)`` and apply

        .. math::
            x = d \left[-\ln(1-u)\right]^{1/k}.

        With cutoff
        -----------
        Sampling from ``X | X >= cutoff`` is achieved by restricting the CDF
        to the interval ``[F(cutoff), 1)``.
        Draw ``u ~ Uniform(0, 1)``, compute

        .. math::
            p = F(cutoff) + u(1 - F(cutoff)),

        then apply the same quantile transform using ``p``.

        Parameters
        ----------
        n_samples
            Number of samples to draw.

        Returns
        -------
        AnyUnit
            Array of samples with the same units as ``characteristic_value``.

        Raises
        ------
        ValueError
            If ``spread`` is not strictly positive.
        """
        if n_samples <= 0:
            return np.array([]) * self._units

        k = float(self.spread)
        if k <= 0.0:
            raise ValueError("spread must be positive.")

        scale_value = self.characteristic_value.to(self._units).magnitude

        uniform_samples = np.random.uniform(size=int(n_samples))
        uniform_samples = np.clip(uniform_samples, 1e-12, 1.0 - 1e-12)

        if self.cutoff is None:
            probabilities = uniform_samples
        else:
            cutoff_value = self.cutoff.to(self._units).magnitude
            if cutoff_value < 0.0:
                raise ValueError("cutoff must be non negative.")

            if cutoff_value == 0.0:
                probabilities = uniform_samples
            else:
                cdf_at_cutoff = 1.0 - np.exp(-((cutoff_value / scale_value) ** k))
                cdf_at_cutoff = float(np.clip(cdf_at_cutoff, 0.0, 1.0 - 1e-15))

                probabilities = cdf_at_cutoff + uniform_samples * (1.0 - cdf_at_cutoff)
                probabilities = np.clip(probabilities, 1e-12, 1.0 - 1e-12)

        samples = scale_value * (-np.log(1.0 - probabilities)) ** (1.0 / k)

        if self.cutoff is not None:
            cutoff_value = self.cutoff.to(self._units).magnitude
            samples = np.maximum(samples, cutoff_value)

        return samples

    def _generate_default_x(
        self, x_min: float, x_max: float, n_samples: int = 100
    ) -> np.ndarray:
        """
        Generate a default x grid for plotting.

        The grid is constructed as a multiplicative range around the scale
        parameter:

            x in [x_min * d, x_max * d].

        Parameters
        ----------
        x_min
            Lower bound factor relative to ``characteristic_value``.
            Must be strictly positive.

        x_max
            Upper bound factor relative to ``characteristic_value``.
            Must be greater than ``x_min``.

        n_samples
            Number of points in the returned grid.

        Returns
        -------
        np.ndarray
            1D array of x values with length units.
        """
        if x_min <= 0:
            raise ValueError("x_min must be greater than 0.")
        if x_max <= x_min:
            raise ValueError("x_max must be greater than x_min.")

        scale_value = self.characteristic_value.to(self._units).magnitude
        x_min_value = scale_value * float(x_min)
        x_max_value = scale_value * float(x_max)

        return np.linspace(x_min_value, x_max_value, int(n_samples)) * self._units

    def get_pdf(
        self,
        x_min: float = 0.1,
        x_max: float = 2.0,
        n_samples: int = 100,
    ) -> Tuple[np.ndarray, np.ndarray]:
        r"""
        Return x values and the probability density function.

        Without cutoff, the Rosin Rammler PDF is

        .. math::
            f(x) = \frac{k}{d}\left(\frac{x}{d}\right)^{k-1}
                   \exp\!\left(-\left(\frac{x}{d}\right)^k\right).

        With cutoff, this method returns the truncated PDF for ``x >= cutoff``:

        .. math::
            f_{\mathrm{trunc}}(x) =
            \begin{cases}
                \frac{f(x)}{P(X \ge cutoff)} & x \ge cutoff, \\
                0 & x < cutoff.
            \end{cases}

        Parameters
        ----------
        x_min
            Lower bound factor relative to ``characteristic_value``.
        x_max
            Upper bound factor relative to ``characteristic_value``.
        n_samples
            Number of points used for the x grid.

        Returns
        -------
        x, pdf
            ``x`` is a 1D array with length units.
            ``pdf`` is a 1D NumPy array of density values.
        """
        x = self._generate_default_x(x_min=x_min, x_max=x_max, n_samples=n_samples).to(
            self._units
        )

        x_values = x.magnitude
        scale_value = self.characteristic_value.to(self._units).magnitude
        k = float(self.spread)

        pdf = (
            (k / scale_value)
            * (x_values / scale_value) ** (k - 1.0)
            * np.exp(-((x_values / scale_value) ** k))
        )

        if self.cutoff is not None:
            cutoff_value = self.cutoff.to(self._units).magnitude
            survival_at_cutoff = np.exp(-((cutoff_value / scale_value) ** k))
            survival_at_cutoff = float(np.clip(survival_at_cutoff, 1e-15, 1.0))
            pdf = np.where(x_values >= cutoff_value, pdf / survival_at_cutoff, 0.0)

        return x, pdf

    def __repr__(self) -> str:
        if self.cutoff is None:
            return f"RR({self.characteristic_value:.3f~P}, {self.spread:.3f})"
        return f"RR({self.characteristic_value:.3f~P}, {self.spread:.3f}, cutoff={self.cutoff:.3f~P})"
