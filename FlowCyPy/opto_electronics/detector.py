from typing import Optional

import numpy as np
from TypedUnit import (
    Angle,
    AnyUnit,
    Current,
    Frequency,
    Length,
    Responsitivity,
    ureg,
    validate_units,
)

from FlowCyPy.signal_generator import SignalGenerator
from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing


@dataclass(config=config_dict, kw_only=True, unsafe_hash=True)
class Detector(StrictDataclassMixing):
    """
    Represents a photodetector for flow cytometry simulations.

    This class simulates a photodetector that captures light scattering signals in a flow
    cytometry setup. It models the detector response by incorporating detector specific
    transformations and optional noise sources into the signal processing workflow.

    The detector supports bandwidth dependent operations such as dark current noise and
    shot noise modeling. The bandwidth can be provided explicitly to each method, or stored
    directly on the detector instance through the ``bandwidth`` attribute. If neither is
    defined, the corresponding bandwidth dependent computation is skipped.

    Parameters
    ----------
    name : str, optional
        A unique identifier for the detector. If not provided, a unique ID is generated.
    phi_angle : Angle
        The primary azimuthal angle of incidence for the detector.
    numerical_aperture : float
        The numerical aperture of the detector.
    cache_numerical_aperture : float, optional
        The numerical aperture of the caching element placed in front of the detector.
        Default is 0.
    responsivity : Current / Power, optional
        Detector responsivity in ampere per watt. Default is 1 A/W.
    dark_current : Current, optional
        Dark current in ampere. Default is 0 A.
    bandwidth : Frequency, optional
        Detector bandwidth. If ``None``, bandwidth dependent effects are not applied
        unless a bandwidth is explicitly provided to the relevant methods.
    gamma_angle : Angle, optional
        The complementary longitudinal angle of incidence. Default is 0 degree.
    sampling : int, optional
        Number of spatial sampling points used to define the detector support.
        Default is 200.
    channel : str, optional
        Signal channel associated with this detector. Default is ``"scattering"``.
    """

    phi_angle: Angle
    numerical_aperture: float

    cache_numerical_aperture: float = 0
    gamma_angle: Optional[Angle] = 0 * ureg.degree
    sampling: Optional[int] = 200
    responsivity: Optional[Responsitivity] = 1 * ureg.ampere / ureg.watt
    dark_current: Optional[Current] = 0.0 * ureg.ampere
    bandwidth: Optional[Frequency] = None
    name: Optional[str] = None
    channel: str = "scattering"

    def __post_init__(self) -> None:
        """
        Finalize detector initialization.

        If no explicit name is provided, a unique identifier derived from the object
        instance is assigned.
        """
        if self.name is None:
            self.name = str(id(self))

    def _resolve_bandwidth(
        self,
        bandwidth: Optional[Frequency],
    ) -> Optional[Frequency]:
        """
        Return the effective bandwidth to use for a computation.

        The explicitly provided bandwidth takes precedence. If it is ``None``,
        the detector's own ``bandwidth`` attribute is used. If both are ``None``,
        the computation should be skipped by the caller.

        Parameters
        ----------
        bandwidth : Frequency or None
            Bandwidth provided directly to a method.

        Returns
        -------
        Frequency or None
            Effective bandwidth to use.
        """
        if bandwidth is not None:
            return bandwidth

        return self.bandwidth

    def apply_dark_current_noise(
        self,
        signal: Current,
        bandwidth: Optional[Frequency] = None,
    ) -> Current:
        r"""
        Apply dark current noise directly to a detector current signal.

        Dark current noise is bandwidth dependent. The method first resolves the
        effective bandwidth from the method argument or from ``self.bandwidth``.
        If no bandwidth is available, the input signal is returned unchanged.

        The dark current noise standard deviation is computed as:

        .. math::

            \sigma_{\mathrm{dark}} = \sqrt{2 q I_d B}

        where:

        - :math:`q` is the elementary charge
        - :math:`I_d` is the dark current
        - :math:`B` is the bandwidth

        A Gaussian random term with mean equal to the detector dark current and
        standard deviation :math:`\sigma_{\mathrm{dark}}` is added directly to
        each sample of the signal.

        Parameters
        ----------
        signal : Current
            Input detector current signal.
        bandwidth : Frequency or None, optional
            Signal bandwidth. If ``None``, ``self.bandwidth`` is used. If both are
            undefined, dark current noise is skipped.

        Returns
        -------
        Current
            Signal with dark current noise added.
        """
        bandwidth = self._resolve_bandwidth(bandwidth)

        if bandwidth is None:
            return signal

        standard_deviation_noise = np.sqrt(
            2 * 1.602176634e-19 * ureg.coulomb * self.dark_current * bandwidth
        )

        signal_magnitude = np.asarray(signal.to("ampere").magnitude, dtype=float)

        if signal_magnitude.size == 0:
            raise ValueError("Signal array is empty.")

        noisy_signal_magnitude = signal_magnitude + np.random.normal(
            loc=self.dark_current.to("ampere").magnitude,
            scale=standard_deviation_noise.to("ampere").magnitude,
            size=signal_magnitude.shape,
        )

        return noisy_signal_magnitude * ureg.ampere

    def _get_optical_power_to_photon_factor(
        self,
        wavelength: Length,
        bandwidth: Frequency,
    ) -> AnyUnit:
        """
        Compute the conversion factor from optical power to photon count.

        This factor represents the mean number of photons collected during one
        effective sampling interval associated with the provided bandwidth.

        Parameters
        ----------
        wavelength : Length
            Optical wavelength of the incident light.
        bandwidth : Frequency
            Signal bandwidth.

        Returns
        -------
        AnyUnit
            Conversion factor in ``1 / watt``.
        """
        energy_per_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength
        sampling_interval = 1 / (bandwidth * 2)

        optical_power_to_photon_count_conversion_factor = (
            sampling_interval / energy_per_photon
        ).to("1 / watt")

        return optical_power_to_photon_count_conversion_factor
