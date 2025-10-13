import warnings
from typing import Optional

import numpy as np
from TypedUnit import (
    Angle,
    AnyUnit,
    Dimensionless,
    ElectricField,
    Frequency,
    Length,
    Power,
    Velocity,
    ureg,
)

from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.simulation_settings import SimulationSettings
from FlowCyPy.utils import dataclass, config_dict, StrictDataclassMixing


class BaseBeam:
    """
    Mixin class providing unit validation for quantities used in optical sources.
    """

    def initialization(self):
        """
        Initialize beam waists based on the numerical apertures and calculate electric field amplitude at the focus.
        """
        self.frequency = PhysicalConstant.c / self.wavelength
        self.photon_energy = (PhysicalConstant.h * self.frequency).to(
            ureg.joule
        ) / ureg.particle

        # Calculate amplitude at focus
        self.amplitude = self.calculate_field_amplitude_at_focus()

    def calculate_field_amplitude_at_focus(self) -> None:
        return NotImplementedError(
            "This method should be implemneted by the derived class!"
        )

    def _validation(*args, **kwargs):
        def wrapper(function):
            return function(*args, **kwargs)

        return wrapper

    def add_rin_to_amplitude(self, amplitude: AnyUnit, bandwidth: Frequency) -> AnyUnit:
        # Convert RIN from dB/Hz to linear scale if necessary
        rin_linear = 10 ** (self.RIN / 10)

        # Compute noise standard deviation, scaled by bandwidth
        std_dev_amplitude = (
            np.sqrt(rin_linear * bandwidth.to(ureg.hertz).magnitude) * self.amplitude
        )

        # Apply Gaussian noise to the amplitude
        amplitude += (
            np.random.normal(
                loc=0,
                scale=std_dev_amplitude.to(self.amplitude.units).magnitude,
                size=len(amplitude),
            )
            * amplitude.units
        )

        return amplitude

    def get_amplitude_signal(
        self, bandwidth: Frequency, x: Length, y: Length, z: Length = 0 * ureg.meter
    ) -> np.ndarray:
        r"""
        Applies Relative Intensity Noise (RIN) to the source amplitude if enabled, accounting for detection bandwidth.

        Parameters
        ----------
        size : int
            The number of particles being simulated.
        bandwidth : Frequency
            The detection bandwidth in Hz.

        Returns
        -------
        np.ndarray
            Array of amplitudes with RIN noise applied.

        Equations
        ---------
        1. Relative Intensity Noise (RIN):
            RIN quantifies the fluctuations in the laser's intensity relative to its mean intensity.
            RIN is typically specified as a power spectral density (PSD) in units of dB/Hz:
            \[
            \text{RIN (dB/Hz)} = 10 \cdot \log_{10}\left(\frac{\text{Noise Power (per Hz)}}{\text{Mean Power}}\right)
            \]

        2. Conversion from dB/Hz to Linear Scale:
            To compute noise power, RIN must be converted from dB to a linear scale:
            \[
            \text{RIN (linear)} = 10^{\text{RIN (dB/Hz)} / 10}
            \]

        3. Total Noise Power:
            The total noise power depends on the bandwidth (\(B\)) of the detection system:
            \[
            P_{\text{noise}} = \text{RIN (linear)} \cdot B
            \]

        4. Standard Deviation of Amplitude Fluctuations:
            The noise standard deviation for amplitude is derived from the total noise power:
            \[
            \sigma_{\text{amplitude}} = \sqrt{P_{\text{noise}}} \cdot \text{Amplitude}
            \]
            Substituting \(P_{\text{noise}}\), we get:
            \[
            \sigma_{\text{amplitude}} = \sqrt{\text{RIN (linear)} \cdot B} \cdot \text{Amplitude}
            \]

        Implementation
        --------------
        - The RIN value from the source is converted to linear scale using:
            \[
            \text{RIN (linear)} = 10^{\text{source.RIN} / 10}
            \]
        - The noise standard deviation is scaled by the detection bandwidth (\(B\)) in Hz:
            \[
            \sigma_{\text{amplitude}} = \sqrt{\text{RIN (linear)} \cdot B} \cdot \text{source.amplitude}
            \]
        - Gaussian noise with mean \(0\) and standard deviation \(\sigma_{\text{amplitude}}\) is applied to the source amplitude.

        Notes
        -----
        - The bandwidth parameter (\(B\)) must be in Hz and reflects the frequency range of the detection system.
        - The function assumes that RIN is specified in dB/Hz. If RIN is already in linear scale, the conversion step can be skipped.
        """
        if SimulationSettings.assume_perfect_hydrodynamic_focusing:
            amplitudes = self.amplitude_at(x=0 * x, y=0 * y, z=0 * z).values.quantity
        else:
            amplitudes = self.amplitude_at(x=x, y=y, z=z).values.quantity

        if (
            SimulationSettings.include_source_noise
            and SimulationSettings.include_noises
        ):
            amplitudes = self.add_rin_to_amplitude(amplitudes, bandwidth=bandwidth)

        return amplitudes

    def get_particle_width(self, velocity: Velocity) -> Length:
        """
        Returns the width of the particle flow at the waist of the beam, scaled by the velocity
        of the particles.

        Parameters
        ----------
        velocity : Velocity
            The velocity of the particles in the flow (in meters per second).

        Returns
        -------
        Length
            The width of the particle flow at the waist of the beam in meters.
        """
        return self.waist_z / (2 * velocity)


@dataclass(config=config_dict)
class AstigmaticGaussianBeam(BaseBeam, StrictDataclassMixing):
    """
    Represents an astigmatic Gaussian laser beam focused by a cylindrical lens system.

    Parameters
    ----------
    optical_power : Power
        The optical power of the laser (in watts).
    wavelength : Length
        The wavelength of the laser (in meters).
    numerical_aperture_y : Optional[Dimensionless]
        The numerical aperture of the lens along the x-axis (unitless).
    waist_y : Optional[Length]
        The beam waist along the x-axis. If not provided, it will be computed as:
        waist_y = wavelength / (pi * numerical_aperture_y).
    numerical_aperture_z : Optional[Dimensionless]
        The numerical aperture of the lens along the y-axis (unitless).
    waist_z : Optional[Length]
        The beam waist along the y-axis. If not provided, it will be computed as:
        waist_z = wavelength / (pi * numerical_aperture_z).
    polarization : Optional[Angle]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float]
        The Relative Intensity Noise (RIN) of the laser, specified as a fractional value.
        Default is 0.0, representing a perfectly stable laser.

    """

    optical_power: Power
    wavelength: Length
    numerical_aperture_y: Optional[Dimensionless] = None
    numerical_aperture_z: Optional[Dimensionless] = None
    waist_y: Optional[Length] = None
    waist_z: Optional[Length] = None
    polarization: Optional[Angle] = 0 * ureg.degree
    RIN: Optional[float] = 0.0

    frequency: Frequency = None
    photon_energy: object = None
    amplitude: ElectricField = None

    def __post_init__(self):
        """
        Initialize additional parameters like beam waists, frequency, photon energy,
        and electric field amplitude at the focus.
        """
        # Check for x-axis parameters
        if (self.numerical_aperture_y is None) and (self.waist_y is None):
            raise ValueError("Either numerical_aperture_y or waist_y must be provided.")
        if (self.numerical_aperture_y is not None) and (self.waist_y is not None):
            raise ValueError(
                "Provide only one: either numerical_aperture_y or waist_y, not both."
            )

        # Check for y-axis parameters
        if (self.numerical_aperture_z is None) and (self.waist_z is None):
            raise ValueError("Either numerical_aperture_z or waist_z must be provided.")
        if (self.numerical_aperture_z is not None) and (self.waist_z is not None):
            raise ValueError(
                "Provide only one: either numerical_aperture_z or waist_z, not both."
            )

        # Compute missing values for y-axis
        if self.numerical_aperture_y is not None:
            self.waist_y = self.wavelength / (
                PhysicalConstant.pi * self.numerical_aperture_y
            )
        else:
            self.numerical_aperture_y = self.wavelength / (
                PhysicalConstant.pi * self.waist_y
            )

        # Compute missing values for z-axis
        if self.numerical_aperture_z is not None:
            self.waist_z = self.wavelength / (
                PhysicalConstant.pi * self.numerical_aperture_z
            )
        else:
            self.numerical_aperture_z = self.wavelength / (
                PhysicalConstant.pi * self.waist_z
            )

        self.initialization()

    def amplitude_at(
        self, x: Length, y: Length, z: Length = 0 * ureg.meter
    ) -> ElectricField:
        r"""
        Returns the electric field amplitude at a position (x,y) in the focal plane.

        For a Gaussian beam, the spatial distribution is:
            E(x,y) = E(0) * exp[-(x^2+y^2)/w_0^2]

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        if np.any(y > self.waist_y):
            warnings.warn(
                "Transverse distribution of particle flow exceed the waist of the source"
            )

        E0 = self.calculate_field_amplitude_at_focus()
        return E0 * np.exp(-(y**2) / (self.waist_y**2) - (z**2) / (self.waist_z**2))

    def calculate_field_amplitude_at_focus(self) -> ElectricField:
        r"""
        Calculate the electric field amplitude (E0) at the focus for an astigmatic Gaussian beam.

        The electric field amplitude at the focus is given by:

        .. math::
            E_0 = \sqrt{\frac{2 P}{\pi \epsilon_0 c w_{0x} w_{0y}}}

        where:
            - `P` is the optical power of the beam,
            - `\epsilon_0` is the permittivity of free space,
            - `c` is the speed of light,
            - `w_{0x}` is the beam waist at the focus along the x-axis,
            - `w_{0y}` is the beam waist at the focus along the y-axis.

        Returns
        -------
        ElectricField
            The electric field amplitude at the focus in volts per meter.
        """
        area = self.waist_y * self.waist_z
        E0 = np.sqrt(
            4
            * self.optical_power
            / (
                PhysicalConstant.pi
                * PhysicalConstant.epsilon_0
                * PhysicalConstant.c
                * area
            )
        )
        return E0.to(ureg.volt / ureg.meter)


@dataclass(config=config_dict)
class GaussianBeam(AstigmaticGaussianBeam):
    """
    Represents a monochromatic Gaussian laser beam focused by a standard lens.

    Parameters
    ----------
    optical_power : Power
        The optical power of the laser (in watts).
    wavelength : Length
        The wavelength of the laser (in meters).
    numerical_aperture : Optional[Dimensionless]
        The numerical aperture (NA) of the lens focusing the Gaussian beam (unitless).
    waist : Optional[Length]
        The beam waist at the focus, calculated as `waist = wavelength / (pi * numerical_aperture)` if not provided.
        Alternatively, if this is provided, the numerical aperture will be computed as `numerical_aperture = wavelength / (pi * waist)`.
    polarization : Optional[Angle]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float]
        The Relative Intensity Noise (RIN) of the laser, specified as dB/Hz. Default is -120.0 dB/Hz, representing a stable laser.
    """

    optical_power: Power
    wavelength: Length
    numerical_aperture: Optional[Dimensionless] = None
    waist: Optional[Length] = None
    polarization: Optional[Angle] = 0 * ureg.degree
    RIN: Optional[float] = -120.0

    def __post_init__(self):
        if (self.numerical_aperture is None) and (self.waist is None):
            raise ValueError("Either numerical_aperture or waist must be provided.")
        if (self.numerical_aperture is not None) and (self.waist is not None):
            raise ValueError(
                "Provide only one: either numerical_aperture or waist, not both."
            )

        if self.numerical_aperture is not None:
            self.waist = self.wavelength / (
                PhysicalConstant.pi * self.numerical_aperture
            )
        else:
            self.numerical_aperture = self.wavelength / (
                PhysicalConstant.pi * self.waist
            )

        # Use same waist for both axes
        self.waist_y = self.waist
        self.waist_z = self.waist

        # Continue with AstigmaticGaussianBeam post init logic
        super().__post_init__()
