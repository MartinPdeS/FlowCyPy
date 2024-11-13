
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


class QuantityValidationMixin:
    """
    Mixin class providing unit validation for quantities used in optical sources.
    """

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
class Source(PropertiesReport, QuantityValidationMixin):
    """
    Represents a monochromatic Gaussian laser source.

    Parameters
    ----------
    optical_power : Quantity
        Optical power of the laser (in watts).
    wavelength : Quantity
        Wavelength of the laser (in meters).
    numerical_aperture: Quantity
        Numerical aperture of the laser (unitless).
    polarization : Optional[Quantity]
        Polarization of the laser source in degrees (default is 0 degrees).
    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture: Quantity
    polarization: Optional[Quantity] = 0 * degree

    def __post_init__(self):
        """
        Initialize additional parameters like beam waist, frequency, photon energy,
        and electric field amplitude at the focus.
        """
        self.waist = 2 * self.wavelength / (PhysicalConstant.pi * self.numerical_aperture)
        self.frequency = PhysicalConstant.c / self.wavelength
        self.photon_energy = (PhysicalConstant.h * self.frequency).to(joule) / particle
        self.amplitude = self.calculate_field_amplitude_at_focus()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        """
        Calculate the electric field amplitude at the focus for a Gaussian beam.

        Returns
        -------
        Quantity
            Electric field amplitude at the focus in volts per meter.
        """
        E0 = np.sqrt(2 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * self.waist**2))
        return E0.to(volt / meter)


@dataclass(config=config_dict)
class AstigmaticGaussianBeam(PropertiesReport, QuantityValidationMixin):
    """
    Represents an astigmatic Gaussian laser beam passing through a cylindrical lens.

    Parameters
    ----------
    optical_power : Quantity
        Optical power of the laser (in watts).
    wavelength : Quantity
        Wavelength of the laser (in meters).
    numerical_aperture_x : Quantity
        Numerical aperture of the laser along the x-axis (unitless).
    numerical_aperture_y : Quantity
        Numerical aperture of the laser along the y-axis (unitless).
    """
    optical_power: Quantity
    wavelength: Quantity
    numerical_aperture_x: Quantity
    numerical_aperture_y: Quantity

    def __post_init__(self):
        """
        Initialize beam waists based on the numerical apertures and calculate electric field amplitude at the focus.
        """
        # Calculate waists based on numerical apertures
        self.w_0x = (self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_x))
        self.w_0y = (self.wavelength / (PhysicalConstant.pi * self.numerical_aperture_y))

        # Calculate amplitude at focus
        self.amplitude = self.calculate_field_amplitude_at_focus()

    def calculate_field_amplitude_at_focus(self) -> Quantity:
        """
        Calculate the electric field amplitude at the focus for an astigmatic Gaussian beam.

        Returns
        -------
        Quantity
            Electric field amplitude at the focus in volts per meter.
        """
        E0 = np.sqrt(2 * self.optical_power / (PhysicalConstant.pi * PhysicalConstant.epsilon_0 * PhysicalConstant.c * self.w_0x * self.w_0y))

        return E0.to(volt / meter)
