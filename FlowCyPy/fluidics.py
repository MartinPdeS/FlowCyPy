import pandas as pd
from TypedUnit import ureg, Time, ParticleFlux, Concentration, Particle
import numpy as np

from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy import population  # noqa: F401
from FlowCyPy.fluorescence import Dye, SurfaceDensityLabeling  # noqa: F401
from FlowCyPy.simulation_settings import SimulationSettings  # noqa: F401
from FlowCyPy.fraction_selection import FractionSelection  # noqa: F401
from FlowCyPy.binary.flow_cell import FlowCell  # noqa: F401
from FlowCyPy.binary import distributions  # noqa: F401


class Fluidics:
    def __init__(self, scatterer_collection: ScattererCollection, flow_cell: FlowCell):
        """
        Initializes the Fluidics system with a scatterer collection and a flow cell.

        Parameters
        ----------
        scatterer_collection : ScattererCollection, optional
            The collection of particles or scatterers to be processed in the flow cytometer.
        flow_cell : FlowCell, optional
            The flow cell through which the particles will pass.
        """
        self.scatterer_collection = scatterer_collection
        self.flow_cell = flow_cell

    def compute_particle_flux(
        self, run_time: Time, population: population.BasePopulation
    ) -> ParticleFlux:
        """
        Computes the particle flux in the flow system, accounting for flow speed,
        flow area, and either the particle concentration or a predefined number of particles.

        Parameters
        ----------
        flow_speed : Velocity
            The speed of the flow (e.g., in meters per second).
        flow_area : Area
            The cross-sectional area of the flow tube (e.g., in square meters).
        run_time : Time
            The total duration of the flow (e.g., in seconds).

        Returns
        -------
        ParticleFlux
            The particle flux in particles per second (particle/second).
        """
        if isinstance(population.particle_count, Particle):
            return population.particle_count / run_time

        elif isinstance(population.particle_count, Concentration):
            flow_volume_per_second = (
                self.flow_cell.sample.average_flow_speed * self.flow_cell.sample.area
            )
            return population.particle_count * flow_volume_per_second

        raise ValueError("Invalid particle count representation.")

    def get_arrival_times(
        self, run_time: Time, population: population.BasePopulation
    ) -> pd.Series:
        """
        Computes the arrival times of particles for a given population over the specified run time.

        Parameters
        ----------
        run_time : Time
            The total duration of the flow (e.g., in seconds).
        population : BasePopulation
            The population of particles for which to compute arrival times.

        Returns
        -------
        pd.Series
            A pandas Series containing the arrival times of particles.
        """
        particle_flux = self.compute_particle_flux(
            run_time=run_time, population=population
        )

        arrival_times = (
            self.flow_cell._cpp_sample_arrival_times(
                run_time=run_time.to("second").magnitude,
                particle_flux=particle_flux.to("particle / second").magnitude,
            )
            * ureg.second
        )

        if SimulationSettings.evenly_spaced_events:
            arrival_times = (
                np.linspace(0, run_time.to("second").magnitude, len(arrival_times))
                * ureg.second
            )

        return arrival_times
