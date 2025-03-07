import numpy as np
from typing import Optional
from pydantic.dataclasses import dataclass
from pydantic import field_validator

from FlowCyPy.physical_constant import PhysicalConstant
from FlowCyPy.units import Quantity, meter, joule, particle, degree, volt, AU

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

    @field_validator('waist', 'waist_x', 'waist_y', mode='plain')
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

    @field_validator('numerical_aperture', 'numerical_aperture_x', 'numerical_aperture_y', mode='plain')
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

    def amplitude_at(self, x: Quantity, y: Quantity = 0 * meter) -> Quantity:
        r"""
        Returns the electric field amplitude at a position (x,y) in the focal plane.

        For a Gaussian beam, the spatial distribution is:
            E(x,y) = E(0) * exp[-(x^2+y^2)/w_0^2]

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        r2 = x**2 + y**2
        E0 = self.calculate_field_amplitude_at_focus()
        return E0 * np.exp(-r2 / self.waist**2)


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
    numerical_aperture_x : Optional[Quantity]
        The numerical aperture of the lens along the x-axis (unitless).
    waist_x : Optional[Quantity]
        The beam waist along the x-axis. If not provided, it will be computed as:
        waist_x = wavelength / (pi * numerical_aperture_x).
    numerical_aperture_y : Optional[Quantity]
        The numerical aperture of the lens along the y-axis (unitless).
    waist_y : Optional[Quantity]
        The beam waist along the y-axis. If not provided, it will be computed as:
        waist_y = wavelength / (pi * numerical_aperture_y).
    polarization : Optional[Quantity]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float]
        The Relative Intensity Noise (RIN) of the laser, specified as a fractional value.
        Default is 0.0, representing a perfectly stable laser.

    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture_x: Optional[Quantity] = None
    waist_x: Optional[Quantity] = None
    numerical_aperture_y: Optional[Quantity] = None
    waist_y: Optional[Quantity] = None
    polarization: Optional[Quantity] = 0 * degree
    RIN: Optional[float] = 0.0

    def __post_init__(self):
        """
        Initialize additional parameters like beam waists, frequency, photon energy,
        and electric field amplitude at the focus.
        """
        # Check for x-axis parameters
        if (self.numerical_aperture_x is None) and (self.waist_x is None):
            raise ValueError("Either numerical_aperture_x or waist_x must be provided.")
        if (self.numerical_aperture_x is not None) and (self.waist_x is not None):
            raise ValueError("Provide only one: either numerical_aperture_x or waist_x, not both.")

        # Check for y-axis parameters
        if (self.numerical_aperture_y is None) and (self.waist_y is None):
            raise ValueError("Either numerical_aperture_y or waist_y must be provided.")
        if (self.numerical_aperture_y is not None) and (self.waist_y is not None):
            raise ValueError("Provide only one: either numerical_aperture_y or waist_y, not both.")

        # Compute missing values for x-axis
        if self.numerical_aperture_x is not None:
            self.waist_x = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_x)
        else:
            self.numerical_aperture_x = self.wavelength / (PhysicalConstant.pi * self.waist_x)

        # Compute missing values for y-axis
        if self.numerical_aperture_y is not None:
            self.waist_y = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_y)
        else:
            self.numerical_aperture_y = self.wavelength / (PhysicalConstant.pi * self.waist_y)

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
        area = self.waist_x * self.waist_y
        E0 = np.sqrt(4 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * area))
        return E0.to(volt / meter)

    def amplitude_at(self, x: Quantity, y: Quantity) -> Quantity:
        r"""
        Returns the electric field amplitude at position (x,y) in the focal plane.

        For an astigmatic Gaussian beam, the distribution is:
            E(x,y) = E(0,0) * exp[-(x^2/w_{0x}^2) - (y^2/w_{0y}^2)]

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        E0 = self.calculate_field_amplitude_at_focus()
        return E0 * np.exp(-x**2 / self.waist_x**2 - y**2 / self.waist_y**2)


@dataclass(config=config_dict)
class FlatTop(BaseBeam):
    """
    Represents a flat-top laser source focused by an optical system.

    Parameters
    ----------
    optical_power : Quantity
        The optical power of the laser (in watts).
    wavelength : Quantity
        The wavelength of the laser (in meters).
    numerical_aperture : Optional[Quantity]
        The numerical aperture of the focusing system (unitless).
    flat_top_radius : Optional[Quantity]
        The radius of the flat-top beam at the focus. If not provided,
        it will be computed as: flat_top_radius = wavelength / (pi * numerical_aperture).
        Alternatively, if provided, the numerical aperture will be computed as:
        numerical_aperture = wavelength / (pi * flat_top_radius).
    polarization : Optional[Quantity]
        The polarization of the laser source in degrees (default is 0 degrees).
    RIN : Optional[float]
        The Relative Intensity Noise (RIN) of the laser. Default is 0.0, representing a perfectly stable laser.

    Attributes
    ----------
    flat_top_radius : Quantity
        The beam radius at the focus.
    numerical_aperture : Quantity
        The numerical aperture of the focusing system.
    amplitude : Quantity
        The electric field amplitude at the focus, derived from the optical power and flat-top beam area.
    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture: Optional[Quantity] = None
    flat_top_radius: Optional[Quantity] = None
    polarization: Optional[Quantity] = 0 * degree
    RIN: Optional[float] = 0.0

    def __post_init__(self):
        """
        Initialize additional parameters like flat-top radius and derived properties.
        The user must provide exactly one of: numerical_aperture or flat_top_radius.
        """
        if (self.numerical_aperture is None) and (self.flat_top_radius is None):
            raise ValueError("Either numerical_aperture or flat_top_radius must be provided.")
        if (self.numerical_aperture is not None) and (self.flat_top_radius is not None):
            raise ValueError("Provide only one: either numerical_aperture or flat_top_radius, not both.")

        if self.numerical_aperture is not None:
            self.flat_top_radius = self.wavelength / (PhysicalConstant.pi * self.numerical_aperture)
        else:
            self.numerical_aperture = self.wavelength / (PhysicalConstant.pi * self.flat_top_radius)

        self.initialization()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        r"""
        Calculate the electric field amplitude (E0) at the focus for a flat-top beam.

        The electric field amplitude at the focus is given by:

        .. math::
            E_0 = \sqrt{\frac{2 P}{\pi \epsilon_0 c R^2}}

        where:
            - `P` is the optical power of the beam,
            - `\epsilon_0` is the permittivity of free space,
            - `c` is the speed of light,
            - `R` is the flat-top beam radius at the focus.

        Returns
        -------
        Quantity
            The electric field amplitude at the focus in volts per meter.
        """
        # Compute the beam area
        beam_area = PhysicalConstant.pi * self.flat_top_radius**2

        E0 = np.sqrt(2 * self.optical_power / (PhysicalConstant.epsilon_0 * PhysicalConstant.c * beam_area))
        return E0.to(volt / meter)

    def amplitude_at(self, x: Quantity, y: Quantity = 0 * meter) -> Quantity:
        """
        Returns the electric field amplitude at a position (x,y) in the focal plane.
        For a flat-top beam, the amplitude is constant (E0) within the beam radius and zero outside.
        Supports x and y as scalars or NumPy arrays.
        """
        if not isinstance(x, np.ndarray):
            x = np.atleast_1d(x.magnitude) * x.units

        if not isinstance(y, np.ndarray):
            y = np.atleast_1d(y.magnitude) * y.units

        r = np.sqrt(x**2 + y**2)
        E0 = self.calculate_field_amplitude_at_focus()
        # Create an output array with the same shape as r, filled with zeros
        amplitude = np.zeros_like(r) * E0
        # Set amplitude to E0 where r is within the flat_top_radius.
        mask = r <= self.flat_top_radius
        amplitude[mask] = E0
        return amplitude