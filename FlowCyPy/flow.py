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

    flow_speed: Optional[float] = 80e-6  # Flow speed in meters/second (default: 80 µm/s)
    flow_area: Optional[float] = 1e-6  # Cross-sectional area in square meters (default: 1 µm²)
    total_time: Optional[float] = 1.0  # Total simulation time in seconds (default: 1 second)
    scatterer_density: Optional[float] = 1e12  # Scatterer density in particles per cubic meter (default: 1e12 particles/m³)

    def __post_init__(self):
        """Initialize units for flow parameters."""
        self.flow_speed = Quantity(self.flow_speed, meter / second)
        self.flow_area = Quantity(self.flow_area, meter ** 2)
        self.total_time = Quantity(self.total_time, second)
        self.scatterer_density = Quantity(self.scatterer_density, particle / meter**3)

        self.n_events = self.calculate_number_of_events()

        self._generate_longitudinal_positions(self.n_events)

        logging.info(f"FlowCytometer initialized with an estimated {self.n_events}.")

    def calculate_number_of_events(self) -> int:
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
        number_of_particles = self.scatterer_density * volume

        return int(number_of_particles.magnitude) * particle

    def _generate_longitudinal_positions(self, n_samples: int) -> None:
        r"""
        Generate particle arrival times over the entire experiment duration based on a Poisson process.

        In flow cytometry, the particle arrival times can be modeled as a Poisson process, where the time
        intervals between successive particle arrivals follow an exponential distribution. The average rate
        of particle arrivals (the particle flux) is given by:

        .. math::
            \text{Particle Flux} = \rho \cdot v \cdot A

        where:
        - :math:`\rho` is the scatterer density (particles per cubic meter),
        - :math:`v` is the flow speed (meters per second),
        - :math:`A` is the cross-sectional area of the flow tube (square meters).

        The number of particles arriving in a given time interval follows a Poisson distribution, and the
        time between successive arrivals follows an exponential distribution. The mean inter-arrival time
        is the inverse of the particle flux:

        .. math::
            \Delta t \sim \text{Exponential}(1/\lambda)

        where:
        - :math:`\Delta t` is the time between successive particle arrivals,
        - :math:`\lambda` is the particle flux (particles per second).

        Steps:
        1. Compute the particle flux, which is the average number of particles passing through the detection
        region per second.
        2. Calculate the expected number of particles over the entire experiment duration.
        3. Generate random inter-arrival times using the exponential distribution.
        4. Compute the cumulative arrival times by summing the inter-arrival times.
        5. Ensure that all arrival times fall within the total experiment duration.

        Returns
        -------
        np.ndarray
            An array of particle arrival times (in seconds) for the entire experiment duration, based on the Poisson process.
        """
        # Step 1: Compute the average particle flux (particles per second)
        particle_flux = (self.scatterer_density * self.flow_speed * self.flow_area)

        # Step 2: Calculate the expected number of particles over the entire experiment
        expected_particles = int((particle_flux * self.total_time).magnitude) * particle

        # Step 3: Generate inter-arrival times (exponentially distributed)
        inter_arrival_times = np.random.exponential(scale=1 / particle_flux.magnitude, size=expected_particles.magnitude)

        # Step 4: Compute cumulative arrival times
        arrival_times = np.cumsum(inter_arrival_times) * second

        # Step 5: Limit the arrival times to the total experiment duration
        arrival_times = arrival_times[arrival_times <= self.total_time]
        self.time_positions = arrival_times
        self.longitudinal_positions = self.time_positions / self.flow_speed

        self.n_events = len(arrival_times) * particle

    def print_properties(self) -> None:
        """
        Print the core properties of the flow and particle interactions in the flow cytometer.
        """
        flow_properties = [
            ["Flow Speed", f"{self.flow_speed:.2f~#P}"],
            ["Flow Area", f"{self.flow_area:.2f~#P}"],
            ["Total Simulation Time", f"{self.total_time:.2f~#P}"],
            ["Scatterer Density", f"{self.scatterer_density:.2e~#P}"],
            ['Number of events', f"{self.n_events:.2e~#P}"]
        ]

        print("\nFlow Properties")
        print(tabulate(flow_properties, headers=["Property", "Value"], tablefmt="grid"))
