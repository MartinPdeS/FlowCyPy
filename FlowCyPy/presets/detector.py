from FlowCyPy.units import ureg

from FlowCyPy.opto_electronics.detector import Detector


class PMT:
    def __new__(
        cls,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: ureg.Quantity,
        responsivity: ureg.Quantity = ureg.Quantity(0.2, ureg.ampere / ureg.watt),
        dark_current: ureg.Quantity = ureg.Quantity(1e-9, ureg.ampere),
        current_noise_density: ureg.Quantity = ureg.Quantity(
            0.0, ureg.ampere / ureg.hertz**0.5
        ),
        **kwargs,
    ):
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
    def __new__(
        cls,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: ureg.Quantity,
        responsivity=ureg.Quantity(
            0.5, ureg.ampere / ureg.watt
        ),  # Higher responsivity for PIN
        dark_current=ureg.Quantity(1e-8, ureg.ampere),  # Slightly higher dark current
        current_noise_density=ureg.Quantity(0.0, ureg.ampere / ureg.hertz**0.5),
        **kwargs,
    ):
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
    def __new__(
        cls,
        name: str,
        phi_angle: ureg.Quantity,
        numerical_aperture: ureg.Quantity,
        responsivity=ureg.Quantity(
            0.7, ureg.ampere / ureg.watt
        ),  # APDs often have high responsivity
        dark_current=ureg.Quantity(5e-9, ureg.ampere),
        current_noise_density=ureg.Quantity(0.0, ureg.ampere / ureg.hertz**0.5),
        **kwargs,
    ):
        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            current_noise_density=current_noise_density,
            **kwargs,
        )
