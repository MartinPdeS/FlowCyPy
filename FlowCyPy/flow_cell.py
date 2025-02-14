from typing import List, Optional
import numpy
import warnings

import pandas as pd
from pydantic.dataclasses import dataclass
from pydantic import field_validator
from pint_pandas import PintArray

from FlowCyPy.source import BaseBeam
from FlowCyPy.population import Population
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.units import meter, particle, Quantity
from FlowCyPy import units
from FlowCyPy.helper import validate_units
from FlowCyPy.dataframe_subclass import ScattererDataFrame

config_dict = dict(
    arbitrary_types_allowed=True,
    kw_only=True,
    slots=True,
    extra='forbid'
)



@dataclass(config=config_dict)
class FlowCell:
    """
    Models the flow parameters in a flow cytometer.

    This version initializes with a volumetric flow rate (volume_flow) and a flow area,
    and then computes the flow speed as:

        flow_speed = volume_flow / flow_area

    Parameters
    ----------
    volume_flow : Quantity
        The volumetric flow rate (in m³/s).
    flow_area : Quantity
        The cross-sectional area of the flow tube (in m²).
    event_scheme : str, optional
        The event timing scheme, by default 'poisson'.
    source : BaseBeam, optional
        An optional beam source.
    """
    volume_flow: Quantity
    flow_area: Quantity
    event_scheme: str = 'poisson'
    source: Optional[BaseBeam] = None

    # The flow_speed will be computed in __post_init__, so it's not provided at initialization.
    flow_speed: Quantity = None  # type: ignore

    def __post_init__(self):
        # Compute flow_speed from the provided volume_flow and flow_area:
        self.flow_speed = (self.volume_flow / self.flow_area).to('meter/second')

    @field_validator('flow_area')
    def _validate_flow_area(cls, value):
        """
        Validates that flow_area is provided in units of meter².
        """
        if not value.check(meter ** 2):
            raise ValueError(f"flow_area must be in meter ** 2, but got {value.units}")
        return value

    @validate_units(run_time=units.second)
    def get_volume(self, run_time: Quantity) -> Quantity:
        """
        Computes the volume passing through the flow cell over the given run time.
        """
        return (self.volume_flow * run_time).to_compact()

    @validate_units(run_time=units.second)
    def get_population_sampling(self, run_time: Quantity, scatterer_collection: ScattererCollection) -> list[Quantity]:
        """
        Calculates the number of events (or particle counts) for each population based on the run time.
        """
        return [
            p.particle_count.calculate_number_of_events(
                flow_area=self.flow_area,
                flow_speed=self.flow_speed,
                run_time=run_time
            )
            for p in scatterer_collection.populations
        ]

    def _generate_event_dataframe(self, populations: List[Population], run_time: Quantity) -> pd.DataFrame:
        """
        Generates a DataFrame of event times for each population based on the specified scheme.
        """
        # Generate individual DataFrames for each population
        population_event_frames = [
            self._generate_poisson_events(population=population, run_time=run_time)
            for population in populations
        ]

        # Combine the DataFrames with population names as keys
        event_dataframe = pd.concat(population_event_frames, keys=[pop.name for pop in populations])
        event_dataframe.index.names = ["Population", "Index"]

        if self.event_scheme.lower() in ['uniform-random', 'uniform-sequential']:
            total_events = len(event_dataframe)
            start_time = 0 * run_time.units
            end_time = run_time
            time_interval = (end_time - start_time) / total_events
            evenly_spaced_times = numpy.arange(0, total_events) * time_interval

            if self.event_scheme.lower() == 'uniform-random':
                numpy.random.shuffle(evenly_spaced_times.magnitude)
            event_dataframe['Time'] = PintArray(evenly_spaced_times.to(units.second).magnitude, units.second)

        scatterer_dataframe = ScattererDataFrame(event_dataframe)
        scatterer_dataframe.attrs['run_time'] = run_time
        return scatterer_dataframe

    def _generate_poisson_events(self, run_time: Quantity, population: Population) -> pd.DataFrame:
        """
        Generates particle arrival times using a Poisson process.
        """

        particle_flux = population.particle_count.compute_particle_flux(
            flow_speed=self.flow_speed,
            flow_area=self.flow_area,
            run_time=run_time
        )
        expected_particles = particle_flux * run_time

        inter_arrival_times = numpy.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.to(particle).magnitude)
        ) / (particle_flux.units / particle)
        arrival_times = numpy.cumsum(inter_arrival_times)
        arrival_times = arrival_times[arrival_times <= run_time]

        dataframe = pd.DataFrame()
        dataframe['Time'] = PintArray(arrival_times, dtype=arrival_times.units)

        if len(dataframe) == 0:
            warnings.warn("Population has been initialized with 0 events.")

        return dataframe
