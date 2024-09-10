
from dataclasses import dataclass
from FlowCyPy.units import Quantity, meter, watt
from tabulate import tabulate
import numpy as np

@dataclass()
class Source():
    """
    optical_power : float
        The optical power of the laser (in watts).
    wavelength : float
        The wavelength of the laser (in meters).
    """
    optical_power: float
    wavelength: float
    NA: float

    def __post_init__(self) -> None:
        """
        Initialize additional parameters after class instantiation by assigning physical units to parameters.
        """
        self._add_units_to_parameters()

        # Calculate Gaussian beam waist at the focus
        self.waist = self.wavelength / (np.pi * self.NA)

    def _add_units_to_parameters(self) -> None:
        """Adds physical units to the core parameters of the Source."""
        self.optical_power *= watt
        self.wavelength *= meter

    def print_properties(self) -> None:
        """Displays the core properties of the flow cytometer and its detectors using the `tabulate` library."""
        properties = [
            ["Optical Power", f"{self.optical_power:.2f~#P}"],
            ["Wavelength", f"{self.wavelength:.2e~#P}"],
        ]

        print("\nSource Properties")
        print(tabulate(properties, headers=["Property", "Value"], tablefmt="grid"))
