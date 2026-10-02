from FlowCyPy.opto_electronics.detector import Detector
from FlowCyPy.units import ureg

_PMT_DEFAULT_RESPONSIVITY = ureg.Quantity(0.2, ureg.ampere / ureg.watt)
_PMT_DEFAULT_DARK_CURRENT = ureg.Quantity(1e-9, ureg.ampere)
_PMT_DEFAULT_CURRENT_NOISE_DENSITY = ureg.Quantity(0.0, ureg.ampere / ureg.hertz**0.5)
_PIN_DEFAULT_RESPONSIVITY = ureg.Quantity(0.5, ureg.ampere / ureg.watt)
_PIN_DEFAULT_DARK_CURRENT = ureg.Quantity(1e-8, ureg.ampere)
_PIN_DEFAULT_CURRENT_NOISE_DENSITY = ureg.Quantity(0.0, ureg.ampere / ureg.hertz**0.5)
_APD_DEFAULT_RESPONSIVITY = ureg.Quantity(0.7, ureg.ampere / ureg.watt)
_APD_DEFAULT_DARK_CURRENT = ureg.Quantity(5e-9, ureg.ampere)
_APD_DEFAULT_CURRENT_NOISE_DENSITY = ureg.Quantity(0.0, ureg.ampere / ureg.hertz**0.5)


class PMT:
    """Factory namespace for a photomultiplier-tube detector preset."""

    def __new__(
        cls,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: ureg.Quantity,
        responsivity: ureg.Quantity = _PMT_DEFAULT_RESPONSIVITY,
        dark_current: ureg.Quantity = _PMT_DEFAULT_DARK_CURRENT,
        current_noise_density: ureg.Quantity = _PMT_DEFAULT_CURRENT_NOISE_DENSITY,
        **kwargs,
    ):
        """Create a :class:`Detector` configured with PMT-like defaults."""
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            current_noise_density=current_noise_density,
            **kwargs,
        )


# Predefined PIN Photodiode Detector
class PIN:
    """Factory namespace for a PIN photodiode detector preset."""

    def __new__(
        cls,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: ureg.Quantity,
        responsivity=_PIN_DEFAULT_RESPONSIVITY,  # Higher responsivity for PIN
        dark_current=_PIN_DEFAULT_DARK_CURRENT,  # Slightly higher dark current
        current_noise_density=_PIN_DEFAULT_CURRENT_NOISE_DENSITY,
        **kwargs,
    ):
        """Create a :class:`Detector` configured with PIN-photodiode defaults."""
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            current_noise_density=current_noise_density,
            **kwargs,
        )


# Predefined Avalanche Photodiode (APD) Detector
class APD:
    """Factory namespace for an avalanche photodiode detector preset."""

    def __new__(
        cls,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: ureg.Quantity,
        responsivity=_APD_DEFAULT_RESPONSIVITY,  # APDs often have high responsivity
        dark_current=_APD_DEFAULT_DARK_CURRENT,
        current_noise_density=_APD_DEFAULT_CURRENT_NOISE_DENSITY,
        **kwargs,
    ):
        """Create a :class:`Detector` configured with APD-like defaults."""
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            current_noise_density=current_noise_density,
            **kwargs,
        )
