
import numpy as np
from typing import Union
from FlowCyPy.distribution import BaseDistribution, DeltaDistribution
from pydantic.dataclasses import dataclass
from FlowCyPy.units import Quantity, particle, second
from FlowCyPy.flow import FlowCell
import logging
from tabulate import tabulate

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class Population():
    refractive_index: Union[BaseDistribution, Quantity]   # Refractive index or refractive index distributions
    size: Union[BaseDistribution, Quantity]  # Particle size or size distributions
    concentration: Quantity = 1  # Scatterer density in particles per cubic meter (default: 1e12 particles/m³)
    name: str = ''  # Name of the population distribution

    def initialize(self, flow_cell: FlowCell):

        if isinstance(self.size, Quantity):
            self.size = DeltaDistribution(size_value=self.size)

        self.flow_cell = flow_cell

        self.n_events = self.flow_cell.calculate_number_of_events(concentration=self.concentration)

        self._generate_longitudinal_positions()

        logging.info(f"Population [{self.name}] initialized with an estimated {self.n_events}.")

        self.size_list = self.size.generate(self.n_events)

        self.refractive_index_list = self.refractive_index.generate(self.n_events)

    def _generate_longitudinal_positions(self) -> None:
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
        particle_flux = (self.concentration * self.flow_cell.flow_speed * self.flow_cell.flow_area).to(particle / second)

        # Step 2: Calculate the expected number of particles over the entire experiment
        expected_particles = self.n_events

        # Step 3: Generate inter-arrival times (exponentially distributed)
        inter_arrival_times = np.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.magnitude)
        ) / (particle_flux.units / particle)


        # Step 4: Compute cumulative arrival times
        arrival_times = np.cumsum(inter_arrival_times)

        # Step 5: Limit the arrival times to the total experiment duration
        arrival_times = arrival_times[arrival_times <= self.flow_cell.total_time]
        self.time_positions = arrival_times
        self.longitudinal_positions = self.time_positions / self.flow_cell.flow_speed

        self.n_events = len(arrival_times) * particle

        if self.n_events == 0:
            raise ValueError("Population has been initialized with 0 events.")


    def print_properties(self) -> None:
        """
        Print the core properties of the population, including size, refractive index,
        concentration, and the number of generated events.
        """
        # Compute additional properties to display
        mean_size = np.mean(self.size_list).to_compact()  # Mean particle size in compact form
        mean_refractive_index = np.mean(self.refractive_index_list)  # Mean refractive index
        total_particles = self.n_events.to_compact()  # Total number of events (particles)

        population_properties = [
            ["Population Name", self.name],
            ["Mean Size", f"{mean_size:.2e~#P}"],
            ["Mean Refractive Index", f"{mean_refractive_index:.2f}"],
            ["Concentration", f"{self.concentration:.2e~#P}"],
            ["Total Number of Events", f"{total_particles:.2e~#P}"],
        ]

        print("\nPopulation Properties")
        print(tabulate(population_properties, headers=["Property", "Value"], tablefmt="grid"))