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
from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing


@dataclass(config=config_dict, kw_only=True, unsafe_hash=True)
class Detector(StrictDataclassMixing):
    """
    Represents a photodetector for flow cytometry simulations.

    This class simulates a photodetector that captures light scattering signals in a flow
    cytometry setup. It models the detector response by incorporating detector specific
    transformations and optional noise sources into the signal processing workflow.

    The detector supports bandwidth dependent operations such as dark current noise and
    shot noise modeling. When ``bandwidth`` is not provided to these methods, the related
    bandwidth dependent computation is skipped entirely.

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

    def apply_dark_current_noise(
        self,
        signal_generator: SignalGenerator,
        bandwidth: Optional[Frequency],
    ) -> None:
        r"""
        Apply dark current noise to the detector channel.

        Dark current noise is bandwidth dependent. If ``bandwidth`` is ``None``,
        this method returns immediately and no dark current noise is applied.

        The dark current noise standard deviation is computed as:

        .. math::

            \sigma_{\mathrm{dark}} = \sqrt{2 q I_d B}

        where:

        - :math:`q` is the elementary charge
        - :math:`I_d` is the dark current
        - :math:`B` is the bandwidth

        Parameters
        ----------
        signal_generator : SignalGenerator
            Signal generator instance used to apply noise to the detector channel.
        bandwidth : Frequency or None
            Signal bandwidth. If ``None``, dark current noise is skipped.
        """
        if bandwidth is None:
            return

        standard_deviation_noise = np.sqrt(
            2 * 1.602176634e-19 * ureg.coulomb * self.dark_current * bandwidth
        )

        signal_generator.apply_gaussian_noise_to_signal(
            channel=self.name,
            mean=self.dark_current.to("ampere").magnitude,
            standard_deviation=standard_deviation_noise.to("ampere").magnitude,
        )

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

        Notes
        -----
        This method is inherently bandwidth dependent and therefore requires
        a defined bandwidth.
        """
        energy_per_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength
        sampling_interval = 1 / (bandwidth * 2)

        optical_power_to_photon_count_conversion_factor = (
            sampling_interval / energy_per_photon
        ).to("1 / watt")

        return optical_power_to_photon_count_conversion_factor

    def _get_photon_count_to_current_factor(
        self,
        wavelength: Length,
        bandwidth: Frequency,
    ) -> Current:
        """
        Compute the conversion factor from photon count to current.

        This factor converts a photon count per effective sampling interval into
        detector current using the detector responsivity.

        Parameters
        ----------
        wavelength : Length
            Optical wavelength of the incident light.
        bandwidth : Frequency
            Signal bandwidth.

        Returns
        -------
        Current
            Conversion factor relating photon count to current.

        Notes
        -----
        This method is inherently bandwidth dependent and therefore requires
        a defined bandwidth.
        """
        energy_per_photon = PhysicalConstant.h * PhysicalConstant.c / wavelength
        photon_to_power_factor = energy_per_photon * (bandwidth * 2)
        power_to_current_factor = self.responsivity

        return photon_to_power_factor * power_to_current_factor

    def _transform_optical_power_to_photon_count(
        self,
        signal_generator: SignalGenerator,
        wavelength: Length,
        bandwidth: Optional[Frequency],
    ) -> None:
        """
        Convert optical power to photon count on the detector channel.

        If ``bandwidth`` is ``None``, this method returns immediately and no
        conversion is applied.

        Parameters
        ----------
        signal_generator : SignalGenerator
            Signal generator instance used to apply the conversion.
        wavelength : Length
            Optical wavelength of the incident light.
        bandwidth : Frequency or None
            Signal bandwidth. If ``None``, the transformation is skipped.
        """
        if bandwidth is None:
            return

        optical_power_to_photon_count_conversion = (
            self._get_optical_power_to_photon_factor(
                wavelength=wavelength,
                bandwidth=bandwidth,
            )
        )

        signal_generator.multiply(
            channel=self.name,
            factor=optical_power_to_photon_count_conversion,
        )

    @validate_units
    def apply_shot_noise(
        self,
        signal_generator: SignalGenerator,
        wavelength: Length,
        bandwidth: Optional[Frequency],
    ) -> None:
        r"""
        Apply shot noise arising from photon statistics.

        Shot noise is modeled by converting optical power into an effective photon count
        over a sampling interval determined by the bandwidth, applying Poisson statistics,
        and mapping the result back through the detector chain.

        If ``bandwidth`` is ``None``, this method returns immediately and no shot noise
        is applied.

        Parameters
        ----------
        signal_generator : SignalGenerator
            Signal generator instance used to apply shot noise.
        wavelength : Length
            Optical wavelength of the incident light.
        bandwidth : Frequency or None
            Signal bandwidth. If ``None``, shot noise is skipped.

        Notes
        -----
        The conversion uses:

        .. math::

            E_{\mathrm{photon}} = \frac{h c}{\lambda}

        and an effective sampling interval of:

        .. math::

            \Delta t = \frac{1}{2 B}

        so that the mean photon count scales with both optical power and bandwidth.
        """
        if bandwidth is None:
            return

        watt_to_photon = self._get_optical_power_to_photon_factor(
            wavelength=wavelength,
            bandwidth=bandwidth,
        )

        signal_generator.apply_poisson_noise_through_conversion(
            channel=self.name,
            watt_to_photon=watt_to_photon.to("1/watt").magnitude,
        )
