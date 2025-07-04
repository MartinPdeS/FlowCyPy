
from FlowCyPy import units
from FlowCyPy.detector import Detector


class PMT():
    def __new__(cls,
        name: str,
        phi_angle: units.Quantity,
        numerical_aperture: units.Quantity,
        responsivity: units.Quantity = units.Quantity(0.2, units.ampere / units.watt),
        dark_current: units.Quantity = units.Quantity(1e-9, units.ampere),
        **kwargs):

        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )

# Predefined PIN Photodiode Detector
class PIN():
    def __new__(cls,
        name: str,
        phi_angle: units.Quantity,
        numerical_aperture: units.Quantity,
        responsivity=units.Quantity(0.5, units.ampere / units.watt),  # Higher responsivity for PIN
        dark_current=units.Quantity(1e-8, units.ampere),               # Slightly higher dark current
        **kwargs):

        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )


# Predefined Avalanche Photodiode (APD) Detector
class APD():
    def __new__(cls,
        name: str,
        phi_angle: units.Quantity,
        numerical_aperture: units.Quantity,
        responsivity=units.Quantity(0.7, units.ampere / units.watt),  # APDs often have high responsivity
        dark_current=units.Quantity(5e-9, units.ampere),
        **kwargs):

        return Detector(
            name=name,
            phi_angle=phi_angle,
            numerical_aperture=numerical_aperture,
            responsivity=responsivity,
            dark_current=dark_current,
            **kwargs
        )
