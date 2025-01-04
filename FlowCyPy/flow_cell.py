from typing import List
from FlowCyPy.units import meter, second, particle

from PyMieSim.units import Quantity
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
    run_time : Quantity
        The total duration of the flow simulation in seconds.
    """
    flow_speed: Quantity
    flow_area: Quantity
    run_time: Quantity

    source: BaseBeam = None

    def __post_init__(self):
        """Initialize units for flow parameters."""
        self.flow_speed = Quantity(self.flow_speed, meter / second)
        self.flow_area = Quantity(self.flow_area, meter ** 2)
        self.run_time = Quantity(self.run_time, second)

        self.volume = self.flow_area * self.flow_speed * self.run_time

    @field_validator('flow_speed')
    def _validate_flow_speed(cls, value):
        """
        Validates that the flow speed is provided in meter per second.

        Parameters
        ----------
        value : Quantity
            The flow speed to validate.

        Returns
        -------
        Quantity
            The flow speed frequency.

        Raises:
            ValueError: If the flow speed is not in meter per second.
        """
        if not value.check(meter / second):
            raise ValueError(f"flow_speed must be in meter per second, but got {value.units}")
        return value

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

    @field_validator('run_time')
    def _validate_run_time(cls, value):
        """
        Validates that the total time is provided in second.

        Parameters
        ----------
        value : Quantity
            The total time to validate.

        Returns
        -------
        Quantity
            The validated total time.

        Raises:
            ValueError: If the total time is not in second.
        """
        if not value.check(second):
            raise ValueError(f"run_time must be in second, but got {value.units}")
        return value

    def print_properties(self) -> None:
        """
        Print the core properties of the flow and particle interactions in the flow cytometer.
        """
        print("\nFlow Properties")
        print(tabulate(self.get_properties(), headers=["Property", "Value"], tablefmt="grid"))

    def get_properties(self) -> List[List[str]]:
        return [
            ['Flow Speed', f"{self.flow_speed:.2f~#P}"],
            ['Flow Area', f"{self.flow_area:.2f~#P}"],
            ['Total Time', f"{self.run_time:.2f~#P}"]
        ]

    # def initialize(self, scatterer: Population | ScattererCollection) -> None:
    #     if isinstance(scatterer, Population):
    #         return self._initialize_population(scatterer)

    #     elif isinstance(scatterer, ScattererCollection):
    #         return self._initialize_scatterer_collection(scatterer)

    def _initialize_population(self, population: Population) -> None:
        population.dataframe = pandas.DataFrame()

        population.n_events = population.particle_count.calculate_number_of_events(
            flow_area=self.flow_area,
            flow_speed=self.flow_speed,
            run_time=self.run_time
        )

        self._generate_longitudinal_positions(population)

        size = population.size.generate(population.n_events)
        population.dataframe['Size'] = PintArray(size, dtype=size.units)

        ri = population.refractive_index.generate(population.n_events)
        population.dataframe['RefractiveIndex'] = PintArray(ri, dtype=ri.units)

    def initialize(self, scatterer_collection: ScattererCollection, size_units: str = 'micrometer') -> None:
        """
        Initializes particle size, refractive index, and medium refractive index distributions.

        Parameters
        ----------
        scatterer : Scatterer
            An instance of the Scatterer class that describes the scatterer collection being used.

        """
        self.scatterer_collection = scatterer_collection

        for population in self.scatterer_collection.populations:
            self._initialize_population(population)
            population.dataframe.Size = population.dataframe.Size.pint.to(size_units)

        if len(self.scatterer_collection.populations) != 0:
            self.scatterer_collection.dataframe = pandas.concat(
                [population.dataframe for population in self.scatterer_collection.populations],
                axis=0,
                keys=[population.name for population in self.scatterer_collection.populations],
            )
            self.scatterer_collection.dataframe.index.names = ['Population', 'Index']

        else:
            dtypes = {
                'Time': PintType('second'),            # Time column with seconds unit
                'Position': PintType('meter'),         # Position column with meters unit
                'Size': PintType('meter'),             # Size column with micrometers unit
                'RefractiveIndex': PintType('meter')   # Dimensionless unit for refractive index
            }

            multi_index = pandas.MultiIndex.from_tuples([], names=["Population", "Index"])

            # Create an empty DataFrame with specified column types and a multi-index
            self.scatterer_collection.dataframe = pandas.DataFrame(
                {col: pandas.Series(dtype=dtype) for col, dtype in dtypes.items()},
                index=multi_index
            )

        self.scatterer_collection.n_events = len(self.scatterer_collection.dataframe)

    def distribute_time_linearly(self, sequential_population: bool = False) -> None:
        """
        Distributes particle arrival times linearly across the total runtime of the flow cell.

        Optionally randomizes the order of times for all populations to simulate non-sequential particle arrivals.

        Parameters
        ----------
        sequential_population : bool, optional
            If `True`, organize the order of arrival times across all populations (default is `False`).

        """
        # Generate linearly spaced time values across the flow cell runtime
        linear_spacing = numpy.linspace(0, self.run_time, self.scatterer_collection.n_events)

        # Optionally randomize the linear spacing
        if not sequential_population:
            numpy.random.shuffle(linear_spacing)

        # Assign the linearly spaced or randomized times to the scatterer DataFrame
        self.scatterer_collection.dataframe.Time = PintArray(linear_spacing, dtype=self.scatterer_collection.dataframe.Time.pint.units)

    def _generate_longitudinal_positions(self, population: Population) -> None:
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
            run_time=self.run_time
        )

        # Step 2: Calculate the expected number of particles over the entire experiment
        expected_particles = population.n_events

        # Step 3: Generate inter-arrival times (exponentially distributed)
        inter_arrival_times = numpy.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.magnitude)
        ) / (particle_flux.units / particle)

        # Step 4: Compute cumulative arrival times
        arrival_times = numpy.cumsum(inter_arrival_times)

        # Step 5: Limit the arrival times to the total experiment duration
        arrival_times = arrival_times[arrival_times <= self.run_time]

        time = arrival_times[arrival_times <= self.run_time]

        population.dataframe['Time'] = PintArray(time, dtype=time.units)

        position = arrival_times * self.flow_speed

        population.dataframe['Position'] = PintArray(position, dtype=position.units)

        population.n_events = len(arrival_times) * particle

        if population.n_events == 0:
            warnings.warn("Population has been initialized with 0 events.")
