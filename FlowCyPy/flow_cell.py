from typing import List, Tuple
import numpy as np
import warnings
import pandas as pd
from pydantic.dataclasses import dataclass
from dataclasses import field
from pint_pandas import PintArray

from FlowCyPy.population import BasePopulation
from FlowCyPy.scatterer_collection import ScattererCollection
from FlowCyPy.units import Quantity
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
class BaseFlowCell:
    """
    Base class for modeling the flow parameters in a flow cytometer.

    This class initializes with a volumetric flow rate (volume_flow) and a flow area,
    and computes the average flow speed as:
        flow_speed = volume_flow / flow_area

    Parameters
    ----------
    volume_flow : Quantity
        The volumetric flow rate (in m³/s).
    flow_area : Quantity
        The cross-sectional area of the flow cell (in m²).
    event_scheme : str, optional
        The event timing scheme, by default 'poisson'.
    """
    # Computed in __post_init__
    flow_speed: Quantity = field(init=False)  # type: ignore

    def __post_init__(self):
        # Compute flow_speed from volume_flow and flow_area
        self.flow_speed = (self.volume_flow / self.flow_area)

    @classmethod
    def _validate_flow_area(cls, value):
        if not value.check(units.meter ** 2):
            raise ValueError(f"flow_area must be in meter**2, but got {value.units}")
        return value

    @validate_units(run_time=units.second)
    def get_volume(self, run_time: Quantity) -> Quantity:
        """
        Computes the volume passing through the flow cell over the given run time.
        """
        return (self.volume_flow * run_time).to_compact()

    @validate_units(run_time=units.second)
    def get_population_sampling(self, run_time: Quantity, scatterer_collection: ScattererCollection) -> List[Quantity]:
        """
        Calculates the number of events (particle counts) for each population based on run time.
        """
        return [
            p.particle_count.calculate_number_of_events(
                flow_area=self.flow_area,
                flow_speed=self.flow_speed,
                run_time=run_time
            )
            for p in scatterer_collection.populations
        ]

    @validate_units(run_time=units.second)
    def _generate_poisson_events(self, run_time: Quantity, population: BasePopulation) -> pd.DataFrame:
        """
        Generates particle arrival times using a Poisson process and samples a velocity for each event.
        """
        particle_flux = population.particle_count.compute_particle_flux(
            flow_speed=self.flow_speed,
            flow_area=self.flow_area,
            run_time=run_time
        )
        expected_particles = particle_flux * run_time

        inter_arrival_times = np.random.exponential(
            scale=1 / particle_flux.magnitude,
            size=int(expected_particles.magnitude)
        ) / (particle_flux.units) * units.particle

        arrival_times = np.cumsum(inter_arrival_times)
        arrival_times = arrival_times[arrival_times <= run_time]

        dataframe = pd.DataFrame()
        dataframe['Time'] = PintArray(arrival_times, dtype=arrival_times.units)

        # Sample velocity for each event using the geometry-specific velocity profile.
        velocities = self.sample_velocity(len(arrival_times))

        dataframe['Velocity'] = PintArray(velocities, dtype=velocities[0].units)

        if len(dataframe) == 0:
            warnings.warn("Population has been initialized with 0 events.")

        return dataframe

    @validate_units(run_time=units.second)
    def _generate_event_dataframe(self, populations: List[BasePopulation], run_time: Quantity) -> pd.DataFrame:
        """
        Generates a DataFrame of event times and sampled velocities for each population based on the specified scheme.
        """
        population_event_frames = [
            self._generate_poisson_events(run_time=run_time, population=population)
            for population in populations
        ]

        event_dataframe = pd.concat(population_event_frames, keys=[pop.name for pop in populations])
        event_dataframe.index.names = ["Population", "Index"]

        if self.event_scheme.lower() in ['uniform-random', 'uniform-sequential']:
            total_events = len(event_dataframe)
            start_time = 0 * run_time.units
            end_time = run_time
            time_interval = (end_time - start_time) / total_events
            evenly_spaced_times = np.arange(0, total_events) * time_interval

            if self.event_scheme.lower() == 'uniform-random':
                np.random.shuffle(evenly_spaced_times.magnitude)
            event_dataframe['Time'] = PintArray(evenly_spaced_times.to(units.second).magnitude, units.second)

        scatterer_dataframe = ScattererDataFrame(event_dataframe)
        scatterer_dataframe.attrs['run_time'] = run_time
        return scatterer_dataframe

    def sample_velocity(self) -> Quantity:
        """
        Abstract method to sample a velocity from the flow cell's velocity distribution.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement sample_velocity.")


@dataclass(config=config_dict)
class CircularFlowCell(BaseFlowCell):
    """
    Models a circular flow cell, where the cross-section is assumed to be a circle.
    The velocity profile is derived from Poiseuille flow:
        v(r) = v_max * (1 - (r/R)^2),
    where R is the tube radius and v_max = 2 * v_avg.
    """
    volume_flow: Quantity
    radius: Quantity
    event_scheme: str = 'poisson'

    def __post_init__(self):
        self.flow_area = np.pi * self.radius ** 2
        return super().__post_init__()

    def get_velocity_profile(self, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes the velocity profile for a circular flow cell using Poiseuille flow.

        For a circular tube, the velocity profile is given by:
            v(r) = v_max * (1 - (r / R)^2)
        where:
        - r is the radial distance from the center of the tube,
        - R is the tube radius (computed as R = sqrt(flow_area / π)),
        - v_max is the maximum velocity at the center, which is 2 * v_avg,
        - v_avg is the average flow speed (computed as volume_flow / flow_area).

        Parameters
        ----------
        num_points : int, optional
            The number of discrete points along the radius to compute the velocity (default is 100).

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            r: 1D numpy array of radial positions from 0 to R (in meters).
            velocities: 1D numpy array of corresponding velocities at each radial position (in m/s),
                        following the profile v(r) = 2 * v_avg * (1 - (r / R)^2).
        """
        r = np.linspace(0, self.radius, num_points)
        velocities = 2 * self.flow_speed * (1 - (r / self.radius)**2)
        return r, velocities.to(units.meter / units.second)

    def sample_velocity(self, n_samples: int) -> Quantity:
        """
        Samples a velocity for a particle in a circular flow cell from the Poiseuille flow distribution.

        The probability density function (PDF) for the radial position in a circular channel (assuming uniform
        distribution over the cross-sectional area) is given by:
            P(r) = 2r / R^2   for 0 ≤ r ≤ R,
        where R is the radius of the channel (R = sqrt(flow_area / π)).
        Given a sample of r values, the local velocity is computed as:
            v(r) = v_max * (1 - (r / R)^2),
        where v_max = 2 * v_avg and v_avg is the average flow speed.

        Parameters
        ----------
        n_samples : int, optional
            The number of velocity samples to generate (default is 1).

        Returns
        -------
        Quantity
            A Quantity representing the sampled velocity (or velocities) in meters per second.
        """
        # Sample r from distribution with PDF: 2r/R^2.
        u = np.random.uniform(0, 1, size=n_samples)
        r_sample = self.radius * np.sqrt(u)
        # Compute velocity at r_sample: v(r) = v_max * (1 - (r/R)^2)
        v_sample = 2 * self.flow_speed * (1 - (r_sample / self.radius)**2)
        return v_sample.to(units.meter / units.second)


@dataclass(config=config_dict)
class RectangularFlowCell(BaseFlowCell):
    """
    Models a rectangular flow cell.

    The velocity profile is assumed to follow a **bi-parabolic** distribution,
    where the velocity decreases quadratically along both the width (`w`) and height (`h`):

        v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

    where:
        - `w` is the width of the channel (in meters),
        - `h` is the height of the channel (in meters),
        - `x` and `y` are coordinates inside the cross-section (-w/2 ≤ x ≤ w/2, -h/2 ≤ y ≤ h/2),
        - `v_max` is the maximum velocity at the center of the channel,
        - `v_avg` is the average flow speed, computed as:

          v_avg = volume_flow / (w * h)

        - For rectangular channels in laminar flow, `v_max` is approximately:

          v_max ≈ 1.5 * v_avg

    This model assumes **low Reynolds number laminar flow** inside the flow cell.

    Attributes:
    -----------
    width : Quantity
        The width of the rectangular channel (in meters).
    height : Quantity
        The height of the rectangular channel (in meters).
    volume_flow : Quantity
        The total volumetric flow rate (in m³/s).
    event_scheme : str
        The event timing scheme, by default 'poisson'.
    """
    width: Quantity  # in meters
    height: Quantity  # in meters
    volume_flow: Quantity
    event_scheme: str = 'poisson'

    def __post_init__(self):
        self.flow_area = self.width * self.height
        return super().__post_init__()

    def get_velocity_profile(self, num_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes the **bi-parabolic** velocity profile for a rectangular flow cell.

        The velocity distribution is given by:

            v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

        where `x` and `y` represent positions inside the channel cross-section.

        Parameters:
        -----------
        num_points : int, optional
            The number of points along each axis for velocity calculation (default: 50).

        Returns:
        --------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            - `X`: 2D numpy array representing the x-coordinates in the cross-section.
            - `Y`: 2D numpy array representing the y-coordinates in the cross-section.
            - `velocities`: 2D numpy array containing the velocity values at each (x, y) position.
        """
        x = np.linspace(- self.width / 2, + self.width / 2, num_points)
        y = np.linspace(- self.height / 2, + self.height / 2, num_points)
        X, Y = np.meshgrid(x, y)
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg
        velocities = v_max * (1 - (2 * X / self.width) ** 2) * (1 - (2 * Y / self.height) ** 2)
        return X, Y, velocities.to(units.meter / units.second)

    def sample_velocity(self, n_sammples: int) -> Quantity:
        """
        Samples a velocity for a particle in a **rectangular flow cell** by choosing
        random (x, y) positions inside the channel and computing the local velocity.

        The (x, y) positions are **uniformly distributed** over the rectangular cross-section,
        and the velocity at each sampled position is computed using the bi-parabolic profile:

            v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

        where:
          - `w` is the channel width.
          - `h` is the channel height.
          - `v_max` is approximately 1.5 * v_avg.

        Parameters:
        -----------
        n_samples : int, optional
            The number of velocity samples to generate (default: 1).

        Returns:
        --------
        Quantity
            A Quantity representing the sampled velocities in meters per second.
        """
        # Uniform sampling in a rectangle:
        x_sample = np.random.uniform(
            - self.width.to(units.meter).magnitude / 2,
            + self.width.to(units.meter).magnitude / 2,
            size=n_sammples
        ) * units.meter

        y_sample = np.random.uniform(
            - self.height.to(units.meter).magnitude / 2,
            + self.height.to(units.meter).magnitude / 2,
            size=n_sammples
        ) * units.meter

        v_avg = self.flow_speed
        v_max = 1.5 * v_avg
        v_sample = v_max * (1 - (2 * x_sample / self.width) ** 2) * (1 - (2 * y_sample / self.height) ** 2)
        return v_sample.to(units.meter / units.second)


@dataclass(config=config_dict)
class SquareFlowCell(BaseFlowCell):
    """
    Models a **square flow cell**, which is a special case of a rectangular flow cell where:
        width = height = side

    The velocity profile follows a **bi-parabolic** distribution, similar to a rectangular channel:

        v(x, y) = v_max * (1 - (2x / side)^2) * (1 - (2y / side)^2)

    where:
        - `side` is the side length of the square channel (in meters),
        - `x` and `y` are positions inside the channel cross-section (-side/2 ≤ x ≤ side/2),
        - `v_max` is the maximum velocity at the center of the channel,
        - `v_avg` is the average flow speed, computed as:

          v_avg = volume_flow / (side^2)

        - For square channels in laminar flow, `v_max` is approximately:

          v_max ≈ 1.5 * v_avg

    This model assumes **low Reynolds number laminar flow** inside the square channel.

    Attributes:
    -----------
    side : Quantity
        The side length of the square channel (in meters).
    volume_flow : Quantity
        The total volumetric flow rate (in m³/s).
    event_scheme : str
        The event timing scheme, by default 'poisson'.
    """
    side: Quantity  # in meters
    volume_flow: Quantity
    event_scheme: str = 'poisson'

    def __post_init__(self):
        self.flow_area = self.side * self.side
        return super().__post_init__()

    def get_velocity_profile(self, num_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes the **bi-parabolic** velocity profile for a square flow cell.

        The velocity distribution follows the equation:

            v(x, y) = v_max * (1 - (2x / side)^2) * (1 - (2y / side)^2)

        where `x` and `y` represent positions inside the square cross-section.

        Parameters:
        -----------
        num_points : int, optional
            The number of points along each axis for velocity calculation (default: 50).

        Returns:
        --------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            - `X`: 2D numpy array representing the x-coordinates in the cross-section.
            - `Y`: 2D numpy array representing the y-coordinates in the cross-section.
            - `velocities`: 2D numpy array containing the velocity values at each (x, y) position.
        """
        x = np.linspace(- self.side / 2, self.side / 2, num_points)
        y = np.linspace(-self.side / 2, self.side / 2, num_points)
        X, Y = np.meshgrid(x, y)
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg
        velocities = v_max * (1 - (2 * X / self.side) ** 2) * (1 - (2 * Y / self.side) ** 2)
        return X, Y, velocities.to(units.meter / units.second)

    def sample_velocity(self, n_sammples: int) -> Quantity:
        """
        Samples a velocity for a particle in a **square flow cell** by choosing
        random (x, y) positions inside the square cross-section and computing the local velocity.

        The (x, y) positions are **uniformly distributed** over the square cross-section,
        and the velocity at each sampled position is computed using the bi-parabolic profile:

            v(x, y) = v_max * (1 - (2x / side)^2) * (1 - (2y / side)^2)

        where:
          - `side` is the channel side length.
          - `v_max` is approximately 1.5 * v_avg.

        Parameters:
        -----------
        n_samples : int, optional
            The number of velocity samples to generate (default: 1).

        Returns:
        --------
        Quantity
            A Quantity representing the sampled velocities in meters per second.
        """
        # Uniform sampling in a rectangle:
        x_sample = np.random.uniform(
            - self.side.to(units.meter).magnitude / 2,
            + self.side.to(units.meter).magnitude / 2,
            size=n_sammples
        ) * units.meter

        y_sample = np.random.uniform(
            - self.side.to(units.meter).magnitude / 2,
            + self.side.to(units.meter).magnitude / 2,
            size=n_sammples
        ) * units.meter

        v_avg = self.flow_speed
        v_max = 1.5 * v_avg
        v_sample = v_max * (1 - (2 * x_sample / self.side) ** 2) * (1 - (2 * y_sample / self.side) ** 2)
        return v_sample.to(units.meter / units.second)
