"""Excitation lines sharing one illumination spot."""

from dataclasses import dataclass
import numpy as np
from FlowCyPy.units import ureg


@dataclass(frozen=True, kw_only=True)
class Laser:
    """Define one monochromatic excitation line.

    Parameters
    ----------
    wavelength : length quantity
        Positive vacuum wavelength.
    optical_power : power quantity
        Nonnegative incident power.
    rin : quantity in dB/Hz, optional
        Relative intensity noise spectral density. Omit for a quiet line.
    """

    wavelength: ureg.Quantity
    optical_power: ureg.Quantity
    rin: ureg.Quantity | None = None

    def __post_init__(self):
        """Validate scalar wavelength and power in physical units."""
        if self.rin is not None:
            density = np.asarray(self.rin.m_as("dB_per_Hz"))
            if density.ndim or not np.isfinite(density):
                raise ValueError("Laser rin must be a finite scalar in dB/Hz.")
        wavelength = np.asarray(self.wavelength.m_as("nm"))
        power = np.asarray(self.optical_power.m_as("W"))
        if wavelength.ndim or not np.isfinite(wavelength) or wavelength <= 0:
            raise ValueError("Laser wavelength must be a finite positive scalar.")
        if power.ndim or not np.isfinite(power) or power < 0:
            raise ValueError("Laser optical_power must be a finite nonnegative scalar.")
