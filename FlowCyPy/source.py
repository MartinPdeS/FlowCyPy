
from typing import Optional
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from FlowCyPy.units import meter, joule, particle, degree, volt, AU
from PyMieSim.units import Quantity
from FlowCyPy.utils import PropertiesReport
from FlowCyPy.physical_constant import PhysicalConstant
import numpy as np


config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


class BaseBeam(PropertiesReport):
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
    def validate_wavelength(cls, value, field):
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

    @field_validator('numerical_aperture', 'numerical_aperture_x', 'numerical_aperture_y', mode='plain')
    def validate_numerical_apertures(cls, value, field):
        if not isinstance(value, Quantity):
            raise ValueError(f"{value} must be a Quantity with arbitrary units [AU].")

        if not value.check(AU):
            raise ValueError(f"{field} must be a Quantity with arbitrary units [AU], but got {value.units}.")

        if value.magnitude < 0 or value.magnitude > 1:
            raise ValueError(f"{field} must be between 0 and 1, but got {value.magnitude}")
        return value


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
    numerical_aperture : Quantity
        The numerical aperture (NA) of the lens focusing the Gaussian beam (unitless).
    polarization : Optional[Quantity]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float], optional
        The Relative Intensity Noise (RIN) of the laser, specified as dB/Hz. Default is -120.0 dB/Hz, representing a pretty stable laser.

    Attributes
    ----------
    waist : Quantity
        The beam waist at the focus, calculated as `waist = wavelength / (pi * numerical_aperture)`.
    frequency : Quantity
        The frequency of the laser, calculated as `frequency = c / wavelength`.
    photon_energy : Quantity
        The energy of a single photon, calculated as `photon_energy = h * frequency`.
    amplitude : Quantity
        The electric field amplitude at the focus, derived from optical power, waist, and fundamental constants.

    Notes
    -----
    RIN Interpretation:
        - The Relative Intensity Noise (RIN) represents fluctuations in the laser's intensity relative to its mean optical power.
        - For a Gaussian beam, the instantaneous intensity at any given time can be modeled as: I(t) = <I> * (1 + ΔI)

    where:
        - `<I>` is the mean intensity derived from the optical power.
        - `ΔI` is the noise component, modeled as a Gaussian random variable with:
            - Mean = 0 (fluctuations are around the mean intensity).
            - Variance = RIN * <I>².

    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture: Quantity
    polarization: Optional[Quantity] = 0 * degree
    RIN: Optional[float] = -120.0

    def __post_init__(self):
        """
        Initialize additional parameters like beam waist, frequency, photon energy,
        and electric field amplitude at the focus.
        """
        self.initialization()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        r"""
        Calculate the electric field amplitude (E0) at the focus for a Gaussian beam.

        The electric field amplitude at the focus is given by:

        .. math::
            E_0 = \sqrt{\frac{2 P}{\pi \epsilon_0 c w_0^2}}

        where:
            - `P` is the optical power of the beam,
            - `epsilon_0` is the permittivity of free space,
            - `c` is the speed of light,
            - `w_0` is the beam waist at the focus.

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        self.waist = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture)

        E0 = np.sqrt(2 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * self.waist**2))

        return E0.to(volt / meter)


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
    numerical_aperture_x : Quantity
        The numerical aperture of the lens along the x-axis (unitless).
    numerical_aperture_y : Quantity
        The numerical aperture of the lens along the y-axis (unitless).
    polarization : Optional[Quantity]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float], optional
        The Relative Intensity Noise (RIN) of the laser, specified as a fractional value (e.g., 0.01 for 1% RIN).
        Default is 0.0, representing a perfectly stable laser.

    Attributes
    ----------
    waist_x : Quantity
        The beam waist at the focus along the x-axis, calculated as `waist_x = wavelength / (pi * numerical_aperture_x)`.
    waist_y : Quantity
        The beam waist at the focus along the y-axis, calculated as `waist_y = wavelength / (pi * numerical_aperture_y)`.
    amplitude : Quantity
        The electric field amplitude at the focus, derived from optical power, waist_x, waist_y, and fundamental constants.

    Notes
    -----
    RIN Interpretation:
        - The Relative Intensity Noise (RIN) represents fluctuations in the laser's intensity relative to its mean optical power.
        - For a Gaussian beam, the instantaneous intensity at any given time can be modeled as:

        I(t) = <I> * (1 + ΔI)

    where:
        - `<I>` is the mean intensity derived from the optical power.
        - `ΔI` is the noise component, modeled as a Gaussian random variable with:
            - Mean = 0 (fluctuations are around the mean intensity).
            - Variance = RIN * <I>².

    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture_x: Quantity
    numerical_aperture_y: Quantity
    polarization: Optional[Quantity] = 0 * degree
    RIN: Optional[float] = 0.0

    def __post_init__(self):
        """
        Initialize additional parameters like beam waist, frequency, photon energy,
        and electric field amplitude at the focus.
        """
        self.initialization()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        """
        Calculate the electric field amplitude (E0) at the focus for an astigmatic Gaussian beam.

        The electric field amplitude at the focus is given by:

        .. math::
            E_0 = \\sqrt{\\frac{2 P}{\\pi \\epsilon_0 c w_{0x} w_{0y}}}

        where:
            - `P` is the optical power of the beam,
            - `epsilon_0` is the permittivity of free space,
            - `c` is the speed of light,
            - `w_{0x}` is the beam waist at the focus along the x-axis,
            - `w_{0y}` is the beam waist at the focus along the y-axis.

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        # Calculate waists based on numerical apertures
        self.waist_x = (self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_x))
        self.waist_y = (self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_y))

        E0 = np.sqrt(2 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * self.waist_x * self.waist_y))

        return E0.to(volt / meter)
