from typing import List
from FlowCyPy.units import meter, second, particle

from PyMieSim.units import Quantity
import pandas as pd
from tabulate import tabulate
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from pint_pandas import PintType, PintArray
from FlowCyPy.source import BaseBeam
from FlowCyPy.population import Population
from FlowCyPy.scatterer_collection import ScattererCollection
import pandas
import numpy
import warnings

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)


@dataclass(config=config_dict)
class FlowCell(object):
    """
    Models the flow parameters in a flow cytometer, including flow speed, flow area,
    and particle interactions. This class interacts with ScattererDistribution to simulate
    the flow of particles through the cytometer.

    Parameters
    ----------
    flow_speed : Quantity
        The speed of the flow in meters per second (m/s).
    flow_area : Quantity
        The cross-sectional area of the flow tube in square meters (m²).
    """
    flow_speed: Quantity
    flow_area: Quantity
    scheme: str = 'poisson'

    source: BaseBeam = None

    def __post_init__(self):
        """Initialize units for flow parameters."""
        self.flow_speed = Quantity(self.flow_speed, meter / second)
        self.flow_area = Quantity(self.flow_area, meter ** 2)

    def get_volume(self, run_time: Quantity) -> Quantity:
        return self.flow_area * self.flow_speed * run_time

    @field_validator('flow_area')
    def _validate_flow_area(cls, value):
        """
        Validates that the flow area is provided in hertz.

        Parameters
        ----------
        value : Quantity
            The flow area to validate.

        Returns
        -------
        Quantity
            The validated flow area.

        Raises:
            ValueError: If the flow area is not in hertz.
        """
        if not value.check(meter ** 2):
            raise ValueError(f"flow_area must be in meter ** 2, but got {value.units}")
        return value

    def get_population_sampling(self, run_time: Quantity, scatterer_collection: ScattererCollection) -> list[Quantity]:
        population_sampling = [
            p.particle_count.calculate_number_of_events(
                flow_area=self.flow_area,
                flow_speed=self.flow_speed,
                run_time=run_time
            ) for p in scatterer_collection.populations
        ]

        return population_sampling

    def generate_event_dataframe(self, populations: List[Population], run_time: Quantity) -> pd.DataFrame:
        """
        Generates a DataFrame of event times for each population based on the specified scheme.

        Parameters
        ----------
        populations : List[Population]
            A list of populations for which to generate event times.
        run_time : Quantity
            The total duration of the experiment.

        Returns
        -------
        pd.DataFrame
            A MultiIndex DataFrame with event times for each population.
        """
        # Generate individual DataFrames for each population
        population_event_frames = [
            self._generate_poisson_events(population=population, run_time=run_time)
            for population in populations
        ]

        # Combine the DataFrames with population names as keys
        event_dataframe = pd.concat(population_event_frames, keys=[pop.name for pop in populations])
        event_dataframe.index.names = ["Population", "Index"]

        # Handle the scheme for event timing
        if self.scheme.lower() in ['uniform-random', 'uniform-sequential']:
            total_events = len(event_dataframe)
            start_time = 0 * run_time.units
            end_time = run_time
            time_interval = (end_time - start_time) / total_events
            evenly_spaced_times = numpy.arange(0, total_events) * time_interval

            if self.scheme.lower() == 'uniform-random':
                numpy.random.shuffle(evenly_spaced_times.magnitude)  # Shuffle times for random spacing

            # Assign the computed times to the DataFrame
            event_dataframe['Time'] = PintArray(evenly_spaced_times.to('second'))

        return event_dataframe

    def _generate_poisson_events(self, run_time: Quantity, population: Population) -> pd.DataFrame:
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
        particle_flux = population.particle_count.compute_particle_flux(
            flow_speed=self.flow_speed,
            flow_area=self.flow_area,
            run_time=run_time
        )

        # Step 2: Calculate the expected number of particles over the entire experiment
        expected_particles = particle_flux * run_time

        # Step 3: Generate inter-arrival times (exponentially distributed)
        inter_arrival_times = numpy.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.magnitude)
        ) / (particle_flux.units / particle)

        # Step 4: Compute cumulative arrival times
        arrival_times = numpy.cumsum(inter_arrival_times)

        # Step 5: Limit the arrival times to the total experiment duration
        arrival_times = arrival_times[arrival_times <= run_time]

        dataframe = pd.DataFrame()

        dataframe['Time'] = PintArray(arrival_times, dtype=arrival_times.units)

        if len(dataframe) == 0:
            warnings.warn("Population has been initialized with 0 events.")

        return dataframe
