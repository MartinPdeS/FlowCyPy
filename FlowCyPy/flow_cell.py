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

    This class now provides an option for hydrodynamic focusing. The parameter
    'focusing_factor' (between 0 and 1) adjusts the probability density function (PDF)
    for particle radial positions. With focusing_factor = 0, particles are uniformly distributed
    over the area, following:
        P(r) = 2r / R^2.
    With focusing_factor = 1, particles are ideally focused at the center (r = 0). Intermediate values
    interpolate between these distributions.

    Parameters
    ----------
    volume_flow : Quantity
        The volumetric flow rate (in m³/s).
    radius : Quantity
        The tube radius (in meters).
    event_scheme : str, optional
        The event timing scheme, by default 'poisson'.
    focusing_factor : float, optional
        A value between 0 (no focusing, uniform distribution) and 1 (ideal focusing at the center).
        Default is 0.
    """
    volume_flow: Quantity
    radius: Quantity
    event_scheme: str = 'poisson'
    focusing_factor: float = 1.0  # 0: uniform; 1: all at center

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
            - R is the tube radius,
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
            velocities: 1D numpy array of corresponding velocities (in m/s).
        """
        r = np.linspace(0, self.radius, num_points)
        velocities = 2 * self.flow_speed * (1 - (r / self.radius)**2)
        return r, velocities.to(units.meter / units.second)

    def sample_velocity(self, n_samples: int = 1) -> Quantity:
        """
        Samples a velocity for a particle in a circular flow cell from the Poiseuille flow distribution,
        with an option to apply hydrodynamic focusing.

        The standard PDF for the radial position in a uniformly distributed circular channel is:
            P(r) = 2r / R^2   for 0 ≤ r ≤ R,
        where R is the tube radius. To incorporate hydrodynamic focusing, we scale the sampled radial position
        by (1 - focusing_factor). With focusing_factor = 0, particles are uniformly distributed (r = R * sqrt(u)).
        With focusing_factor = 1, particles are ideally focused at the center (r = 0).

        The local velocity is computed from the effective radial position using:
            v(r) = 2 * v_avg * (1 - (r / R)^2),
        where v_avg is the average flow speed.

        Parameters
        ----------
        n_samples : int, optional
            The number of velocity samples to generate (default is 1).

        Returns
        -------
        Quantity
            A Quantity representing the sampled velocity (or velocities) in meters per second.
        """
        # Uniform sampling: u ~ U(0,1)
        u = np.random.uniform(0, 1, size=n_samples)
        # Apply hydrodynamic focusing by scaling the sampled radial position.
        # If focusing_factor = 0: r_sample = R * sqrt(u) (uniform distribution)
        # If focusing_factor = 1: r_sample = 0 (perfect focusing)
        r_sample = (1 - self.focusing_factor) * self.radius * np.sqrt(u)
        # Compute local velocity using the Poiseuille profile: v(r) = 2 * v_avg * (1 - (r/R)^2)
        v_sample = 2 * self.flow_speed * (1 - (r_sample / self.radius)**2)
        return v_sample


@dataclass(config=config_dict)
class RectangularFlowCell(BaseFlowCell):
    """
    Models a rectangular flow cell.

    The velocity profile follows a **bi-parabolic** distribution:
        v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

    where:
        - `w` is the channel width (in meters),
        - `h` is the channel height (in meters),
        - `x` and `y` are coordinates inside the cross-section (-w/2 ≤ x ≤ w/2, -h/2 ≤ y ≤ h/2),
        - `v_max ≈ 1.5 * v_avg` is the maximum velocity at the center,
        - `v_avg = volume_flow / (w * h)` is the average flow speed.

    This model assumes **low Reynolds number laminar flow** inside the flow cell.

    Hydrodynamic focusing is enabled using the `focusing_factor` parameter, where:
        - `focusing_factor = 0` results in **uniform** particle distribution across the area.
        - `focusing_factor = 1` forces **perfect focusing** at the center (`x = y = 0`).

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
    focusing_factor : float
        A value between 0 (uniform distribution) and 1 (perfect focusing at the center).
    """
    width: Quantity  # in meters
    height: Quantity  # in meters
    volume_flow: Quantity
    event_scheme: str = 'poisson'
    focusing_factor: float = 1.0  # Default: perfect focusing

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

    def sample_velocity(self, n_samples: int) -> Quantity:
        """
        Samples a velocity for a particle in a **rectangular flow cell**, with optional hydrodynamic focusing.

        **Standard Uniform Sampling:**
        - If `focusing_factor = 0`, particles are **uniformly** distributed over the area.
        - The **(x, y) positions** are drawn from a uniform distribution:
            x ~ U(-w/2, w/2),  y ~ U(-h/2, h/2).

        **Hydrodynamic Focusing:**
        - As `focusing_factor → 1`, particles are increasingly concentrated toward (x, y) = (0, 0).
        - We modify the sampling using an exponential scaling:
            x_sample = w/2 * (1 - focusing_factor) * sign(U) * |U|^focusing_factor
            y_sample = h/2 * (1 - focusing_factor) * sign(V) * |V|^focusing_factor
          where U, V ~ U(-1, 1) (uniform random variables).

        **Velocity Calculation:**
        - The velocity at (x, y) is computed using:
            v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

        Parameters:
        -----------
        n_samples : int, optional
            Number of velocity samples to generate (default: 1).

        Returns:
        --------
        Quantity
            A Quantity representing the sampled velocities in meters per second.
        """
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg  # Max velocity in center

        # Generate uniform random variables U, V in [-1, 1]
        U = np.random.uniform(-1, 1, size=n_samples)
        V = np.random.uniform(-1, 1, size=n_samples)

        # Apply hydrodynamic focusing transformation
        x_sample = (self.width / 2) * (1 - self.focusing_factor) * np.sign(U) * np.abs(U) ** self.focusing_factor
        y_sample = (self.height / 2) * (1 - self.focusing_factor) * np.sign(V) * np.abs(V) ** self.focusing_factor

        # Compute velocity at sampled positions
        v_sample = v_max * (1 - (2 * x_sample / self.width) ** 2) * (1 - (2 * y_sample / self.height) ** 2)

        return v_sample


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

    This model assumes **low Reynolds number laminar flow** inside the flow cell.

    Hydrodynamic focusing is enabled using the `focusing_factor` parameter, where:
        - `focusing_factor = 0` results in **uniform** particle distribution across the area.
        - `focusing_factor = 1` forces **perfect focusing** at the center (`x = y = 0`).

    Attributes:
    -----------
    side : Quantity
        The side length of the square channel (in meters).
    volume_flow : Quantity
        The total volumetric flow rate (in m³/s).
    event_scheme : str
        The event timing scheme, by default 'poisson'.
    focusing_factor : float
        A value between 0 (uniform distribution) and 1 (perfect focusing at the center).
    """
    side: Quantity  # in meters
    volume_flow: Quantity
    event_scheme: str = 'poisson'
    focusing_factor: float = 1.0  # Default: perfect focusing

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

    def sample_velocity(self, n_samples: int) -> Quantity:
        """
        Samples a velocity for a particle in a **rectangular flow cell**, with optional hydrodynamic focusing.

        **Standard Uniform Sampling:**
        - If `focusing_factor = 0`, particles are **uniformly** distributed over the area.
        - The **(x, y) positions** are drawn from a uniform distribution:
            x ~ U(-w/2, w/2),  y ~ U(-h/2, h/2).

        **Hydrodynamic Focusing:**
        - As `focusing_factor → 1`, particles are increasingly concentrated toward (x, y) = (0, 0).
        - We modify the sampling using an exponential scaling:
            x_sample = w/2 * (1 - focusing_factor) * sign(U) * |U|^focusing_factor
            y_sample = h/2 * (1 - focusing_factor) * sign(V) * |V|^focusing_factor
          where U, V ~ U(-1, 1) (uniform random variables).

        **Velocity Calculation:**
        - The velocity at (x, y) is computed using:
            v(x, y) = v_max * (1 - (2x / w)^2) * (1 - (2y / h)^2)

        Parameters:
        -----------
        n_samples : int, optional
            Number of velocity samples to generate (default: 1).

        Returns:
        --------
        Quantity
            A Quantity representing the sampled velocities in meters per second.
        """
        v_avg = self.flow_speed
        v_max = 1.5 * v_avg  # Max velocity in center

        # Generate uniform random variables U, V in [-1, 1]
        U = np.random.uniform(-1, 1, size=n_samples)
        V = np.random.uniform(-1, 1, size=n_samples)

        # Apply hydrodynamic focusing transformation
        x_sample = (self.side / 2) * (1 - self.focusing_factor) * np.sign(U) * np.abs(U) ** self.focusing_factor
        y_sample = (self.side / 2) * (1 - self.focusing_factor) * np.sign(V) * np.abs(V) ** self.focusing_factor

        # Compute velocity at sampled positions
        v_sample = v_max * (1 - (2 * x_sample / self.side) ** 2) * (1 - (2 * y_sample / self.side) ** 2)

        return v_sample


@dataclass(config=config_dict)
class IdealFlowCell(BaseFlowCell):
    """
    Models an **idealized flow cell** where the **flow speed is directly specified** instead of
    computing it from the volumetric flow rate and cross-sectional area.

    This class is useful for cases where the velocity is already known from external constraints,
    such as in **microfluidic setups** where a controlled speed is imposed.

    Attributes:
    -----------
    flow_speed : Quantity
        The specified flow speed (in meters per second).
    flow_area : Quantity
        The cross-sectional area of the flow channel (in square meters).
    event_scheme : str, optional
        The event timing scheme, by default 'poisson'.
    """
    flow_speed: Quantity  # Directly provided velocity (m/s)
    flow_area: Quantity  # Cross-sectional area (m²)
    event_scheme: str = 'poisson'

    def __post_init__(self):
        """
        Initializes the IdealFlowCell. Since the flow speed is given explicitly,
        there is **no need to compute it** from volume flow.
        """
        self.volume_flow = self.flow_area * self.flow_speed
        return super().__post_init__()

    def get_velocity_profile(self, num_points: int = 100) -> np.ndarray:
        """
        Returns a **uniform velocity profile** across the flow cell.

        In an **ideal flow cell**, we assume a **constant velocity field** where:

            v(x) = v(y) = v(z) = flow_speed  (∀ x, y, z in the cross-section)

        Unlike **parabolic velocity profiles** (Poiseuille flow), the velocity **does not vary**
        across the cross-section, making this an idealized model.

        Parameters:
        -----------
        num_points : int, optional
            The number of sample points for visualization (default: 100).

        Returns:
        --------
        np.ndarray
            A 1D numpy array of uniform velocity values across all sampled points.
        """
        return np.full(num_points, self.flow_speed.to(units.meter / units.second).magnitude)

    def sample_velocity(self, n_samples: int = 1) -> Quantity:
        """
        Samples **particle velocities** in an **idealized uniform flow**.

        Since the velocity profile is assumed to be **uniform**, all sampled velocities
        are identical to the specified `flow_speed`.

        Parameters:
        -----------
        n_samples : int, optional
            The number of velocity samples to generate (default: 1).

        Returns:
        --------
        Quantity
            A Quantity representing the sampled velocities (m/s), all equal to `flow_speed`.
        """
        return np.full(n_samples, self.flow_speed.to(units.meter / units.second).magnitude) * units.meter / units.second
