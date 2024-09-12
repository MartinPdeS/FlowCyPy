from dataclasses import dataclass
from typing import Optional
import numpy as np
from FlowCyPy.units import Quantity, meter, second, particle
from tabulate import tabulate
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


@dataclass
class FlowCell:
    """
    A class to model the flow parameters in a flow cytometer, including flow speed, flow area,
    and particle interactions. This class interacts with ScattererDistribution to simulate
    the flow of particles through the cytometer.

    Attributes
    ----------
    flow_speed : float
        The speed of the flow in meters per second (m/s).
    flow_area : float
        The cross-sectional area of the flow tube in square meters (m²).
    total_time : float
        The total duration of the flow simulation in seconds.
    scatterer_density : float
        The density of the scatterers (particles) in particles per cubic meter (particles/m³).
    """

    flow_speed: Quantity  # Flow speed in meters/second (default: 80 µm/s)
    flow_area: Quantity  # Cross-sectional area in square meters (default: 1 µm²)
    total_time: Quantity  # Total simulation time in seconds (default: 1 second)

    def __post_init__(self):
        """Initialize units for flow parameters."""
        self.flow_speed = Quantity(self.flow_speed, meter / second)
        self.flow_area = Quantity(self.flow_area, meter ** 2)
        self.total_time = Quantity(self.total_time, second)

    def calculate_number_of_events(self, concentration: Quantity) -> int:
        """
        Calculate the total number of particles based on the scatterer density, flow speed, and flow area.

        Returns
        -------
        int
            The total number of particles in the flow.
        """
        # Volume swept by the flow over the total time
        volume = self.flow_area * self.flow_speed * self.total_time

        # Calculate the total number of particles in this volume
        number_of_particles = concentration * volume

        return number_of_particles.to(particle).round()

    def print_properties(self) -> None:
        """
        Print the core properties of the flow and particle interactions in the flow cytometer.
        """
        flow_properties = [
            ["Flow Speed", f"{self.flow_speed:.2f~#P}"],
            ["Flow Area", f"{self.flow_area:.2f~#P}"],
            ["Total Simulation Time", f"{self.total_time:.2f~#P}"],
        ]

        print("\nFlow Properties")
        print(tabulate(flow_properties, headers=["Property", "Value"], tablefmt="grid"))
