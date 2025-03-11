import numpy as np
from typing import Optional
from pydantic.dataclasses import dataclass
from pydantic import field_validator
import warnings

from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy import units
from FlowCyPy.units import Quantity, meter, joule, particle, degree, volt, AU
from FlowCyPy.noises import NoiseSetting

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


class BaseBeam():
    """
    Mixin class providing unit validation for quantities used in optical sources.
    """

    def initialization(self):
        """
        Initialize beam waists based on the numerical apertures and calculate electric field amplitude at the focus.
        """
        self.frequency = PhysicalConstant.c / self.wavelength
        self.photon_energy = (PhysicalConstant.h * self.frequency).to(joule) / particle

        # Calculate amplitude at focus
        self.amplitude = self.calculate_field_amplitude_at_focus()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        return NotImplementedError('This method should be implemneted by the derived class!')

    @field_validator('wavelength', mode='plain')
    def validate_length(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with distance units [<prefix>meter].")

        if not value.check('meter'):
            raise ValueError(f"{field} must be a Quantity with distance units [<prefix>meter], but got {value.units}.")

        return value

    @field_validator('waist', 'waist_y', 'waist_z', mode='plain')
    def validate_waist(cls, value, field):
        if value is None:
            return value
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with distance units [<prefix>meter].")

        if not value.check('meter'):
            raise ValueError(f"{field} must be a Quantity with distance units [<prefix>meter], but got {value.units}.")

        return value

    @field_validator('polarization', mode='plain')
    def validate_polarization(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with angle units [<prefix>degree or <prefix>radian].")

        if not value.check('degree'):
            raise ValueError(f"{field} must be a Quantity with angle units [<prefix>degree or <prefix>radian], but got {value.units}.")

        return value

    @field_validator('optical_power', mode='plain')
    def validate_optical_power(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with power units [<prefix>watt].")

        if not value.check('watt'):
            raise ValueError(f"{field} must be a Quantity with power units [<prefix>watt], but got {value.units}.")

        return value

    @field_validator('numerical_aperture', 'numerical_aperture_y', 'numerical_aperture_z', mode='plain')
    def validate_numerical_apertures(cls, value, field):
        if value is None:
            return value
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with arbitrary units [AU].")

        if not value.check(AU):
            raise ValueError(f"{field} must be a Quantity with arbitrary units [AU], but got {value.units}.")

        if value.magnitude < 0 or value.magnitude > 1:
            raise ValueError(f"{field} must be between 0 and 1, but got {value.magnitude}")
        return value

    def add_rin_to_amplitude(self, amplitude: Quantity, bandwidth: Quantity) -> Quantity:
        # Convert RIN from dB/Hz to linear scale if necessary
        rin_linear = 10**(self.RIN / 10)

        # Compute noise standard deviation, scaled by bandwidth
        std_dev_amplitude = np.sqrt(rin_linear * bandwidth.to(units.hertz).magnitude) * self.amplitude

        # Apply Gaussian noise to the amplitude
        amplitude += np.random.normal(
            loc=0,
            scale=std_dev_amplitude.to(self.amplitude.units).magnitude,
            size=len(amplitude)
        ) * amplitude.units

        return amplitude

    def get_amplitude_signal(self, size: int, bandwidth: float, x: Quantity, y: Quantity, z: Quantity = 0 * units.meter) -> np.ndarray:
        r"""
        Applies Relative Intensity Noise (RIN) to the source amplitude if enabled, accounting for detection bandwidth.

        Parameters
        ----------
        size : int
            The number of particles being simulated.
        bandwidth : float
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
        amplitudes = self.amplitude_at(x=x, y=y, z=z).values.quantity

        if NoiseSetting.include_RIN_noise and NoiseSetting.include_noises:
            amplitudes = self.add_rin_to_amplitude(amplitudes, bandwidth=bandwidth)

        return amplitudes


@dataclass(config=config_dict)
class GaussianBeam(BaseBeam):
    """
    Represents a monochromatic Gaussian laser beam focused by a standard lens.

    Parameters
    ----------
    optical_power : Quantity
        The optical power of the laser (in watts).
    wavelength : Quantity
        The wavelength of the laser (in meters).
    numerical_aperture : Optional[Quantity]
        The numerical aperture (NA) of the lens focusing the Gaussian beam (unitless).
    waist : Optional[Quantity]
        The beam waist at the focus, calculated as `waist = wavelength / (pi * numerical_aperture)` if not provided.
        Alternatively, if this is provided, the numerical aperture will be computed as `numerical_aperture = wavelength / (pi * waist)`.
    polarization : Optional[Quantity]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float]
        The Relative Intensity Noise (RIN) of the laser, specified as dB/Hz. Default is -120.0 dB/Hz, representing a stable laser.
    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture: Optional[Quantity] = None
    waist: Optional[Quantity] = None
    polarization: Optional[Quantity] = 0 * degree
    RIN: Optional[float] = -120.0

    def __post_init__(self):
        """
        Ensure that either numerical_aperture or waist is provided (but not both),
        then compute the missing parameter before initializing other attributes.
        """
        if (self.numerical_aperture is None) and (self.waist is None):
            raise ValueError("Either numerical_aperture or waist must be provided.")
        if (self.numerical_aperture is not None) and (self.waist is not None):
            raise ValueError("Provide only one: either numerical_aperture or waist, not both.")

        if self.numerical_aperture is not None:
            self.waist = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture)
        else:
            self.numerical_aperture = self.wavelength / (PhysicalConstant.pi * self.waist)

        self.initialization()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        r"""
        Calculate the electric field amplitude (E0) at the focus for a Gaussian beam.

        The electric field amplitude at the focus is given by:

        .. math::
            E_0 = \sqrt{\frac{4 P}{\pi \epsilon_0 c w_0^2}}

        where:
            - `P` is the optical power of the beam,
            - `\epsilon_0` is the permittivity of free space,
            - `c` is the speed of light,
            - `w_0` is the beam waist at the focus.

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        # Ensure that waist has been computed
        area = self.waist ** 2
        E0 = np.sqrt(4 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * area))
        return E0.to(volt / meter)

    def amplitude_at(self, x: Quantity, y: Quantity, z: Quantity = 0 * units.meter) -> Quantity:
        r"""
        Returns the electric field amplitude at a position (x,y) in the focal plane.

        For a Gaussian beam, the spatial distribution is:
            E(x,y) = E(0) * exp[-(x^2+y^2)/w_0^2]

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        if np.any(y > self.waist):
            warnings.warn('Transverse distribution of particle flow exceed the waist of the source')

        E0 = self.calculate_field_amplitude_at_focus()
        return E0 * np.exp(-y ** 2 / self.waist ** 2 - z ** 2 / self.waist ** 2)

    def get_particle_width(self, velocity: Quantity) -> Quantity:
        return self.waist / (2 * velocity)



@dataclass(config=config_dict)
class AstigmaticGaussianBeam(BaseBeam):
    """
    Represents an astigmatic Gaussian laser beam focused by a cylindrical lens system.

    Parameters
    ----------
    optical_power : Quantity
        The optical power of the laser (in watts).
    wavelength : Quantity
        The wavelength of the laser (in meters).
    numerical_aperture_y : Optional[Quantity]
        The numerical aperture of the lens along the x-axis (unitless).
    waist_y : Optional[Quantity]
        The beam waist along the x-axis. If not provided, it will be computed as:
        waist_y = wavelength / (pi * numerical_aperture_y).
    numerical_aperture_z : Optional[Quantity]
        The numerical aperture of the lens along the y-axis (unitless).
    waist_z : Optional[Quantity]
        The beam waist along the y-axis. If not provided, it will be computed as:
        waist_z = wavelength / (pi * numerical_aperture_z).
    polarization : Optional[Quantity]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float]
        The Relative Intensity Noise (RIN) of the laser, specified as a fractional value.
        Default is 0.0, representing a perfectly stable laser.

    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture_y: Optional[Quantity] = None
    waist_y: Optional[Quantity] = None
    numerical_aperture_z: Optional[Quantity] = None
    waist_z: Optional[Quantity] = None
    polarization: Optional[Quantity] = 0 * degree
    RIN: Optional[float] = 0.0

    def __post_init__(self):
        """
        Initialize additional parameters like beam waists, frequency, photon energy,
        and electric field amplitude at the focus.
        """
        # Check for x-axis parameters
        if (self.numerical_aperture_y is None) and (self.waist_y is None):
            raise ValueError("Either numerical_aperture_y or waist_y must be provided.")
        if (self.numerical_aperture_y is not None) and (self.waist_y is not None):
            raise ValueError("Provide only one: either numerical_aperture_y or waist_y, not both.")

        # Check for y-axis parameters
        if (self.numerical_aperture_z is None) and (self.waist_z is None):
            raise ValueError("Either numerical_aperture_z or waist_z must be provided.")
        if (self.numerical_aperture_z is not None) and (self.waist_z is not None):
            raise ValueError("Provide only one: either numerical_aperture_z or waist_z, not both.")

        # Compute missing values for y-axis
        if self.numerical_aperture_y is not None:
            self.waist_y = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_y)
        else:
            self.numerical_aperture_y = self.wavelength / (PhysicalConstant.pi * self.waist_y)

        # Compute missing values for z-axis
        if self.numerical_aperture_z is not None:
            self.waist_z = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_z)
        else:
            self.numerical_aperture_z = self.wavelength / (PhysicalConstant.pi * self.waist_z)

        self.initialization()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
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
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        area = self.waist_y * self.waist_z
        E0 = np.sqrt(4 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * area))
        return E0.to(volt / meter)

    def amplitude_at(self, x: Quantity, y: Quantity, z: Quantity = 0 * units.meter) -> Quantity:
        r"""
        Returns the electric field amplitude at position (x,y) in the focal plane.

        For an astigmatic Gaussian beam, the distribution is:
            E(x,y) = E(0,0) * exp[-(x^2/w_{0x}^2) - (y^2/w_{0y}^2)]

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        if np.any(y > self.waist_z):
            warnings.warn('Transverse distribution of particle flow exceed the waist of the source')

        E0 = self.calculate_field_amplitude_at_focus()
        return E0 * np.exp(- y ** 2 / self.waist_y ** 2 - z ** 2 / self.waist_z ** 2)

    def get_particle_width(self, velocity: Quantity) -> Quantity:
        return self.waist_z / (2 * velocity)
